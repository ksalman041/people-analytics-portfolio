"""
reference_kpis.py - the independent answer sheet for D1 and D2.

Re-implements the D1 cleaning rules and the D2 KPI definitions in pandas, so the
numbers Power BI shows can be checked against something built a different way.
If Power Query + DAX and this script agree, both are probably right.

Inputs
  data/exports/YYYY-MM.csv, data/reference/planted_issues.csv,
  data/reference/termination_reasons.csv, data/external/fx_rates_monthly.csv
Outputs
  data/reference/dq_exceptions_expected.csv  every data-quality rule hit
  data/reference/reference_kpis.csv          Month x Scope x KPI -> Value
Checks (the script fails loudly if any is false)
  - the DQ rules find exactly the planted issues (no misses, no false alarms)
  - each person appears once per month after cleaning
  - the headcount bridge closes for every month and division

Run: python src/reference_kpis.py
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

ENTITY_CURRENCY = {
    "VMG Deutschland GmbH": "EUR", "VMG Czech Republic s.r.o.": "CZK",
    "VMG Luxembourg S.A.": "EUR", "VMG UK Ltd": "GBP",
}
LOCATION_FIX = {"Praha": "Prague"}
LEADERSHIP_GRADES = {6, 7}  # Head of department and above
MIN_GROUP = 5  # confidentiality: never show a figure based on fewer than 5 people


# ---------------------------------------------------------------------------
# Load and clean
# ---------------------------------------------------------------------------

def parse_date(s: pd.Series) -> pd.Series:
    iso = pd.to_datetime(s, format="%Y-%m-%d", errors="coerce")
    german = pd.to_datetime(s, format="%d.%m.%Y", errors="coerce")
    return iso.fillna(german)


def load_exports() -> pd.DataFrame:
    frames = []
    for path in sorted((DATA / "exports").glob("*.csv")):
        if not re.fullmatch(r"\d{4}-\d{2}\.csv", path.name):
            continue
        df = pd.read_csv(path, dtype=str, keep_default_na=False)
        df.insert(0, "File", path.name)
        df.insert(1, "As Of", pd.Period(path.stem, "M").to_timestamp(how="end").normalize())
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def dq_exceptions(raw: pd.DataFrame) -> pd.DataFrame:
    """Apply rules DQ01-DQ08 to the raw rows; one output row per rule hit."""
    hits = []

    def add(mask: pd.Series, rule: str) -> None:
        part = raw.loc[mask, ["File", "Person ID External"]].assign(**{"Rule ID": rule})
        hits.append(part)

    data_cols = [c for c in raw.columns if c not in ("As Of",)]
    add(raw.duplicated(subset=data_cols, keep="first"), "DQ01")
    add((raw["Manager ID"].str.strip() == "") & (raw["Job Title"] != "Chief Executive Officer"), "DQ02")
    ids_per_file = raw.groupby("File")["Person ID External"].apply(set)
    unknown_mgr = raw.apply(lambda r: r["Manager ID"] != "" and r["Manager ID"] not in ids_per_file[r["File"]], axis=1)
    add(unknown_mgr, "DQ03")
    add(parse_date(raw["Event Date"]) > raw["As Of"], "DQ04")
    standard = raw["Location"].str.strip().replace(LOCATION_FIX)
    add(raw["Location"] != standard, "DQ05")
    non_iso_files = raw.loc[pd.to_datetime(raw["Event Date"], format="%Y-%m-%d", errors="coerce").isna(), "File"].unique()
    hits.append(pd.DataFrame({"File": non_iso_files, "Person ID External": "", "Rule ID": "DQ06"}))
    expected_ccy = raw["Legal Entity"].map(ENTITY_CURRENCY)
    add((raw["Currency"] != "") & (raw["Currency"] != expected_ccy), "DQ07")
    fte = pd.to_numeric(raw["FTE"], errors="coerce")
    add(~fte.between(0, 1, inclusive="right"), "DQ08")
    return pd.concat(hits, ignore_index=True).sort_values(["File", "Rule ID", "Person ID External"])


def clean(raw: pd.DataFrame, fx: pd.DataFrame) -> pd.DataFrame:
    data_cols = [c for c in raw.columns if c not in ("As Of",)]
    df = raw.drop_duplicates(subset=data_cols).copy()
    for col in df.select_dtypes("object"):
        df[col] = df[col].str.strip()
    df["Location"] = df["Location"].replace(LOCATION_FIX)
    df["Hire Date"] = parse_date(df["Hire Date"])
    df["Event Date"] = parse_date(df["Event Date"])
    df = df[df["Event Date"] <= df["As Of"]].copy()  # future-dated records are not true yet

    df["FTE"] = pd.to_numeric(df["FTE"], errors="coerce")
    df.loc[~df["FTE"].between(0, 1, inclusive="right"), "FTE"] = np.nan
    df["Annual Salary"] = pd.to_numeric(df["Annual Salary"], errors="coerce")
    df["Grade"] = pd.to_numeric(df["Pay Grade"].str.removeprefix("G"), errors="coerce")
    df["Is Headcount"] = (df["Employee Status"] == "Active") & (df["Employee Class"] != "External")
    df["Tenure Months"] = ((df["As Of"] - df["Hire Date"]).dt.days / 30.4375).round(1)

    df["Month"] = df["As Of"].dt.strftime("%Y-%m")
    df = df.merge(fx, on=["Month", "Currency"], how="left")
    # The ECB publishes a month's average after the month ends: use the latest known rate if missing.
    latest = fx.sort_values("Month").groupby("Currency")["Units per EUR"].last()
    df["Units per EUR"] = df["Units per EUR"].fillna(df["Currency"].map(latest))
    df["Pay Valid"] = (df["Is Headcount"] & df["Annual Salary"].notna() & df["FTE"].notna()
                       & (df["Currency"] == df["Legal Entity"].map(ENTITY_CURRENCY)))
    # Full-time-equivalent salary in EUR: part-timers are scaled up so pay is compared like for like.
    df["Salary FTE EUR"] = np.where(df["Pay Valid"], df["Annual Salary"] / df["FTE"] / df["Units per EUR"], np.nan)
    return df


# ---------------------------------------------------------------------------
# Movements: compare consecutive month-end snapshots
# ---------------------------------------------------------------------------

def movements(snap: pd.DataFrame, reasons: pd.DataFrame) -> pd.DataFrame:
    hc = snap[snap["Is Headcount"]]
    months = sorted(snap["Month"].unique())
    keep = ["Person ID External", "Division", "Department", "Legal Entity", "Gender", "Grade"]
    rows = []
    for prev, cur in zip(months, months[1:]):
        a = hc[hc["Month"] == prev][keep].set_index("Person ID External")
        b = hc[hc["Month"] == cur][keep].set_index("Person ID External")
        terminated = snap[(snap["Month"] == cur) & (snap["Employee Status"] == "Terminated")].set_index("Person ID External")

        for pid in b.index.difference(a.index):
            rows.append({"Month": cur, "Person ID External": pid, "Movement": "Hire", **b.loc[pid].to_dict()})
        for pid in a.index.difference(b.index):
            t = terminated.loc[pid] if pid in terminated.index else None
            rows.append({
                "Month": cur, "Person ID External": pid, "Movement": "Leaver", **a.loc[pid].to_dict(),
                "Event Reason": None if t is None else t["Event Reason"],
                "Regretted": None if t is None else t["Regret Termination"] == "Yes",
                "Tenure Months At Exit": None if t is None else (t["Event Date"] - t["Hire Date"]).days / 30.4375,
            })
        both = a.index.intersection(b.index)
        moved = [pid for pid in both if a.loc[pid, "Department"] != b.loc[pid, "Department"]]
        for pid in moved:
            rows.append({"Month": cur, "Person ID External": pid, "Movement": "Transfer Out", **a.loc[pid].to_dict()})
            rows.append({"Month": cur, "Person ID External": pid, "Movement": "Transfer In", **b.loc[pid].to_dict()})
    mv = pd.DataFrame(rows)
    mv = mv.merge(reasons, on="Event Reason", how="left")
    return mv


# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------

def pay_gap(df: pd.DataFrame, stat: str) -> float:
    m = df.loc[df["Gender"] == "Male", "Salary FTE EUR"]
    f = df.loc[df["Gender"] == "Female", "Salary FTE EUR"]
    if len(m) < MIN_GROUP or len(f) < MIN_GROUP:
        return np.nan
    mm, ff = (m.mean(), f.mean()) if stat == "mean" else (m.median(), f.median())
    return (mm - ff) / mm * 100


def adjusted_gap(df: pd.DataFrame) -> float:
    """Like-for-like gap: the mean gap inside each legal entity x pay grade group, weighted by
    group size. Comparing within an entity matters: the EU Pay Transparency Directive reports
    per employer, and pooling Prague and Frankfurt salaries would measure geography, not gender."""
    gaps, weights = [], []
    for _, g in df.groupby(["Legal Entity", "Grade"]):
        gap = pay_gap(g, "mean")
        if not np.isnan(gap):
            gaps.append(gap)
            weights.append(len(g))
    return float(np.average(gaps, weights=weights)) if gaps else np.nan


def kpis_for(scope: str, snap: pd.DataFrame, mv: pd.DataFrame) -> list[dict]:
    out = []
    months = sorted(snap["Month"].unique())
    hc_by_month = snap[snap["Is Headcount"]].groupby("Month").size().reindex(months, fill_value=0)
    for i, month in enumerate(months):
        s = snap[(snap["Month"] == month) & snap["Is Headcount"]]
        m = mv[mv["Month"] == month]
        window = months[max(0, i - 11): i + 1]
        r12 = mv[mv["Month"].isin(window) & (mv["Movement"] == "Leaver")]
        avg_hc = hc_by_month[window].mean()
        # Leavers exist from month 2 on, so a full 12-month window starts at month 13;
        # rates over fewer than 5 people are suppressed (confidentiality rule).
        has_full_window = i >= 12 and avg_hc >= MIN_GROUP
        lead = s[s["Grade"].isin(LEADERSHIP_GRADES)]
        pay = s[s["Pay Valid"]]
        vals = {
            "Headcount": len(s),
            "FTE": s["FTE"].sum(),
            "Hires": (m["Movement"] == "Hire").sum(),
            "Leavers": (m["Movement"] == "Leaver").sum(),
            "Leavers Voluntary": ((m["Movement"] == "Leaver") & (m["Leaver Category"] == "Voluntary")).sum(),
            "Leavers Regretted": ((m["Movement"] == "Leaver") & (m["Regretted"] == True)).sum(),  # noqa: E712
            "Transfers In": (m["Movement"] == "Transfer In").sum(),
            "Transfers Out": (m["Movement"] == "Transfer Out").sum(),
            "Turnover R12 %": len(r12) / avg_hc * 100 if has_full_window else np.nan,
            "Voluntary Turnover R12 %": (r12["Leaver Category"] == "Voluntary").sum() / avg_hc * 100 if has_full_window else np.nan,
            "Early Leavers R12 %": (r12["Tenure Months At Exit"] < 12).mean() * 100 if has_full_window and len(r12) >= MIN_GROUP else np.nan,
            "Women in Leadership %": (lead["Gender"] == "Female").mean() * 100 if len(lead) >= MIN_GROUP else np.nan,
            "Pay Gap Mean %": pay_gap(pay, "mean"),
            "Pay Gap Median %": pay_gap(pay, "median"),
            "Pay Gap Adjusted %": adjusted_gap(pay),
        }
        out += [{"Month": month, "Scope": scope, "KPI": k, "Value": round(float(v), 2)} for k, v in vals.items()]
    return out


def main() -> None:
    raw = load_exports()
    fx = pd.read_csv(DATA / "external" / "fx_rates_monthly.csv")
    reasons = pd.read_csv(DATA / "reference" / "termination_reasons.csv")

    # 1. Data-quality rules vs the answer key
    found = dq_exceptions(raw)
    found.to_csv(DATA / "reference" / "dq_exceptions_expected.csv", index=False)
    planted = pd.read_csv(DATA / "reference" / "planted_issues.csv", dtype=str, keep_default_na=False)
    key = lambda d: set(map(tuple, d[["File", "Person ID External", "Rule ID"]].values))  # noqa: E731
    missed, false_alarms = key(planted) - key(found), key(found) - key(planted)
    assert not missed and not false_alarms, f"missed={missed} false_alarms={false_alarms}"
    print(f"DQ rules: {len(found)} hits = {len(planted)} planted issues, no misses, no false alarms")

    # 2. Clean snapshot and movements
    snap = clean(raw, fx)
    dupes = snap.duplicated(["Month", "Person ID External"]).sum()
    assert dupes == 0, f"{dupes} people appear twice in a month after cleaning"
    mv = movements(snap, reasons)

    # 3. Bridge check: opening + hires - leavers + transfers in - transfers out = closing
    months = sorted(snap["Month"].unique())
    hc = snap[snap["Is Headcount"]].groupby(["Month", "Division"]).size()
    for prev, cur in zip(months, months[1:]):
        for div in snap["Division"].unique():
            m = mv[(mv["Month"] == cur) & (mv["Division"] == div)].groupby("Movement").size()
            got = hc.get((prev, div), 0) + m.get("Hire", 0) - m.get("Leaver", 0) + m.get("Transfer In", 0) - m.get("Transfer Out", 0)
            assert got == hc.get((cur, div), 0), f"bridge does not close: {cur} {div}"
    print("Headcount bridge closes for every month and division")

    # 4. KPIs: company-wide, per division (the HRBP row-level-security view) and per legal
    #    entity (pay gaps are reported per employer)
    rows = kpis_for("Company", snap, mv)
    for col in ("Division", "Legal Entity"):
        for value in sorted(snap[col].unique()):
            rows += kpis_for(value, snap[snap[col] == value], mv[mv[col] == value])
    kpis = pd.DataFrame(rows)
    kpis.to_csv(DATA / "reference" / "reference_kpis.csv", index=False)

    wide = kpis[kpis["Scope"] == "Company"].pivot(index="Month", columns="KPI", values="Value")
    cols = ["Headcount", "Hires", "Leavers", "Turnover R12 %", "Voluntary Turnover R12 %", "Early Leavers R12 %",
            "Women in Leadership %", "Pay Gap Mean %", "Pay Gap Median %", "Pay Gap Adjusted %"]
    with pd.option_context("display.width", 220, "display.max_columns", 20):
        print("\nCompany KPIs (last 6 months)\n", wide[cols].tail(6))
        last = kpis[kpis["Month"] == months[-1]].pivot(index="Scope", columns="KPI", values="Value")
        print(f"\nBy division and legal entity, {months[-1]}\n", last[cols[:1] + cols[3:]])
        ent = snap[snap["Is Headcount"]].groupby(["Month", "Legal Entity"]).size().unstack()
        print(f"\nHeadcount by legal entity\n", ent.loc[[months[0], months[12], months[-1]]])


if __name__ == "__main__":
    main()

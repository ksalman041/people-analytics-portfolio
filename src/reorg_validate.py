"""
reorg_validate.py - D3: check a reorg mapping before it goes live, then describe the new structure.

Mapping checks (any failure blocks go-live):
  R01 unit not mapped            R02 new unit not in the target structure
  R03 cost center clash           R04 unit head not an active employee
  R05 effective date differs      R06 headcount does not reconcile (before = after)
Design checks on the resulting structure (for HR to decide, not errors):
  S01 span above 12               S02 manager with a single report
  S03 a unit gains a management layer
It also proves the final mapping (v2) is what the HRIS shows after go-live (July 2026 export).

Outputs
  data/reorg/validation_v1.csv, validation_v2.csv   exceptions per mapping version
  data/reorg/reorg_metrics.csv                      structure before vs after
  portfolio/reorg/spans.png                         chart for the memo
  docs/reorg_memo.md                                one-page memo with Mermaid org charts
Run: python src/reorg_validate.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reference_kpis as rk  # noqa: E402
from viz_style import TOKENS as T, apply, message_title  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "data" / "reorg"
PROGRAMME_DATE = "2026-07-01"
WIDE_SPAN = 12


def load(name: str) -> pd.DataFrame:
    return pd.read_csv(DIR / name, dtype=str, keep_default_na=False)


# ---------------------------------------------------------------------------
# Mapping checks
# ---------------------------------------------------------------------------

def check_mapping(mapping: pd.DataFrame, positions: pd.DataFrame, units: pd.DataFrame,
                  target: pd.DataFrame, people: pd.DataFrame) -> list[dict]:
    out = []

    def hit(rule, name, unit, detail, kind="Blocker"):
        out.append({"Type": kind, "Rule ID": rule, "Rule": name, "Old Department": unit, "Detail": detail})

    target_cc = dict(zip(target["Department"], target["Cost Center"]))
    cc_owner = {cc: dept for dept, cc in target_cc.items()}
    active = set(people["Person ID External"])

    for unit in units["Department"]:
        if unit not in set(mapping["Old Department"]):
            n = int((positions["Department"] == unit).sum())
            hit("R01", "Unit not mapped", unit, f"{n} positions would have no unit after go-live")
    for _, r in mapping.iterrows():
        if r["New Department"] not in target_cc:
            hit("R02", "New unit not in target structure", r["Old Department"], f"'{r['New Department']}' (typo)"
                if any(_close(r["New Department"], t) for t in target_cc) else f"'{r['New Department']}'")
        elif r["New Cost Center"] != target_cc[r["New Department"]]:
            owner = cc_owner.get(r["New Cost Center"])
            hit("R03", "Cost center used by two new units", r["Old Department"],
                f"{r['New Cost Center']} already belongs to {owner}" if owner else f"{r['New Cost Center']} is not in the target structure")
        if r["New Unit Head"] not in active:
            hit("R04", "Unit head not an active employee", r["Old Department"], f"Person {r['New Unit Head']} left before June 2026")
        if r["Effective Date"] != PROGRAMME_DATE:
            hit("R05", "Effective date differs from the programme", r["Old Department"],
                f"{r['Effective Date']} instead of {PROGRAMME_DATE}")
    before = len(positions)
    after = int(positions["Department"].isin(mapping["Old Department"]).sum())
    if before != after:
        hit("R06", "Headcount does not reconcile", "(all)", f"{before} before, {after} after")
    return out


def _close(a: str, b: str) -> bool:
    """Same length within one or two characters and mostly the same letters: probably a typo."""
    a, b = a.lower(), b.lower()
    return abs(len(a) - len(b)) <= 2 and sum(x == y for x, y in zip(a, b)) >= min(len(a), len(b)) - 6


# ---------------------------------------------------------------------------
# Apply a mapping and describe the structure
# ---------------------------------------------------------------------------

def apply_mapping(positions: pd.DataFrame, mapping: pd.DataFrame, units: pd.DataFrame) -> pd.DataFrame:
    """New department, cost center and manager for everyone in scope."""
    m = mapping.set_index("Old Department")
    old_heads = dict(zip(units["Department"], units["Head"]))
    after = positions.copy()
    for i, r in positions.iterrows():
        if r["Department"] not in m.index:
            continue
        row = m.loc[r["Department"]]
        after.loc[i, ["Division", "Department", "Cost Center"]] = [row["New Division"], row["New Department"], row["New Cost Center"]]
        pid = r["Person ID External"]
        if pid == row["New Unit Head"]:
            after.loc[i, "Manager ID"] = row["Head Reports To"]
        elif pid == old_heads.get(r["Department"]):  # a former head under a new head reports to them
            after.loc[i, "Manager ID"] = row["New Unit Head"]
    return after


def structure(scope: pd.DataFrame, people: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    manager_of = dict(zip(people["Person ID External"], people["Manager ID"]))
    manager_of.update(dict(zip(scope["Person ID External"], scope["Manager ID"])))

    def depth(pid: str) -> int:
        d, seen = 1, set()
        while manager_of.get(pid) and pid not in seen:
            seen.add(pid)
            pid, d = manager_of[pid], d + 1
        return d

    spans = scope.groupby("Manager ID").size()
    managers = scope[scope["Person ID External"].isin(spans.index)].copy()
    managers["Span"] = managers["Person ID External"].map(spans)
    scope = scope.assign(Layers=scope["Person ID External"].map(depth))
    metrics = {
        "Positions": len(scope),
        "Units": scope["Department"].nunique(),
        "Managers": len(managers),
        "Average span": round(managers["Span"].mean(), 1),
        "Widest span": int(managers["Span"].max()),
        "Spans above 12": int((managers["Span"] > WIDE_SPAN).sum()),
        "Single-report managers": int((managers["Span"] == 1).sum()),
        "Layers (CEO to front line)": int(scope["Layers"].max()),
    }
    by_unit = scope.groupby("Department")["Layers"].max()
    return metrics | {f"Layers: {u}": int(v) for u, v in by_unit.items()}, managers


def design_checks(before_scope, after_scope, people, units, mapping) -> list[dict]:
    out = []
    _, mgr_after = structure(after_scope, people)
    for _, r in mgr_after.iterrows():
        if r["Span"] > WIDE_SPAN:
            out.append({"Type": "Design note", "Rule ID": "S01", "Rule": f"Span above {WIDE_SPAN}", "Old Department": r["Department"],
                        "Detail": f"{r['Job Title']} ({r['Person ID External']}) has {r['Span']} direct reports"})
        if r["Span"] == 1:
            out.append({"Type": "Design note", "Rule ID": "S02", "Rule": "Manager with a single report", "Old Department": r["Department"],
                        "Detail": f"{r['Job Title']} ({r['Person ID External']}) has 1 direct report"})
    m_before, _ = structure(before_scope, people)
    m_after, _ = structure(after_scope, people)
    m = mapping.set_index("Old Department")
    for old_unit in units["Department"]:
        if old_unit not in m.index:
            continue
        new_unit = m.loc[old_unit, "New Department"]
        old_ids = before_scope.loc[before_scope["Department"] == old_unit, "Person ID External"]
        b = _max_layers(before_scope, old_ids, people)
        a = _max_layers(after_scope, old_ids, people)
        if a > b:
            out.append({"Type": "Design note", "Rule ID": "S03", "Rule": "Unit gains a management layer", "Old Department": old_unit,
                        "Detail": f"{old_unit} staff go from {b} to {a} layers below the CEO, now inside {new_unit}",
                        "Before": b, "After": a})
    return out


def _max_layers(scope, ids, people) -> int:
    manager_of = dict(zip(people["Person ID External"], people["Manager ID"]))
    manager_of.update(dict(zip(scope["Person ID External"], scope["Manager ID"])))
    best = 0
    for pid in ids:
        d, seen = 1, set()
        while manager_of.get(pid) and pid not in seen:
            seen.add(pid)
            pid, d = manager_of[pid], d + 1
        best = max(best, d)
    return best


# ---------------------------------------------------------------------------
# Proof: the final mapping is what the HRIS shows after go-live
# ---------------------------------------------------------------------------

def compare_with_hris(after_scope: pd.DataFrame) -> tuple[int, int]:
    raw = rk.load_exports()
    fx = pd.read_csv(rk.DATA / "external" / "fx_rates_monthly.csv")
    snap = rk.clean(raw, fx)
    jul = snap[(snap["Month"] == "2026-07") & (snap["Employee Status"] == "Active")
               & ~snap["Event"].isin(["Transfer"])].set_index("Person ID External")
    stay = after_scope[after_scope["Person ID External"].isin(jul.index)]
    same = sum(jul.loc[p, "Department"] == d for p, d in zip(stay["Person ID External"], stay["Department"]))
    return int(same), len(stay)


# ---------------------------------------------------------------------------
# Memo and chart
# ---------------------------------------------------------------------------

def spans_chart(mgr_before: pd.DataFrame, mgr_after: pd.DataFrame, path: Path) -> str:
    apply()
    b = mgr_before.set_index("Person ID External")["Span"]
    a = mgr_after.set_index("Person ID External")
    ids = a.sort_values("Span")["Span"].index
    titles = a.loc[ids, "Job Title"].str.replace("Team Lead, ", "Team lead · ").str.replace("Head of ", "Head · ")
    wide = int((a["Span"] > WIDE_SPAN).sum())
    wide_before = int((b > WIDE_SPAN).sum())
    title = (f"{wide} managers run teams above {WIDE_SPAN}, before and after the merge" if wide == wide_before
             else f"{wide} managers run teams above {WIDE_SPAN} after the merge (was {wide_before})")
    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    y = np.arange(len(ids))
    for yi, pid in zip(y, ids):
        before, after = b.get(pid, np.nan), a.loc[pid, "Span"]
        if not np.isnan(before) and before != after:
            ax.plot([before, after], [yi, yi], color=T["baseline"], lw=1.5, zorder=1)
        if not np.isnan(before):
            ax.scatter(before, yi, s=42, color=T["context"], zorder=2, edgecolors=T["card"], linewidths=1.5)
        ax.scatter(after, yi, s=48, color=T["bad"] if after > WIDE_SPAN else T["accent"], zorder=3,
                   edgecolors=T["card"], linewidths=1.5)
        ax.text(after + 0.5, yi, f"{after}", va="center", fontsize=8.5, color=T["ink"])
    ax.axvline(WIDE_SPAN, color=T["ink_2"], lw=0.8)
    ax.text(WIDE_SPAN + 0.2, -0.6, f"guideline: {WIDE_SPAN}", fontsize=8, color=T["ink_2"], va="center")
    ax.set_ylim(-1, len(ids) - 0.4)
    ax.set_yticks(y, titles)
    ax.set_xlim(0, max(a["Span"].max(), b.max()) + 3)
    ax.grid(axis="x")
    ax.grid(axis="y", visible=False)
    ax.tick_params(labelsize=8.5)
    message_title(ax, title, "Direct reports per manager · grey = before (30 Jun), blue = after (1 Jul), red = above guideline")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
    return title


def mermaid(scope: pd.DataFrame, title: str, people: pd.DataFrame) -> str:
    lines = ["```mermaid", "flowchart LR", f'  CEO["CEO"]']
    for div, g in scope.groupby("Division"):
        did = "D_" + div.replace(" ", "")
        lines.append(f'  {did}["{div}"]')
        lines.append(f"  CEO --> {did}")
        for (dept, cc), gg in g.groupby(["Department", "Cost Center"]):
            uid = "U_" + "".join(ch for ch in dept if ch.isalnum())
            lines.append(f'  {uid}["{dept}<br/>{cc} · {len(gg)} positions"]')
            lines.append(f"  {did} --> {uid}")
    lines.append("```")
    return f"**{title}**\n\n" + "\n".join(lines)


def write_memo(v1_exc, v2_exc, m_before, m_after, same, total, dropped, before_scope, after_scope, people) -> None:
    blockers_v1 = [e for e in v1_exc if e["Type"] == "Blocker"]
    notes = sorted((e for e in v2_exc if e["Type"] == "Design note"), key=lambda e: e["Rule ID"])
    rows = "\n".join(f"| {e['Rule ID']} | {e['Rule']} | {e['Old Department']} | {e['Detail']} |" for e in blockers_v1)
    note_rows = "\n".join(f"| {e['Rule ID']} | {e['Rule']} | {e['Detail']} |" for e in notes)
    metric_rows = "\n".join(
        f"| {k} | {m_before.get(k, '–')} | {m_after.get(k, '–')} |"
        for k in ["Positions", "Units", "Managers", "Average span", "Widest span", "Spans above 12",
                  "Single-report managers", "Layers (CEO to front line)"])
    s03 = next((e for e in notes if e["Rule ID"] == "S03"), None)
    layer_note = f"for {s03['Old Department']}, {s03['Before']} → {s03['After']}" if s03 else "none"
    memo = f"""# Q3 2026 Technology reorganisation: mapping validation

*Vltava Market Group People Analytics · prepared 24 June 2026 · go-live 1 July 2026 · synthetic data*

## Summary
- **The first HRBP mapping could not go live:** {len(blockers_v1)} blocking issues, including a whole unit missing
  ({dropped} positions would have dropped out of reporting).
- **The corrected mapping (v2) passes every check:** {m_before['Positions']} positions before, {m_after['Positions']} after, every unit mapped, every cost center unique.
- **Three design points for the Head of Technology:** {len([n for n in notes if n['Rule ID'] == 'S01'])} spans above {WIDE_SPAN},
  one manager with a single report, and the merge adds a management layer ({layer_note}).
- **After go-live the HRIS matches the mapping:** {same} of {total} people still employed in July sit in exactly the unit the mapping predicted.

## What changes
- *Market Data* moves from Markets to Technology and becomes **Data & Analytics** (CC-3400).
- *Platform Engineering* and *IT Infrastructure* merge into **Platform & Infrastructure** (CC-3150).
  The Head of IT Infrastructure becomes deputy and reports to the Head of Platform & Infrastructure.
- *Information Security* is unchanged.

## Blocking issues found in the first submission (v1)
| Rule | Check | Unit | Finding |
|---|---|---|---|
{rows}

All six were fixed in v2 with the HRBPs before the 26 June cut-off.

## Structure before and after (v2)
| Measure | Before (30 Jun) | After (1 Jul) |
|---|---|---|
{metric_rows}

![Spans of control before and after](../portfolio/reorg/spans.png)

## Design notes (not errors: for the business to decide)
| Rule | Check | Finding |
|---|---|---|
{note_rows}

**Recommendations**
1. Let the IT Infrastructure team leads report directly to the Head of Platform & Infrastructure, removing the extra layer.
2. In Data & Analytics the head manages a single team lead: merge the two roles or widen the head's remit.
3. Split the widest teams (13–14 direct reports) when the open roles are filled.

## Org charts (unit level)
{mermaid(before_scope, "Before, 30 June 2026", people)}

{mermaid(after_scope, "After, 1 July 2026", people)}

## How this was checked
`src/reorg_validate.py` applies each mapping to the 30 June position list and runs six blocking checks and three design
checks. The first submission must trigger exactly the issues in `data/reorg/expected_exceptions_v1.csv`. The HRBPs fill in
the mapping in `excel/reorg_mapping_template.xlsx`, which flags most of the blocking issues as they type.
"""
    (ROOT / "docs" / "reorg_memo.md").write_text(memo, encoding="utf-8")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    positions, people = load("positions_before.csv"), load("people_all_before.csv")
    units, target = load("units_current.csv"), load("units_target.csv")
    v1, v2 = load("mapping_v1_hrbp.csv"), load("mapping_v2_final.csv")

    v1_exc = check_mapping(v1, positions, units, target, people)
    v2_exc = check_mapping(v2, positions, units, target, people)
    assert not v2_exc, f"final mapping should be clean: {v2_exc}"
    after = apply_mapping(positions, v2, units)
    v2_exc += design_checks(positions, after, people, units, v2)

    expected = load("expected_exceptions_v1.csv")
    got = {(e["Rule ID"], e["Old Department"]) for e in v1_exc}
    want = set(zip(expected["Rule ID"], expected["Old Department"]))
    assert got == want, f"v1 exceptions differ from the answer key: missing {want - got}, extra {got - want}"
    print(f"v1: {len(v1_exc)} blocking issues = answer key; v2: 0 blocking issues, {len(v2_exc)} design notes")

    pd.DataFrame(v1_exc).to_csv(DIR / "validation_v1.csv", index=False)
    pd.DataFrame(v2_exc).to_csv(DIR / "validation_v2.csv", index=False)
    m_before, mgr_before = structure(positions, people)
    m_after, mgr_after = structure(after, people)
    pd.DataFrame({"Before": pd.Series(m_before), "After": pd.Series(m_after)}).to_csv(DIR / "reorg_metrics.csv")
    assert m_before["Positions"] == m_after["Positions"], "headcount must reconcile"

    same, total = compare_with_hris(after)
    print(f"HRIS check: {same} of {total} people in July sit in the unit the mapping predicted")
    spans_chart(mgr_before, mgr_after, ROOT / "portfolio" / "reorg" / "spans.png")
    dropped = int((~positions["Department"].isin(v1["Old Department"])).sum())
    write_memo(v1_exc, v2_exc, m_before, m_after, same, total, dropped, positions, after, people)
    for k in m_before:
        print(f"  {k:32} {m_before.get(k, '–'):>6} -> {m_after.get(k, '–')}")
    for e in v2_exc:
        print("  note:", e["Rule ID"], e["Detail"])


if __name__ == "__main__":
    main()

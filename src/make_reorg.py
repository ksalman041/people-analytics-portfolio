"""
make_reorg.py - D3 data: the Q3 2026 reorganisation of Technology, as HR would prepare it.

Story: in June 2026 the HR Business Partners submit a mapping of old units to new units
(v1). Validation finds problems; a corrected mapping (v2) goes live on 1 July 2026 - and
the July HRIS export (D1) shows exactly that structure.

The reorganisation (it really happens in the D1 data):
  - Market Data moves from Markets to Technology and becomes Data & Analytics (CC-3400)
  - Platform Engineering + IT Infrastructure merge into Platform & Infrastructure (CC-3150)
  - Information Security stays as it is

Outputs (data/reorg/)
  positions_before.csv          everyone in scope on 30 Jun 2026 (no names: data minimisation)
  people_all_before.csv         Person ID -> Manager ID for the whole company (to count layers to the CEO)
  units_current.csv             today's units: department, division, cost center, head
  units_target.csv              the approved target structure
  mapping_v1_hrbp.csv           the HRBP submission (with the errors real submissions have)
  mapping_v2_final.csv          the corrected mapping that went live
  expected_exceptions_v1.csv    answer key: what validation must find in v1

Run: python src/make_reorg.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reference_kpis as rk  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "reorg"
BEFORE, AFTER = "2026-06", "2026-07"
EFFECTIVE = "2026-07-01"

TARGET_UNITS = [  # division, department, cost center
    ("Technology", "Platform & Infrastructure", "CC-3150"),
    ("Technology", "Data & Analytics", "CC-3400"),
    ("Technology", "Information Security", "CC-3300"),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    raw = rk.load_exports()
    fx = pd.read_csv(rk.DATA / "external" / "fx_rates_monthly.csv")
    snap = rk.clean(raw, fx)
    jun = snap[(snap["Month"] == BEFORE) & (snap["Employee Status"] == "Active")].copy()

    in_scope = (jun["Division"] == "Technology") | (jun["Department"] == "Market Data")
    cols = ["Person ID External", "Division", "Department", "Cost Center", "Legal Entity", "Job Title",
            "Pay Grade", "Employee Class", "Manager ID"]
    positions = jun.loc[in_scope, cols].sort_values(["Department", "Person ID External"])
    positions.to_csv(OUT / "positions_before.csv", index=False)
    jun[["Person ID External", "Manager ID", "Job Title"]].to_csv(OUT / "people_all_before.csv", index=False)

    heads = jun[jun["Job Title"].str.startswith("Head of ")].set_index("Job Title")["Person ID External"]
    units = (positions.groupby(["Division", "Department", "Cost Center"]).size().rename("Positions").reset_index())
    units["Head"] = units["Department"].map(lambda d: heads.get(f"Head of {d}", ""))
    units.to_csv(OUT / "units_current.csv", index=False)
    pd.DataFrame(TARGET_UNITS, columns=["Division", "Department", "Cost Center"]).to_csv(OUT / "units_target.csv", index=False)

    tech_head = heads["Head of Technology"]
    pe_head, md_head, is_head = heads["Head of Platform Engineering"], heads["Head of Market Data"], heads["Head of Information Security"]
    final = pd.DataFrame([
        ("Platform Engineering", "CC-3100", "Technology", "Platform & Infrastructure", "CC-3150", pe_head, tech_head, EFFECTIVE),
        ("IT Infrastructure", "CC-3200", "Technology", "Platform & Infrastructure", "CC-3150", pe_head, tech_head, EFFECTIVE),
        ("Market Data", "CC-1300", "Technology", "Data & Analytics", "CC-3400", md_head, tech_head, EFFECTIVE),
        ("Information Security", "CC-3300", "Technology", "Information Security", "CC-3300", is_head, tech_head, EFFECTIVE),
    ], columns=["Old Department", "Old Cost Center", "New Division", "New Department", "New Cost Center",
                "New Unit Head", "Head Reports To", "Effective Date"])
    final.to_csv(OUT / "mapping_v2_final.csv", index=False)

    # v1 - what the HRBPs actually sent first. One problem per row, plus a missing row.
    leaver = snap[(snap["Employee Status"] == "Terminated") & (snap["Division"] == "Technology")
                  & (snap["Month"] < BEFORE)].sort_values("Month")["Person ID External"].iloc[-1]
    v1 = final.copy()
    v1.loc[v1["Old Department"] == "Platform Engineering", "New Unit Head"] = leaver
    v1.loc[v1["Old Department"] == "IT Infrastructure", "New Department"] = "Platform & Infrastucture"
    v1.loc[v1["Old Department"] == "Market Data", ["New Cost Center", "Effective Date"]] = ["CC-3150", "2026-08-01"]
    v1 = v1[v1["Old Department"] != "Information Security"]
    v1.to_csv(OUT / "mapping_v1_hrbp.csv", index=False)

    is_count = int((positions["Department"] == "Information Security").sum())
    expected = pd.DataFrame([
        ("R01", "Unit not mapped", "Information Security", f"{is_count} positions would have no unit after go-live"),
        ("R02", "New unit not in target structure", "IT Infrastructure", "'Platform & Infrastucture' (typo)"),
        ("R03", "Cost center used by two new units", "Market Data", "CC-3150 already belongs to Platform & Infrastructure"),
        ("R04", "Unit head not an active employee", "Platform Engineering", f"Person {leaver} left before June 2026"),
        ("R05", "Effective date differs from the programme", "Market Data", "2026-08-01 instead of 2026-07-01"),
        ("R06", "Headcount does not reconcile", "(all)", f"{len(positions)} before, {len(positions) - is_count} after"),
    ], columns=["Rule ID", "Rule", "Old Department", "Detail"])
    expected.to_csv(OUT / "expected_exceptions_v1.csv", index=False)

    print(f"{len(positions)} positions in scope, {len(units)} current units, {len(TARGET_UNITS)} target units")
    print(f"v1 has {len(v1)} rows (one unit missing), answer key has {len(expected)} exceptions")


if __name__ == "__main__":
    main()

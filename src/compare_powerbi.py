"""
compare_powerbi.py - do the Power BI measures equal the independent pandas reference?

Reads data/reference/powerbi_kpis.csv (written by src/check_powerbi_numbers.ps1 from the open
Power BI file) and data/reference/reference_kpis.csv (written by src/reference_kpis.py).
Run: python src/compare_powerbi.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

REF = Path(__file__).resolve().parents[1] / "data" / "reference"


def main() -> None:
    pbi = pd.read_csv(REF / "powerbi_kpis.csv")
    ref = pd.read_csv(REF / "reference_kpis.csv")
    m = pbi.merge(ref, on=["Month", "Scope", "KPI"], how="left", suffixes=(" Power BI", " reference"))
    a, b = m["Value Power BI"], m["Value reference"]
    both_blank = a.isna() & b.isna()
    m["Match"] = both_blank | (np.isclose(a, b, atol=0.011) & a.notna() & b.notna())
    print(f"{m['Match'].sum()} of {len(m)} values match (tolerance 0.01)")
    bad = m[~m["Match"]]
    if len(bad):
        print(bad.to_string(index=False))
    raise SystemExit(0 if bad.empty else 1)


if __name__ == "__main__":
    main()

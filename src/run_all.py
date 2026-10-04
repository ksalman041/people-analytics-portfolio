"""
run_all.py - rebuild the whole portfolio from scratch, in order, stopping at the first failure.

  python src/run_all.py              everything (needs internet for the Eurostat / ECB step)
  python src/run_all.py --offline    skip the download and use data/external/ as it is
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STEPS = [
    ("make_exports.py", "D1 data: 25 monthly HRIS exports + planted errors"),
    ("fetch_external.py", "real data: Eurostat pay gaps, ECB exchange rates"),
    ("reference_kpis.py", "reference KPIs and checks (DQ answer key, bridge)"),
    ("make_dataset_overview.py", "all datasets in one Excel workbook"),
    ("make_design_assets.py", "page backgrounds, wireframes, layout"),
    ("render_pages.py", "static previews of the four report pages"),
    ("make_powerbi.py", "Power BI project (PBIP)"),
    ("make_reorg.py", "D3 data: reorg scope, mappings, answer key"),
    ("reorg_validate.py", "D3 validation, structure, memo"),
    ("make_reorg_template.py", "D3 Excel mapping template"),
    ("run_ticket.py", "D4 Ticket #4711 SQL investigation"),
    ("make_portfolio_pdf.py", "portfolio PDF"),
]


def main() -> None:
    offline = "--offline" in sys.argv
    for script, what in STEPS:
        if offline and script == "fetch_external.py":
            print(f"-- skip {script} (offline)")
            continue
        start = time.time()
        print(f"-- {script}: {what}", flush=True)
        done = subprocess.run([sys.executable, str(ROOT / "src" / script)], cwd=ROOT, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
        if done.returncode:
            print(done.stdout[-2000:], done.stderr[-3000:])
            raise SystemExit(f"FAILED: {script}")
        print(f"   ok ({time.time() - start:.0f}s)")
    print("All steps passed.")


if __name__ == "__main__":
    main()

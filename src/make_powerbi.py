"""
make_powerbi.py - writes the complete Power BI project (PBIP) for the Board Pack.

  powerbi/Board_Pack.pbip                 open this in Power BI Desktop
  powerbi/Board_Pack.SemanticModel/       tables, relationships, measures, RLS role (TMDL)
  powerbi/Board_Pack.Report/              4 pages, one JSON file per visual (PBIR)

Everything is generated, so the report can be rebuilt after any change:
  python src/make_powerbi.py
Then check it:
  powershell -ExecutionPolicy Bypass -File src/check_tmdl.ps1
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pbi_model
import pbi_report

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "powerbi"
NAME = "Board_Pack"


def main() -> None:
    model = OUT / f"{NAME}.SemanticModel"
    if model.exists():
        shutil.rmtree(model)
    pbi_model.write_model(model)
    visuals = pbi_report.write_report(OUT / f"{NAME}.Report", model.name)
    (OUT / f"{NAME}.pbip").write_text(json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
        "version": "1.0",
        "artifacts": [{"report": {"path": f"{NAME}.Report"}}],
        "settings": {"enableAutoRecovery": True}}, indent=2) + "\n", encoding="utf-8")
    (OUT / ".gitignore").write_text("**/.pbi/localSettings.json\n**/.pbi/cache.abf\n", encoding="utf-8")
    print(f"Wrote {NAME}.pbip: {len(pbi_model.TABLES)} tables, {len(pbi_model.MEASURES)} measures, {visuals} visuals")


if __name__ == "__main__":
    main()

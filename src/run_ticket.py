"""
run_ticket.py - D4: run the Ticket #4711 investigation (sql/ticket_4711.sql) with DuckDB.

Prints every step, saves the reconciliation, and fails if any difference is unexplained
or the reconciliation does not close.
Output: data/ticket/ticket_4711_reconciliation.csv
Run:    python src/run_ticket.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]


def blocks(sql: str) -> list[tuple[str, str]]:
    parts = re.split(r"^-- name: (.+)$", sql, flags=re.MULTILINE)
    return [(parts[i].strip(), parts[i + 1]) for i in range(1, len(parts), 2)]


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    con = duckdb.connect()
    con.execute(f"SET file_search_path = '{ROOT.as_posix()}'")
    result = None
    for name, sql in blocks((ROOT / "sql" / "ticket_4711.sql").read_text(encoding="utf-8")):
        statements = [s for s in sql.split(";") if s.strip() and not all(
            line.strip().startswith("--") or not line.strip() for line in s.splitlines())]
        for stmt in statements:
            rel = con.sql(stmt)
            if rel is not None:
                result = rel.df()
                print(f"\n=== {name}")
                print(result.to_string(index=False))

    recon = result
    dashboard = int(recon.iloc[0]["people"])
    hrbp = int(recon.iloc[-1]["people"])
    explained = int(recon.iloc[1:-1]["people"].sum())
    assert not recon["line"].str.contains("UNEXPLAINED").any(), "some differences are unexplained"
    assert dashboard + explained == hrbp, f"{dashboard} + {explained} != {hrbp}"
    out = ROOT / "data" / "ticket" / "ticket_4711_reconciliation.csv"
    recon.to_csv(out, index=False)
    print(f"\nReconciled: {dashboard} + {explained} = {hrbp}. Saved {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

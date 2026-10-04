"""
fetch_external.py - the two *real* datasets used in the portfolio.

1. Eurostat earn_gr_gpgr2: unadjusted gender pay gap (%) by economic activity.
   We keep NACE K (financial & insurance activities) and B-S_X_O (whole economy
   excl. public administration) for CZ, DE, LU and the EU27, 2014 onwards.
   https://ec.europa.eu/eurostat/databrowser/view/earn_gr_gpgr2/default/table

2. ECB euro foreign exchange reference rates, monthly averages (dataset EXR),
   for CZK and GBP. Used to convert salaries to EUR for pay-gap reporting.
   https://data.ecb.europa.eu/data/datasets/EXR

Outputs
  data/external/eurostat_gender_pay_gap.csv   Geo, Activity, Year, Pay Gap %, Flag
  data/external/fx_rates_monthly.csv          Month, Currency, Units per EUR

Run: python src/fetch_external.py
"""

from __future__ import annotations

import io
import json
import urllib.request
from itertools import product
from pathlib import Path

import pandas as pd

try:  # python.org builds on Windows don't read the OS certificate store by default
    import truststore

    truststore.inject_into_ssl()
except ImportError:
    pass

ROOT =Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "external"

EUROSTAT_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/earn_gr_gpgr2"
    "?geo=CZ&geo=DE&geo=LU&geo=EU27_2020&nace_r2=K&nace_r2=B-S_X_O&sinceTimePeriod=2014&lang=EN"
)
ECB_URL = (
    "https://data-api.ecb.europa.eu/service/data/EXR/M.CZK+GBP.EUR.SP00.A"
    "?startPeriod=2024-09&endPeriod=2026-10&format=csvdata"
)
GEO_LABELS = {"CZ": "Czechia", "DE": "Germany", "LU": "Luxembourg", "EU27_2020": "EU27"}
ACTIVITY_LABELS = {"K": "Financial & insurance", "B-S_X_O": "Whole economy"}


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "people-analytics-portfolio/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def parse_jsonstat(payload: dict) -> pd.DataFrame:
    """Flatten a JSON-stat 2.0 dataset into one row per cell.

    JSON-stat stores values in a flat array/dict indexed in row-major order over the
    dimensions listed in payload["id"], so we rebuild every combination of category
    codes in that same order and look each one up.
    """
    dims = payload["id"]
    codes = []
    for dim in dims:
        index = payload["dimension"][dim]["category"]["index"]
        codes.append(sorted(index, key=index.get))
    values, status = payload["value"], payload.get("status", {})
    rows = []
    for flat, combo in enumerate(product(*codes)):
        key = str(flat)
        value = values.get(key) if isinstance(values, dict) else values[flat]
        if value is None:
            continue
        rows.append({**dict(zip(dims, combo)), "value": value, "flag": status.get(key, "")})
    return pd.DataFrame(rows)


def fetch_eurostat() -> pd.DataFrame:
    df = parse_jsonstat(json.loads(get(EUROSTAT_URL)))
    out = pd.DataFrame({
        "Geo": df["geo"].map(GEO_LABELS),
        "Activity": df["nace_r2"].map(ACTIVITY_LABELS),
        "Year": df["time"].astype(int),
        "Pay Gap %": df["value"].astype(float),
        "Flag": df["flag"],
    }).sort_values(["Geo", "Activity", "Year"])
    out.to_csv(OUT / "eurostat_gender_pay_gap.csv", index=False)
    return out


def fetch_ecb() -> pd.DataFrame:
    raw = pd.read_csv(io.BytesIO(get(ECB_URL)))
    out = pd.DataFrame({
        "Month": pd.to_datetime(raw["TIME_PERIOD"]).dt.strftime("%Y-%m"),
        "Currency": raw["CURRENCY"],
        "Units per EUR": raw["OBS_VALUE"].astype(float).round(4),
    })
    # EUR itself, so every salary row finds a rate with a plain lookup.
    eur = out[["Month"]].drop_duplicates().assign(Currency="EUR", **{"Units per EUR": 1.0})
    out = pd.concat([out, eur]).sort_values(["Month", "Currency"])
    out.to_csv(OUT / "fx_rates_monthly.csv", index=False)
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    gpg = fetch_eurostat()
    latest = gpg[gpg["Year"] == gpg["Year"].max()]
    print(f"Eurostat: {len(gpg)} rows, latest year {gpg['Year'].max()}")
    print(latest.to_string(index=False))
    fx = fetch_ecb()
    print(f"\nECB: {len(fx)} rows, months {fx['Month'].min()} .. {fx['Month'].max()}")
    print(fx.pivot(index="Month", columns="Currency", values="Units per EUR").tail(4))


if __name__ == "__main__":
    main()

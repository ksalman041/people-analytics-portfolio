"""
pbi_model.py - the semantic model of the Board Pack, written as TMDL (Tabular Model Definition Language).

Tables come from the Power Query files in powerbi/power_query/; measures, relationships and the
row-level-security role are defined here. make_powerbi.py writes it all into the PBIP project.
"""

from __future__ import annotations

import re
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PQ = ROOT / "powerbi" / "power_query"
TAB = "\t"

MEASURE_TABLE = "_Measures"  # "Measures" is a reserved table name in Power BI Desktop
ACCENT, CONTEXT, INK, INK_2, GOOD_TEXT, BAD = "#2A78D6", "#898781", "#0B0B0B", "#52514E", "#006300", "#D03B3B"


def tag(name: str) -> str:
    """Stable lineage tag per object name, so rebuilding doesn't churn git diffs."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"vltava-board-pack/{name}"))


def q(name: str) -> str:
    """TMDL object name, quoted when it isn't a plain identifier."""
    return name if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) else "'" + name.replace("'", "''") + "'"


def body(text: str, level: int) -> str:
    """Indent a multi-line expression; blank lines are dropped (TMDL ends an expression on dedent)."""
    lines = [ln.rstrip() for ln in text.strip("\n").splitlines() if ln.strip()]
    return "\n".join(TAB * level + ln for ln in lines)


def m_source(file: str) -> str:
    return (PQ / file).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Tables: (name, power query file, columns, table options)
# Column: (name, dataType, options) - options: hidden, fmt, sort_by, key
# ---------------------------------------------------------------------------

S, D, I, F, B = "string", "dateTime", "int64", "double", "boolean"

TABLES = [
    ("DimDate", "10_DimDate.m", [
        ("Month End", D, {"key": True, "fmt": "mmm yyyy"}), ("Month", S, {"sort_by": "Month Index"}),
        ("Year", I, {}), ("Quarter", S, {"sort_by": "Quarter Sort"}), ("Quarter Sort", I, {"hidden": True}),
        ("Month Index", I, {"hidden": True})], {"date_table": True}),
    ("DimDivision", "11_DimDivision.m", [("Division", S, {})], {}),
    ("LegalEntities", "02_LegalEntities.m", [
        ("Legal Entity", S, {}), ("Entity Code", S, {}), ("Country", S, {}), ("Location", S, {}), ("Currency", S, {})], {}),
    ("DimTenureBand", "14_DimTenureBand.m", [("Tenure Band", S, {"sort_by": "Band Order"}), ("Band Order", I, {"hidden": True})], {}),
    ("BridgeSteps", "15_BridgeSteps.m", [("Step", S, {"sort_by": "Step Order"}), ("Step Order", I, {"hidden": True})], {}),
    ("Snapshot", "08_Snapshot.m", [
        ("File", S, {"hidden": True}), ("As Of", D, {"hidden": True, "fmt": "yyyy-mm-dd"}), ("Person ID External", S, {}),
        ("Gender", S, {}), ("Employee Status", S, {}), ("Employee Class", S, {}), ("Hire Date", D, {"fmt": "yyyy-mm-dd"}),
        ("Event", S, {}), ("Event Reason", S, {}), ("Event Date", D, {"fmt": "yyyy-mm-dd"}), ("Regret Termination", S, {}),
        ("Division", S, {"hidden": True}), ("Department", S, {}), ("Cost Center", S, {}), ("Legal Entity", S, {"hidden": True}),
        ("Location", S, {"hidden": True}), ("Job Title", S, {}), ("Pay Grade", S, {}), ("FTE", F, {"fmt": "0.0"}),
        ("Manager ID", S, {}), ("Annual Salary", F, {"fmt": "#,0"}), ("Currency", S, {}), ("Is Headcount", B, {}),
        ("Grade", I, {}), ("Is Leadership", B, {}), ("Tenure Months", F, {"fmt": "0.0"}), ("Tenure Band", S, {"hidden": True}),
        ("Pay Valid", B, {}), ("Salary FTE EUR", F, {"fmt": "€#,0"})], {}),
    ("Movements", "09_Movements.m", [
        ("Movement", S, {}), ("Person ID External", S, {}), ("Month", D, {"hidden": True, "fmt": "yyyy-mm-dd"}),
        ("Division", S, {"hidden": True}), ("Department", S, {}), ("Legal Entity", S, {"hidden": True}), ("Gender", S, {}),
        ("Grade", I, {}), ("Event Reason", S, {}), ("Leaver Category", S, {}), ("Is Voluntary", B, {}), ("Reason Short", S, {}),
        ("Tenure Months At Exit", F, {"fmt": "0.0"}), ("Tenure Band", S, {"hidden": True}), ("Is Early Leaver", B, {}),
        ("Is Regretted", B, {}), ("Bridge Sign", I, {})], {}),
    ("DQ_Rules", "06_DQ_Rules.m", [
        ("Rule ID", S, {}), ("Rule", S, {}), ("Severity", S, {"sort_by": "Severity Order"}), ("Action Taken", S, {}),
        ("Rule Label", S, {}), ("Severity Order", I, {"hidden": True})], {}),
    ("DQ_Exceptions", "07_DQ_Exceptions.m", [
        ("File", S, {}), ("As Of", D, {"hidden": True, "fmt": "yyyy-mm-dd"}), ("Person ID External", S, {}),
        ("Rule ID", S, {}), ("Rule", S, {}), ("Rule Label", S, {}), ("Severity", S, {"sort_by": "Severity Order"}),
        ("Severity Order", I, {"hidden": True}), ("Action Taken", S, {})], {}),
    ("LoadStats", "13_LoadStats.m", [("File", S, {}), ("As Of", D, {"fmt": "yyyy-mm-dd"}), ("Rows", I, {})], {}),
    ("Eurostat_GPG", "12_Eurostat_GPG.m", [
        ("Geo", S, {}), ("Activity", S, {}), ("Year", I, {}), ("Pay Gap %", F, {"fmt": "0.0"}), ("Flag", S, {})], {}),
    ("KeyMessageSlots", "17_KeyMessageSlots.m", [("#", I, {})], {}),
    (MEASURE_TABLE, "16_Measures.m", [("Measure Table", S, {"hidden": True})], {}),
]

# Queries used by other queries but not loaded into the model
EXPRESSIONS = [("fnParseDate", "01_fnParseDate.m", "Function"), ("FX", "03_FX.m", "Table"),
               ("TerminationReasons", "04_TerminationReasons.m", "Table"), ("Exports_Raw", "05_Exports_Raw.m", "Table")]
PROJECT_FOLDER = str(ROOT)

RELATIONSHIPS = [  # (many side, one side)
    ("Snapshot", "As Of", "DimDate", "Month End"), ("Movements", "Month", "DimDate", "Month End"),
    ("DQ_Exceptions", "As Of", "DimDate", "Month End"), ("Snapshot", "Division", "DimDivision", "Division"),
    ("Movements", "Division", "DimDivision", "Division"), ("Snapshot", "Legal Entity", "LegalEntities", "Legal Entity"),
    ("Movements", "Legal Entity", "LegalEntities", "Legal Entity"), ("DQ_Exceptions", "Rule ID", "DQ_Rules", "Rule ID"),
    ("Snapshot", "Tenure Band", "DimTenureBand", "Tenure Band"), ("Movements", "Tenure Band", "DimTenureBand", "Tenure Band"),
]


# ---------------------------------------------------------------------------
# Measures: (name, DAX, format, folder, hidden)
# ---------------------------------------------------------------------------

def window(measure_filter: str) -> str:
    """Movements in the 12 months up to the month in context."""
    return f"""
VAR _m = MAX ( DimDate[Month End] )
RETURN
    CALCULATE (
        COUNTROWS ( Movements ),
        {measure_filter},
        REMOVEFILTERS ( DimDate ),
        DimDate[Month End] > EOMONTH ( _m, -12 ),
        DimDate[Month End] <= _m
    )"""


def py(measure: str) -> str:
    return f"""
CALCULATE (
    [{measure}],
    REMOVEFILTERS ( DimDate ),
    DimDate[Month End] = EOMONTH ( MAX ( DimDate[Month End] ), -12 )
)"""


def delta(cur: str, prev: str, pp: bool) -> str:
    """'▲ +2.7 pp  vs Sep 2025' style text for KPI tiles."""
    d, r = ("( _c - _p ) * 100", 1) if pp else ("_c - _p", 0)
    unit = " pp" if pp else ""
    fmt = "0.0" if pp else "0"
    return f"""
VAR _c = [{cur}]
VAR _p = [{prev}]
VAR _r = ROUND ( {d}, {r} )
VAR _arrow = IF ( _r > 0, "▲ +", IF ( _r < 0, "▼ −", "► ±" ) )
RETURN
    IF (
        ISBLANK ( _c ) || ISBLANK ( _p ),
        BLANK (),
        _arrow & FORMAT ( ABS ( _r ), "{fmt}" ) & "{unit}   vs " & FORMAT ( [PY Month], "mmm yyyy" )
    )"""


def delta_color(cur: str, prev: str, pp: bool, direction: str) -> str:
    """Green / red only when the change matters and has a good/bad direction; grey otherwise."""
    d = "( _c - _p ) * 100" if pp else "_c - _p"
    material = "ABS ( _d ) >= 0.5" if pp else "_d <> 0"
    good = "_d > 0" if direction == "up_good" else "_d < 0"
    if direction == "neutral":
        return f'"{INK_2}"'
    return f"""
VAR _c = [{cur}]
VAR _p = [{prev}]
VAR _d = {d}
RETURN
    SWITCH (
        TRUE (),
        ISBLANK ( _c ) || ISBLANK ( _p ), "{INK_2}",
        NOT ( {material} ), "{INK_2}",
        {good}, "{GOOD_TEXT}",
        "{BAD}"
    )"""


def top_color(value_measure: str, over: str) -> str:
    """Accent for the largest bar in the visual, context grey for the rest."""
    return f"""
VAR _v = [{value_measure}]
VAR _max = MAXX ( ALLSELECTED ( {over} ), [{value_measure}] )
RETURN IF ( NOT ISBLANK ( _v ) && _v = _max, "{ACCENT}", "{CONTEXT}" )"""


HC_AT = """
VAR _m = MAX ( DimDate[Month End] )
RETURN
    CALCULATE (
        COUNTROWS ( Snapshot ),
        Snapshot[Is Headcount] = TRUE (),
        REMOVEFILTERS ( DimDate ),
        DimDate[Month End] = _m
    )"""

PAY_GAP = """
VAR _m = MAX ( DimDate[Month End] )
VAR _pay = CALCULATETABLE ( Snapshot, Snapshot[Pay Valid] = TRUE (), REMOVEFILTERS ( DimDate ), DimDate[Month End] = _m )
VAR _men = FILTER ( _pay, Snapshot[Gender] = "Male" )
VAR _women = FILTER ( _pay, Snapshot[Gender] = "Female" )
VAR _am = {agg}X ( _men, Snapshot[Salary FTE EUR] )
VAR _aw = {agg}X ( _women, Snapshot[Salary FTE EUR] )
RETURN IF ( COUNTROWS ( _men ) >= 5 && COUNTROWS ( _women ) >= 5, DIVIDE ( _am - _aw, _am ) )"""

MEASURES = [
    # --- helpers -------------------------------------------------------------
    ("Latest Month", "MAX ( DimDate[Month End] )", "mmm yyyy", "Helpers", False),
    ("PY Month", "EOMONTH ( MAX ( DimDate[Month End] ), -12 )", "mmm yyyy", "Helpers", True),
    ("Has Full Year", """
VAR _m = MAX ( DimDate[Month End] )
RETURN CALCULATE ( COUNTROWS ( DimDate ), REMOVEFILTERS ( DimDate ), DimDate[Month End] <= _m ) >= 13""", None, "Helpers", True),
    ("Report Subtitle", """"Vltava Market Group  ·  " & FORMAT ( [Latest Month], "mmmm yyyy" ) & "  ·  synthetic data\"""", None, "Helpers", False),

    # --- workforce -----------------------------------------------------------
    ("Headcount", HC_AT, "#,0", "Workforce", False),
    ("Headcount PY", py("Headcount"), "#,0", "Workforce", False),
    ("FTE", """
VAR _m = MAX ( DimDate[Month End] )
RETURN CALCULATE ( SUM ( Snapshot[FTE] ), Snapshot[Is Headcount] = TRUE (), REMOVEFILTERS ( DimDate ), DimDate[Month End] = _m )""",
     "#,0.0", "Workforce", False),
    *[(f"Headcount {loc}", f'CALCULATE ( [Headcount], LegalEntities[Location] = "{loc}" )', "#,0", "Workforce", True)
      for loc in ("Prague", "Frankfurt", "Luxembourg", "London")],
    ("Headcount Other Entities", "[Headcount] - [Headcount Prague]", "#,0", "Workforce", True),
    ("Hires R12", window('Movements[Movement] = "Hire"'), "#,0", "Movement", False),
    ("Hires R12 PY", py("Hires R12"), "#,0", "Movement", True),
    ("Leavers R12", window('Movements[Movement] = "Leaver"'), "#,0", "Movement", False),
    ("Transfers In R12", window('Movements[Movement] = "Transfer In"'), "#,0", "Movement", True),
    ("Transfers Out R12", window('Movements[Movement] = "Transfer Out"'), "#,0", "Movement", True),
    ("Avg Headcount R12", """
VAR _m = MAX ( DimDate[Month End] )
VAR _months = CALCULATETABLE ( VALUES ( DimDate[Month End] ), REMOVEFILTERS ( DimDate ), DimDate[Month End] > EOMONTH ( _m, -12 ), DimDate[Month End] <= _m )
RETURN
    AVERAGEX (
        _months,
        VAR _d = DimDate[Month End]
        RETURN CALCULATE ( COUNTROWS ( Snapshot ), Snapshot[Is Headcount] = TRUE (), REMOVEFILTERS ( DimDate ), DimDate[Month End] = _d ) + 0
    )""", "#,0.0", "Movement", True),
    ("Turnover R12 %", """
VAR _avg = [Avg Headcount R12]
RETURN IF ( [Has Full Year] && _avg >= 5, DIVIDE ( [Leavers R12] + 0, _avg ) )""", "0.0%", "Movement", False),
    ("Voluntary Turnover R12 %", """
VAR _avg = [Avg Headcount R12]
VAR _vol = CALCULATE ( [Leavers R12], Movements[Leaver Category] = "Voluntary" )
RETURN IF ( [Has Full Year] && _avg >= 5, DIVIDE ( _vol + 0, _avg ) )""", "0.0%", "Movement", False),
    ("Turnover R12 % PY", py("Turnover R12 %"), "0.0%", "Movement", True),
    ("Voluntary Turnover R12 % PY", py("Voluntary Turnover R12 %"), "0.0%", "Movement", True),
    ("Turnover R12 % Company", "CALCULATE ( [Turnover R12 %], REMOVEFILTERS ( DimDivision ) )", "0.0%", "Movement", False),
    ("Turnover R12 % Operations", 'CALCULATE ( [Turnover R12 %], DimDivision[Division] = "Operations" )', "0.0%", "Movement", False),
    ("Early Leavers R12 %", """
VAR _l = [Leavers R12]
VAR _e = CALCULATE ( [Leavers R12], Movements[Is Early Leaver] = TRUE () )
RETURN IF ( [Has Full Year] && _l >= 5, DIVIDE ( _e + 0, _l ) )""", "0.0%", "Movement", False),
    ("Bridge Value", """
SWITCH (
    SELECTEDVALUE ( BridgeSteps[Step] ),
    "Opening", [Headcount PY],
    "Hires", [Hires R12] + 0,
    "Voluntary leavers", - ( CALCULATE ( [Leavers R12], Movements[Leaver Category] = "Voluntary" ) + 0 ),
    "Involuntary leavers", - ( CALCULATE ( [Leavers R12], Movements[Leaver Category] = "Involuntary" ) + 0 ),
    "Retirements", - ( CALCULATE ( [Leavers R12], Movements[Leaver Category] = "Retirement" ) + 0 ),
    "Net transfers", [Transfers In R12] + 0 - ( [Transfers Out R12] + 0 )
)""", "+#,0;−#,0;0", "Movement", False),

    # --- diversity and pay ---------------------------------------------------
    ("Women %", """
VAR _hc = [Headcount]
RETURN IF ( _hc >= 5, DIVIDE ( CALCULATE ( [Headcount], Snapshot[Gender] = "Female" ) + 0, _hc ) )""", "0.0%", "Diversity & Pay", False),
    ("Women % PY", py("Women %"), "0.0%", "Diversity & Pay", True),
    ("Women in Leadership %", """
VAR _lead = CALCULATE ( [Headcount], Snapshot[Is Leadership] = TRUE () )
RETURN IF ( _lead >= 5, DIVIDE ( CALCULATE ( [Headcount], Snapshot[Is Leadership] = TRUE (), Snapshot[Gender] = "Female" ) + 0, _lead ) )""",
     "0.0%", "Diversity & Pay", False),
    ("Women in Leadership % PY", py("Women in Leadership %"), "0.0%", "Diversity & Pay", True),
    ("Women", """
VAR _f = CALCULATE ( [Headcount], Snapshot[Gender] = "Female" ) + 0
VAR _m = CALCULATE ( [Headcount], Snapshot[Gender] = "Male" ) + 0
RETURN IF ( _f + _m >= 5, DIVIDE ( _f, _f + _m ) )""", "0%", "Diversity & Pay", False),
    ("Men", """
VAR _f = CALCULATE ( [Headcount], Snapshot[Gender] = "Female" ) + 0
VAR _m = CALCULATE ( [Headcount], Snapshot[Gender] = "Male" ) + 0
RETURN IF ( _f + _m >= 5, DIVIDE ( _m, _f + _m ) )""", "0%", "Diversity & Pay", False),
    ("Pay Gap Mean %", PAY_GAP.format(agg="AVERAGE"), "0.0%", "Diversity & Pay", False),
    ("Pay Gap Median %", PAY_GAP.format(agg="MEDIAN"), "0.0%", "Diversity & Pay", False),
    ("Pay Gap Mean % PY", py("Pay Gap Mean %"), "0.0%", "Diversity & Pay", True),
    ("Pay Gap Like-for-like %", """
VAR _m = MAX ( DimDate[Month End] )
VAR _groups = CALCULATETABLE ( SUMMARIZE ( Snapshot, Snapshot[Legal Entity], Snapshot[Grade] ), Snapshot[Pay Valid] = TRUE (), REMOVEFILTERS ( DimDate ), DimDate[Month End] = _m )
VAR _t =
    ADDCOLUMNS (
        _groups,
        "@gap", CALCULATE ( [Pay Gap Mean %] ),
        "@n", CALCULATE ( COUNTROWS ( Snapshot ), Snapshot[Pay Valid] = TRUE (), REMOVEFILTERS ( DimDate ), DimDate[Month End] = _m )
    )
VAR _valid = FILTER ( _t, NOT ISBLANK ( [@gap] ) )
RETURN DIVIDE ( SUMX ( _valid, [@gap] * [@n] ), SUMX ( _valid, [@n] ) )""", "0.0%", "Diversity & Pay", False),
    ("Pay Gap Like-for-like % PY", py("Pay Gap Like-for-like %"), "0.0%", "Diversity & Pay", True),
    ("Sector Benchmark %", """
VAR _c = SELECTEDVALUE ( LegalEntities[Country] )
VAR _y = CALCULATE ( MAX ( Eurostat_GPG[Year] ), Eurostat_GPG[Geo] = _c, Eurostat_GPG[Activity] = "Financial & insurance" )
RETURN DIVIDE ( CALCULATE ( MAX ( Eurostat_GPG[Pay Gap %] ), Eurostat_GPG[Geo] = _c, Eurostat_GPG[Activity] = "Financial & insurance", Eurostat_GPG[Year] = _y ), 100 )""",
     "0.0%", "Diversity & Pay", False),
    ("Like-for-like Cell", """
VAR _g = SELECTEDVALUE ( Snapshot[Pay Grade] )
VAR _v = [Pay Gap Mean %]
RETURN
    IF (
        ISBLANK ( _g ) || _g = "",
        BLANK (),
        IF ( ISBLANK ( _v ), "—", IF ( _v >= 0.05, "▲ ", "" ) & FORMAT ( _v, "0.0%" ) )
    )""", None, "Diversity & Pay", False),

    # --- data quality --------------------------------------------------------
    ("Rule Exceptions", "COUNTROWS ( DQ_Exceptions ) + 0", "#,0;-#,0;", "Data Quality", False),
    ("Files Loaded", "COUNTROWS ( LoadStats )", "#,0", "Data Quality", False),
    ("Rows Loaded", "SUM ( LoadStats[Rows] )", "#,0", "Data Quality", False),
    ("Rows Excluded", "[Rows Loaded] - CALCULATE ( COUNTROWS ( Snapshot ), REMOVEFILTERS () )", "#,0", "Data Quality", False),
    ("DQ Note Files", """FORMAT ( MIN ( LoadStats[As Of] ), "mmm yyyy" ) & " – " & FORMAT ( MAX ( LoadStats[As Of] ), "mmm yyyy" )""",
     None, "Data Quality", True),
    ("DQ Note Rows", """FORMAT ( DIVIDE ( [Rows Loaded], [Files Loaded] ), "0" ) & " rows per file on average\"""", None, "Data Quality", True),
    ("DQ Note Exceptions", """DISTINCTCOUNT ( DQ_Exceptions[Rule ID] ) & " of " & COUNTROWS ( DQ_Rules ) & " rules fired\"""", None, "Data Quality", True),
    ("DQ Note Excluded", '"duplicates + future-dated records"', None, "Data Quality", True),
]

# KPI tile deltas and their colours
for name, cur, prev, pp, direction in [
    ("Headcount", "Headcount", "Headcount PY", False, "neutral"),
    ("Hires", "Hires R12", "Hires R12 PY", False, "neutral"),
    ("Turnover", "Turnover R12 %", "Turnover R12 % PY", True, "down_good"),
    ("Voluntary Turnover", "Voluntary Turnover R12 %", "Voluntary Turnover R12 % PY", True, "down_good"),
    ("Women in Leadership", "Women in Leadership %", "Women in Leadership % PY", True, "up_good"),
    ("Women", "Women %", "Women % PY", True, "up_good"),
    ("Pay Gap", "Pay Gap Mean %", "Pay Gap Mean % PY", True, "down_good"),
    ("Pay Gap LfL", "Pay Gap Like-for-like %", "Pay Gap Like-for-like % PY", True, "down_good"),
]:
    MEASURES.append((f"Delta {name}", delta(cur, prev, pp), None, "Tiles", True))
    MEASURES.append((f"Color Delta {name}", delta_color(cur, prev, pp, direction), None, "Tiles", True))

# Colours for emphasis bars
MEASURES += [
    ("Color Turnover by Division", top_color("Turnover R12 %", "DimDivision[Division]"), None, "Colours", True),
    ("Color Early Leavers", top_color("Early Leavers R12 %", "DimDivision[Division]"), None, "Colours", True),
    ("Color Leaver Reason", top_color("Leavers R12", "Movements[Reason Short]"), None, "Colours", True),
    ("Color DQ Rule", top_color("Rule Exceptions", "DQ_Rules[Rule Label]"), None, "Colours", True),
    ("Color Tenure Band", f'IF ( SELECTEDVALUE ( DimTenureBand[Tenure Band] ) = "< 1 year", "{ACCENT}", "{CONTEXT}" )', None, "Colours", True),
    ("Color DQ File", f'IF ( [Rule Exceptions] > 0, "{ACCENT}", "{CONTEXT}" )', None, "Colours", True),
    ("Color Women by Grade", f'IF ( SELECTEDVALUE ( Snapshot[Pay Grade] ) IN {{ "G5", "G6", "G7" }}, "{ACCENT}", "{CONTEXT}" )',
     None, "Colours", True),
    ("Color LfL Cell", f'IF ( [Pay Gap Mean %] >= 0.05, "{BAD}", "{INK}" )', None, "Colours", True),
]

# Message titles: every chart title is a measure, so it is always true for the data on screen
SIGNED = '"+0;-0;0"'
MEASURES += [
    ("Title Headcount Trend", f"""
VAR _first = CALCULATE ( MIN ( DimDate[Month End] ), REMOVEFILTERS ( DimDate ) )
VAR _last = CALCULATE ( MAX ( DimDate[Month End] ), REMOVEFILTERS ( DimDate ) )
VAR _h0 = CALCULATE ( [Headcount], REMOVEFILTERS ( DimDate ), DimDate[Month End] = _first )
VAR _h1 = CALCULATE ( [Headcount], REMOVEFILTERS ( DimDate ), DimDate[Month End] = _last )
VAR _p0 = CALCULATE ( [Headcount Prague], REMOVEFILTERS ( DimDate ), DimDate[Month End] = _first ) + 0
VAR _p1 = CALCULATE ( [Headcount Prague], REMOVEFILTERS ( DimDate ), DimDate[Month End] = _last ) + 0
VAR _rest = ( _h1 - _p1 ) - ( _h0 - _p0 )
RETURN
    "Headcount " & FORMAT ( DIVIDE ( _h1, _h0 ) - 1, "+0%;-0%;0%" ) & " since " & FORMAT ( _first, "mmm yyyy" )
        & ": Prague " & FORMAT ( _p1 - _p0, {SIGNED} ) & ", other entities " & FORMAT ( _rest, {SIGNED} )""", None, "Titles", True),
    ("Title Turnover by Division", """
VAR _t = FILTER ( ADDCOLUMNS ( ALLSELECTED ( DimDivision[Division] ), "@v", [Turnover R12 %] ), NOT ISBLANK ( [@v] ) )
VAR _top = TOPN ( 1, _t, [@v], DESC )
VAR _v = MAXX ( _top, [@v] )
VAR _n = ROUND ( DIVIDE ( 1, _v ), 0 )
RETURN
    IF ( ISBLANK ( _v ), "Turnover by division",
        MAXX ( _top, DimDivision[Division] ) & " loses " & IF ( _v > DIVIDE ( 1, _n ), "more than ", "about " )
            & "1 in " & _n & " people a year" )""", None, "Titles", True),
    ("Subtitle Turnover by Division", """
"Turnover, last 12 months to " & FORMAT ( [Latest Month], "mmm yyyy" ) & " · company " & FORMAT ( [Turnover R12 % Company], "0.0%" )""",
     None, "Titles", True),
    ("Title Headcount by Entity", f"""
VAR _t = ADDCOLUMNS ( ALLSELECTED ( LegalEntities[Location] ), "@d", [Headcount] - [Headcount PY] )
VAR _top = TOPN ( 1, _t, [@d], DESC )
VAR _d = MAXX ( _top, [@d] )
VAR _others = SUMX ( _t, [@d] ) - _d
RETURN
    MAXX ( _top, LegalEntities[Location] ) & " " & FORMAT ( _d, {SIGNED} ) & " people vs last year; others "
        & IF ( _others = 0, "flat", FORMAT ( _others, {SIGNED} ) )""", None, "Titles", True),
    ("Title Bridge", """
VAR _open = [Headcount PY]
VAR _close = [Headcount]
VAR _h = [Hires R12] + 0
VAR _l = [Leavers R12] + 0
RETURN
    "Headcount " & FORMAT ( _close - _open, "+0;-0;0" ) & " in 12 months: " & _h & " hires "
        & IF ( _h >= _l, "outpaced ", "trailed " ) & _l & " leavers\"""", None, "Titles", True),
    ("Title Turnover Trend", """
VAR _months = FILTER ( ALL ( DimDate[Month End] ), NOT ISBLANK ( [Turnover R12 % Company] ) )
VAR _above = COUNTROWS ( FILTER ( _months, [Turnover R12 % Operations] > [Turnover R12 % Company] ) )
RETURN IF ( _above = COUNTROWS ( _months ), "Operations turnover above the company all year", "Operations turnover runs above the company" )""",
     None, "Titles", True),
    ("Subtitle Turnover Trend", """
VAR _months = FILTER ( ALL ( DimDate[Month End] ), NOT ISBLANK ( [Turnover R12 % Company] ) )
VAR _gap = AVERAGEX ( _months, [Turnover R12 % Operations] - [Turnover R12 % Company] )
RETURN "Turnover, rolling 12 months, % · gap averages " & FORMAT ( _gap * 100, "0" ) & " pp\"""", None, "Titles", True),
    ("Title Leaver Reasons", """
VAR _t = ADDCOLUMNS ( FILTER ( ALL ( Movements[Reason Short] ), NOT ISBLANK ( Movements[Reason Short] ) ), "@n", [Leavers R12] + 0 )
VAR _top = TOPN ( 1, _t, [@n], DESC )
VAR _name = MAXX ( _top, Movements[Reason Short] )
VAR _share = DIVIDE ( MAXX ( _top, [@n] ), SUMX ( _t, [@n] ) )
VAR _phrase =
    SWITCH ( _name, "Career move", "Career moves", "Personal", "Personal reasons", "Performance", "Performance exits",
        "Redundancy", "Redundancies", "Retirement", "Retirements", "Contract ended", "Contract ends", _name )
RETURN _phrase & " drive " & FORMAT ( _share * 10, "0" ) & " in 10 exits\"""", None, "Titles", True),
    ("Subtitle Leaver Reasons", """"Leavers by reason, last 12 months (n=" & ( [Leavers R12] + 0 ) & ")\"""", None, "Titles", True),
    ("Title Early Leavers", """
VAR _ops = CALCULATE ( [Early Leavers R12 %], DimDivision[Division] = "Operations" )
RETURN FORMAT ( _ops * 10, "0" ) & " in 10 Operations leavers quit in year 1\"""", None, "Titles", True),
    ("Title Tenure", """
VAR _first = CALCULATE ( [Turnover R12 %], DimTenureBand[Tenure Band] = "< 1 year" )
VAR _later = CALCULATE ( [Turnover R12 %], DimTenureBand[Tenure Band] <> "< 1 year" )
RETURN "First-year turnover is " & FORMAT ( DIVIDE ( _first, _later ), "0" ) & "x the rate after year one\"""", None, "Titles", True),
    ("Title Women by Grade", """
VAR _mid = { CALCULATE ( [Women], Snapshot[Pay Grade] = "G2" ), CALCULATE ( [Women], Snapshot[Pay Grade] = "G3" ), CALCULATE ( [Women], Snapshot[Pay Grade] = "G4" ) }
VAR _senior = { CALCULATE ( [Women], Snapshot[Pay Grade] = "G5" ), CALCULATE ( [Women], Snapshot[Pay Grade] = "G6" ), CALCULATE ( [Women], Snapshot[Pay Grade] = "G7" ) }
RETURN
    "Women hold " & FORMAT ( MINX ( _mid, [Value] ), "0%" ) & "–" & FORMAT ( MAXX ( _mid, [Value] ), "0%" )
        & " of G2–G4 roles, but at most " & FORMAT ( MAXX ( _senior, [Value] ), "0%" ) & " from G5 up\"""", None, "Titles", True),
    ("Title Gap vs Benchmark", """
VAR _t = FILTER ( ADDCOLUMNS ( ALLSELECTED ( LegalEntities[Location] ), "@r", DIVIDE ( [Pay Gap Mean %], [Sector Benchmark %] ) ), NOT ISBLANK ( [@r] ) )
VAR _top = TOPN ( 1, _t, [@r], DESC )
VAR _r = MAXX ( _top, [@r] )
RETURN
    MAXX ( _top, LegalEntities[Location] ) & "'s raw gap is "
        & IF ( _r >= 1.8 && _r < 2.3, "double", FORMAT ( _r, "0.0" ) & "x" ) & " its sector benchmark\"""", None, "Titles", True),
    ("Title Like-for-like", """
VAR _m = MAX ( DimDate[Month End] )
VAR _cells = CALCULATETABLE ( SUMMARIZE ( Snapshot, Snapshot[Legal Entity], Snapshot[Grade] ), Snapshot[Pay Valid] = TRUE (), REMOVEFILTERS ( DimDate ), DimDate[Month End] = _m )
VAR _t = ADDCOLUMNS ( _cells, "@gap", CALCULATE ( [Pay Gap Mean %] ) )
VAR _comp = COUNTROWS ( FILTER ( _t, NOT ISBLANK ( [@gap] ) ) )
VAR _over = COUNTROWS ( FILTER ( _t, [@gap] >= 0.05 ) ) + 0
RETURN
    IF ( _over = 0, "All " & _comp & " comparable groups are under the 5% EU trigger",
        _over & " of " & _comp & " comparable groups " & IF ( _over = 1, "exceeds", "exceed" ) & " the 5% EU trigger: review" )""",
     None, "Titles", True),
    ("Title DQ Rules", """
VAR _t = ADDCOLUMNS ( ALL ( DQ_Rules[Rule] ), "@n", [Rule Exceptions] )
RETURN "'" & MAXX ( TOPN ( 1, _t, [@n], DESC ), DQ_Rules[Rule] ) & "' is the most frequent issue\"""", None, "Titles", True),
    ("Title DQ Files", """
DISTINCTCOUNT ( DQ_Exceptions[File] ) & " of " & [Files Loaded] & " monthly files had at least one issue\"""", None, "Titles", True),
    ("Key Message", """
SWITCH ( SELECTEDVALUE ( KeyMessageSlots[#] ), 1, [Key Message 1], 2, [Key Message 2], 3, [Key Message 3] )""",
     None, "Key messages", False),
    ("Key Message 1", """
VAR _d = ( [Turnover R12 %] - [Turnover R12 % PY] ) * 100
RETURN
    IF ( _d > 0, "Turnover is rising: ", "Turnover is falling: " ) & FORMAT ( [Turnover R12 %], "0.0%" ) & " ("
        & FORMAT ( _d, "+0.0;-0.0" ) & " pp). Operations is the hotspot at " & FORMAT ( [Turnover R12 % Operations], "0.0%" )
        & "; " & FORMAT ( CALCULATE ( [Early Leavers R12 %], DimDivision[Division] = "Operations" ) * 10, "0" )
        & " in 10 of its leavers quit in year one.\"""", None, "Key messages", False),
    ("Key Message 2", """
VAR _first = CALCULATE ( MIN ( DimDate[Month End] ), REMOVEFILTERS ( DimDate ) )
VAR _p = [Headcount Prague] - CALCULATE ( [Headcount Prague], REMOVEFILTERS ( DimDate ), DimDate[Month End] = _first )
VAR _all = [Headcount] - CALCULATE ( [Headcount], REMOVEFILTERS ( DimDate ), DimDate[Month End] = _first )
RETURN
    "Growth is Prague-led: " & FORMAT ( _p, "+0;-0;0" ) & " people since " & FORMAT ( _first, "mmm yyyy" )
        & "; the other entities " & FORMAT ( _all - _p, "+0;-0;0" ) & ".\"""", None, "Key messages", False),
    ("Key Message 3", """
"Pay gap is mostly structure: raw " & FORMAT ( [Pay Gap Mean %], "0.0%" ) & ", like-for-like "
    & FORMAT ( [Pay Gap Like-for-like %], "0.0%" ) & ". " & [Title Gap vs Benchmark] & ".\"""",
     None, "Key messages", False),
]


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------

# Definitions shown when hovering a measure in Power BI's field list (same wording as docs/kpi_catalog.md)
DESCRIPTIONS = {
    "Headcount": "Employees on the last day of the month: status Active, not External, effective on or before month-end.",
    "FTE": "Contracted capacity in full-time equivalents at month-end; FTE outside 0-1 is treated as missing.",
    "Hires R12": "Employees who joined in the 12 months up to the selected month (found by comparing month-end snapshots).",
    "Leavers R12": "Employees who left in the 12 months up to the selected month (found by comparing month-end snapshots).",
    "Turnover R12 %": "Leavers in the last 12 months divided by the average of the 12 month-end headcounts. Hidden below 5 people.",
    "Voluntary Turnover R12 %": "Resignations in the last 12 months divided by the average month-end headcount. Hidden below 5 people.",
    "Early Leavers R12 %": "Share of the last 12 months' leavers who left within 12 months of joining. Hidden below 5 leavers.",
    "Women %": "Women as a share of headcount at month-end.",
    "Women in Leadership %": "Women as a share of grades G6-G7 at month-end. Hidden below 5 people.",
    "Pay Gap Mean %": "(Men's mean - women's mean FTE salary in EUR) / men's mean. Needs at least 5 women and 5 men.",
    "Pay Gap Median %": "(Men's median - women's median FTE salary in EUR) / men's median. Needs at least 5 women and 5 men.",
    "Pay Gap Like-for-like %": "Mean gap inside each legal entity x grade group (5+ women and 5+ men), weighted by group size.",
    "Sector Benchmark %": "Eurostat earn_gr_gpgr2: raw gender pay gap, financial & insurance sector, entity's country, latest year.",
    "Rule Exceptions": "Data-quality rule hits (DQ01-DQ08) across all monthly files.",
    "Rows Excluded": "Raw rows not used for reporting: exact duplicates and future-dated records.",
}

# Measures whose number format depends on context (DAX format string expression)
FORMAT_EXPRESSIONS = {
    "Bridge Value": 'IF ( SELECTEDVALUE ( BridgeSteps[Step] ) IN { "Opening" } || NOT HASONEVALUE ( BridgeSteps[Step] ), "#,0", "+#,0;-#,0;0" )',
}


def table_tmdl(name: str, source_file: str, columns: list, options: dict) -> str:
    out = [f"table {q(name)}", f"{TAB}lineageTag: {tag(name)}"]
    if options.get("date_table"):
        out.append(f"{TAB}dataCategory: Time")
    out.append("")
    if name == MEASURE_TABLE:
        for m_name, dax, fmt, folder, hidden in MEASURES:
            expr = dax.strip()
            if m_name in DESCRIPTIONS:  # TMDL descriptions are /// lines just above the object
                out.append(f"{TAB}/// {DESCRIPTIONS[m_name]}")
            if "\n" in expr:
                out.append(f"{TAB}measure {q(m_name)} =")
                out.append(body(expr, 3))
            else:
                out.append(f"{TAB}measure {q(m_name)} = {expr}")
            if fmt and m_name not in FORMAT_EXPRESSIONS:
                out.append(f"{TAB * 2}formatString: {fmt}")
            if hidden:
                out.append(f"{TAB * 2}isHidden")
            out.append(f"{TAB * 2}displayFolder: {folder}")
            out.append(f"{TAB * 2}lineageTag: {tag(name + '/' + m_name)}")
            if m_name in FORMAT_EXPRESSIONS:  # a child object, so it comes after the measure's properties
                out.append(f"{TAB * 2}formatStringDefinition = {FORMAT_EXPRESSIONS[m_name]}")
            out.append("")
    for col, dtype, opt in columns:
        out.append(f"{TAB}column {q(col)}")
        out.append(f"{TAB * 2}dataType: {dtype}")
        if opt.get("key"):
            out.append(f"{TAB * 2}isKey")
        if opt.get("fmt"):
            out.append(f"{TAB * 2}formatString: {opt['fmt']}")
        if opt.get("hidden"):
            out.append(f"{TAB * 2}isHidden")
        out.append(f"{TAB * 2}lineageTag: {tag(name + '/' + col)}")
        out.append(f"{TAB * 2}summarizeBy: none")
        out.append(f"{TAB * 2}sourceColumn: {col}")
        if opt.get("sort_by"):
            out.append(f"{TAB * 2}sortByColumn: {q(opt['sort_by'])}")
        out.append("")
    out.append(f"{TAB}partition {q(name)} = m")
    out.append(f"{TAB * 2}mode: import")
    out.append(f"{TAB * 2}source =")
    out.append(body(m_source(source_file), 4))
    out.append("")
    out.append(f"{TAB}annotation PBI_ResultType = Table")
    return "\n".join(out) + "\n"


def expressions_tmdl() -> str:
    out = [f'expression ProjectFolder = "{PROJECT_FOLDER}" meta [IsParameterQuery = true, Type = "Text", IsParameterQueryRequired = true]',
           f"{TAB}lineageTag: {tag('expr/ProjectFolder')}", "", f"{TAB}annotation PBI_ResultType = Text", ""]
    for name, file, kind in EXPRESSIONS:
        out += [f"expression {q(name)} =", body(m_source(file), 2), f"{TAB}lineageTag: {tag('expr/' + name)}", "",
                f"{TAB}annotation PBI_ResultType = {kind}", ""]
    return "\n".join(out)


def relationships_tmdl() -> str:
    out = []
    for many_t, many_c, one_t, one_c in RELATIONSHIPS:
        out += [f"relationship {tag(f'rel/{many_t}.{many_c}')}", f"{TAB}fromColumn: {q(many_t)}.{q(many_c)}",
                f"{TAB}toColumn: {q(one_t)}.{q(one_c)}", ""]
    return "\n".join(out)


MODEL_TMDL = f"""model Model
{TAB}culture: en-US
{TAB}defaultPowerBIDataSourceVersion: powerBI_V3
{TAB}discourageImplicitMeasures
{TAB}sourceQueryCulture: en-US
{TAB}dataAccessOptions
{TAB}{TAB}legacyRedirects
{TAB}{TAB}returnErrorValuesAsNull

annotation __PBI_TimeIntelligenceEnabled = 0

annotation PBI_ProTooling = ["DevMode"]
"""

DATABASE_TMDL = f"""database
{TAB}compatibilityLevel: 1601
"""

ROLE_TMDL = f"""role 'HRBP - Operations'
{TAB}modelPermission: read

{TAB}tablePermission DimDivision = [Division] = "Operations"

{TAB}annotation PBI_Id = {tag('role/hrbp-operations').replace('-', '')}
"""


def write_model(folder: Path) -> None:
    d = folder / "definition"
    (d / "tables").mkdir(parents=True, exist_ok=True)
    (d / "roles").mkdir(parents=True, exist_ok=True)
    (d / "database.tmdl").write_text(DATABASE_TMDL, encoding="utf-8")
    (d / "model.tmdl").write_text(MODEL_TMDL, encoding="utf-8")
    (d / "expressions.tmdl").write_text(expressions_tmdl(), encoding="utf-8")
    (d / "relationships.tmdl").write_text(relationships_tmdl(), encoding="utf-8")
    (d / "roles" / "HRBP - Operations.tmdl").write_text(ROLE_TMDL, encoding="utf-8")
    for name, file, cols, opts in TABLES:
        (d / "tables" / f"{name}.tmdl").write_text(table_tmdl(name, file, cols, opts), encoding="utf-8")
    (folder / "definition.pbism").write_text(
        '{\n  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",\n'
        '  "version": "4.2",\n  "settings": {}\n}\n', encoding="utf-8")

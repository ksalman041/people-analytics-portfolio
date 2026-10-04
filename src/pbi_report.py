"""
pbi_report.py - the four Board Pack pages, written in Power BI's PBIR format (one JSON file per visual).

Layout comes from make_design_assets.PAGES, colours from viz_style.TOKENS, measures from pbi_model.
Chart titles are bound to "Title ..." measures, so they always describe the data on screen.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from make_design_assets import PAGES
from pbi_model import ACCENT, CONTEXT, INK, INK_2, MEASURE_TABLE

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition"
V_VISUAL, V_PAGE, V_REPORT = "2.9.0", "2.1.0", "3.3.0"
SERIES_2 = "#EB6834"
BASE_THEME = "CY24SU10"
BASE_THEME_FILE = Path(r"C:\Program Files\Microsoft Power BI Desktop\bin\WebView2Resources\minerva\sharedresources\BaseThemes") / f"{BASE_THEME}.json"
INSET = 4


# ---------------------------------------------------------------------------
# JSON building blocks
# ---------------------------------------------------------------------------

def lit(v) -> dict:
    if isinstance(v, bool):
        s = "true" if v else "false"
    elif isinstance(v, int):
        s = f"{v}L"
    elif isinstance(v, float):
        s = f"{v:g}D"
    else:
        s = "'" + str(v).replace("'", "''") + "'"
    return {"expr": {"Literal": {"Value": s}}}


def color(hex_: str) -> dict:
    return {"solid": {"color": lit(hex_)}}


def measure(name: str) -> dict:
    return {"Measure": {"Expression": {"SourceRef": {"Entity": MEASURE_TABLE}}, "Property": name}}


def column(table: str, col: str) -> dict:
    return {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": col}}


def color_by(measure_name: str) -> dict:
    return {"solid": {"color": {"expr": measure(measure_name)}}}


def props(**kw) -> dict:
    return {"properties": {k: (v if isinstance(v, dict) else lit(v)) for k, v in kw.items()}}


def ref(field: dict) -> str:
    kind = "Measure" if "Measure" in field else "Column"
    return f"{field[kind]['Expression']['SourceRef']['Entity']}.{field[kind]['Property']}"


def proj(field: dict, display: str | None = None) -> dict:
    p = {"field": field, "queryRef": ref(field), "nativeQueryRef": field[next(iter(field))]["Property"]}
    if display:
        p["displayName"] = display
    return p


def every_point(**kw) -> dict:
    d = props(**kw)
    d["selector"] = {"data": [{"dataViewWildcard": {"matchingOption": 1}}]}
    return d


def series(field: dict, **kw) -> dict:
    d = props(**kw)
    d["selector"] = {"metadata": ref(field)}
    return d


def slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", text)[:40]


# ---------------------------------------------------------------------------
# Visual factory
# ---------------------------------------------------------------------------

class Page:
    def __init__(self, key: str, name: str, display: str, background: str):
        self.key, self.name, self.display, self.background = key, name, display, background
        self.slots = {s[0]: s[1:5] for s in PAGES[key]["slots"]}
        self.visuals: list[dict] = []

    def add(self, vid: str, vtype: str, box: tuple, *, query: dict | None = None, sort: list | None = None,
            objects: dict | None = None, title: str | dict | None = None, subtitle: str | dict | None = None,
            alt: str | None = None, title_size: float = 13.0, title_align: str = "left", title_color: str = INK,
            padding: tuple | None = None) -> None:
        x, y, w, h = box
        n = len(self.visuals) + 1
        visual: dict = {"visualType": vtype}
        if query:
            visual["query"] = {"queryState": query}
            if sort:
                visual["query"]["sortDefinition"] = {"sort": sort, "isDefaultSort": True}
        if objects:
            visual["objects"] = objects
        vco: dict = {
            "background": [props(show=False)],
            "border": [props(show=False)],
            "dropShadow": [props(show=False)],
        }
        if title is None:
            vco["title"] = [props(show=False)]
        else:
            t = props(show=True, fontSize=title_size, fontColor=color(title_color), alignment=title_align, titleWrap=True)
            t["properties"]["text"] = title if isinstance(title, dict) else lit(title)
            vco["title"] = [t]
        if subtitle is not None:
            s = props(show=True, fontSize=9.0, fontColor=color(INK_2), alignment=title_align)
            s["properties"]["text"] = subtitle if isinstance(subtitle, dict) else lit(subtitle)
            vco["subTitle"] = [s]
        if alt:
            vco["general"] = [props(altText=alt)]
        if padding is not None:  # top, bottom, left, right - small cards need less than the theme's default
            t, b, l, rr = (float(v) for v in padding)
            vco["padding"] = [props(top=t, bottom=b, left=l, right=rr)]
        visual["visualContainerObjects"] = vco
        visual["drillFilterOtherVisuals"] = True
        self.visuals.append({
            "$schema": f"{SCHEMA}/visualContainer/{V_VISUAL}/schema.json",
            "name": f"{self.name}_{vid}",
            "position": {"x": x, "y": y, "z": n * 100, "height": h, "width": w, "tabOrder": n * 100},
            "visual": visual,
        })

    def card_box(self, sid: str, top: int = 0, bottom: int = 0) -> tuple:
        x, y, w, h = self.slots[sid]
        return (x + INSET, y + INSET + top, w - 2 * INSET, h - 2 * INSET - top - bottom)

    # -- reusable visuals ------------------------------------------------------
    def header(self, title: str, footnote: str) -> None:
        self.add("title", "textbox", (24, 18, 520, 36), objects={"general": [{"properties": {"paragraphs": [
            {"textRuns": [{"value": title, "textStyle": {"fontFamily": "Segoe UI Semibold", "fontSize": "20pt", "color": INK}}]}]}}]})
        self.add("subtitle", "card", (18, 52, 380, 26), query={"Values": {"projections": [proj(measure("Report Subtitle"))]}},
                 objects={"labels": [props(fontSize=10.0, color=color(INK_2))], "categoryLabels": [props(show=False)]},
                 padding=(0, 0, 0, 0))
        for i, (table, col, label) in enumerate([("DimDivision", "Division", "Division"), ("LegalEntities", "Location", "Legal entity")]):
            self.add(f"slicer{label.replace(' ', '')}", "slicer", (856 + 104 + i * 152, 18, 144, 62),
                     query={"Values": {"projections": [proj(column(table, col))]}},
                     objects={"data": [props(mode="Dropdown")],
                              "header": [props(show=True, text=label, fontColor=color(INK_2), textSize=9.0)],
                              "items": [props(textSize=10.0, fontColor=color(INK))]},
                     alt=f"Filter the page by {label.lower()}", padding=(0, 0, 2, 2))
        self.add("footnote", "textbox", (24, 700, 1232, 18), objects={"general": [{"properties": {"paragraphs": [
            {"textRuns": [{"value": footnote, "textStyle": {"fontFamily": "Segoe UI", "fontSize": "8pt", "color": INK_2}}]}]}}]})

    def kpi(self, sid: str, label: str, value_measure: str, note_measure: str, note_color: str | None, alt: str) -> None:
        x, y, w, h = self.card_box(sid)
        self.add(f"{sid}_value", "card", (x, y, w, 64), query={"Values": {"projections": [proj(measure(value_measure))]}},
                 objects={"labels": [props(fontSize=22.0, color=color(INK))], "categoryLabels": [props(show=False)]},
                 title=label, title_size=9.0, title_align="center", title_color=INK_2, alt=alt, padding=(6, 0, 4, 4))
        note_label = props(fontSize=9.0)
        note_label["properties"]["color"] = color_by(note_color) if note_color else color(INK_2)
        self.add(f"{sid}_note", "card", (x, y + 62, w, h - 62), query={"Values": {"projections": [proj(measure(note_measure))]}},
                 objects={"labels": [note_label], "categoryLabels": [props(show=False)]}, padding=(0, 2, 2, 2))

    def bars(self, sid: str, vtype: str, category: dict, values: list[tuple], *, title, subtitle, alt: str,
             point_color: str | None = None, series_colors: list[str] | None = None, sort: list | None = None,
             legend: bool = False, value_axis: bool = False, top: int = 0) -> None:
        objects = {
            "categoryAxis": [props(show=True, fontSize=9.0, labelColor=color(INK), showAxisTitle=False,
                                   innerPadding=25, maxMarginFactor=45)],
            "valueAxis": [props(show=value_axis, showAxisTitle=False, gridlineShow=False)],
            "labels": [props(show=True, fontSize=9.0, color=color(INK))],
            "legend": [props(show=legend, position="Top", fontSize=9.0, labelColor=color(INK_2))],
        }
        if point_color:
            objects["dataPoint"] = [every_point(fill=color_by(point_color))]
        elif series_colors:
            objects["dataPoint"] = [series(measure(m), fill=color(c)) for (m, _), c in zip(values, series_colors)]
        self.add(sid, vtype, self.card_box(sid, top=top),
                 query={"Category": {"projections": [proj(category)]},
                        "Y": {"projections": [proj(measure(m), d) for m, d in values]}},
                 sort=sort, objects=objects, title=title, subtitle=subtitle, alt=alt)

    def lines(self, sid: str, values: list[tuple], colors: list[str], *, title, subtitle, alt: str) -> None:
        objects = {
            "categoryAxis": [props(show=True, fontSize=9.0, labelColor=color(INK_2), showAxisTitle=False, gridlineShow=False)],
            "valueAxis": [props(show=True, fontSize=9.0, labelColor=color(INK_2), showAxisTitle=False, gridlineShow=True,
                                gridlineColor=color("#E1E0D9"))],
            "lineStyles": [props(strokeWidth=2, showMarker=False)],
            "legend": [props(show=False)],
            "seriesLabels": [props(show=True, fontSize=9.0)],
            "dataPoint": [series(measure(m), fill=color(c)) for (m, _), c in zip(values, colors)],
        }
        self.add(sid, "lineChart", self.card_box(sid),
                 query={"Category": {"projections": [proj(column("DimDate", "Month End"))]},
                        "Y": {"projections": [proj(measure(m), d) for m, d in values]}},
                 objects=objects, title=title, subtitle=subtitle, alt=alt)

    # -- output ----------------------------------------------------------------
    def page_json(self) -> dict:
        return {
            "$schema": f"{SCHEMA}/page/{V_PAGE}/schema.json",
            "name": self.name,
            "displayName": self.display,
            "displayOption": "FitToPage",
            "height": 720,
            "width": 1280,
            "objects": {
                "background": [props(image={"image": {
                    "name": lit(self.background),
                    "url": {"expr": {"ResourcePackageItem": {"PackageName": "RegisteredResources", "PackageType": 1,
                                                             "ItemName": self.background}}},
                    "scaling": lit("Fit")}}, transparency=0.0)],
                "outspace": [props(color=color("#F9F9F7"), transparency=0.0)],
            },
        }


def T(name: str) -> dict:
    """Bind a title or subtitle to a measure."""
    return {"expr": measure(name)}


# ---------------------------------------------------------------------------
# The four pages
# ---------------------------------------------------------------------------

FOOT = "Source: monthly HRIS exports, Vltava Market Group (synthetic data). "


def board_summary() -> Page:
    p = Page("1_board_summary", "boardSummary", "Board Summary", "bg_1_board_summary.png")
    p.header("Board Summary", FOOT + "Turnover = leavers in last 12 months ÷ average month-end headcount. "
                                     "Groups under 5 people are hidden.")
    for sid, label, value, note, alt in [
        ("K1", "Headcount", "Headcount", "Headcount", "Headcount at month-end"),
        ("K2", "Hires · 12 months", "Hires R12", "Hires", "Hires in the last 12 months"),
        ("K3", "Turnover · 12 months", "Turnover R12 %", "Turnover", "Turnover over the last 12 months"),
        ("K4", "Voluntary turnover", "Voluntary Turnover R12 %", "Voluntary Turnover", "Voluntary turnover"),
        ("K5", "Women in leadership", "Women in Leadership %", "Women in Leadership", "Share of women in grades G6 and G7"),
        ("K6", "Pay gap (raw, mean)", "Pay Gap Mean %", "Pay Gap", "Raw gender pay gap"),
    ]:
        p.kpi(sid, label, value, f"Delta {note}", f"Color Delta {note}", alt)
    p.lines("A", [("Headcount Prague", "Prague"), ("Headcount Other Entities", "Rest of group")], [ACCENT, CONTEXT],
            title=T("Title Headcount Trend"), subtitle="Headcount at month-end: Prague vs the rest of the group",
            alt="Line chart of headcount over two years. Prague grows steadily while the rest of the group shrinks slightly.")
    slot, msg = column("KeyMessageSlots", "#"), measure("Key Message")
    bx, by, bw, bh = p.card_box("B")
    p.add("B", "tableEx", (bx, by, bw, bh),
          query={"Values": {"projections": [proj(slot, " "), proj(msg, "What the Board should know")]}},
          objects={"columnHeaders": [props(fontSize=13.0, fontColor=color(INK), fontFamily="Segoe UI Semibold",
                                           backColor=color("#FFFFFF"), wordWrap=True, autoSizeColumnWidth=False)],
                   "values": [props(fontSize=10.0, fontColor=color(INK), wordWrap=True,
                                    backColorPrimary=color("#FFFFFF"), backColorSecondary=color("#FFFFFF"))],
                   "grid": [props(gridHorizontal=False, gridVertical=False, rowPadding=6)],
                   "total": [props(totals=False)],
                   "columnWidth": [{**props(value=24.0), "selector": {"metadata": ref(slot)}},
                                   {**props(value=float(bw - 60)), "selector": {"metadata": ref(msg)}}]},
          alt="Three key messages for the Board, generated from the data.", padding=(8, 4, 12, 12))
    p.bars("C", "clusteredBarChart", column("DimDivision", "Division"), [("Turnover R12 %", "Turnover")],
           title=T("Title Turnover by Division"), subtitle=T("Subtitle Turnover by Division"),
           point_color="Color Turnover by Division", sort=[{"field": measure("Turnover R12 %"), "direction": "Descending"}],
           alt="Bar chart of 12-month turnover by division, highest highlighted.")
    p.bars("D", "clusteredBarChart", column("LegalEntities", "Location"),
           [("Headcount PY", "Last year"), ("Headcount", "This year")], title=T("Title Headcount by Entity"),
           subtitle="Headcount by legal entity, this year (blue) vs same month last year (grey)",
           series_colors=[CONTEXT, ACCENT], legend=True, sort=[{"field": measure("Headcount"), "direction": "Descending"}],
           alt="Bar chart comparing headcount by legal entity with the same month last year.")
    return p


def movement() -> Page:
    p = Page("2_movement_attrition", "movementAttrition", "Movement & Attrition", "bg_2_movement_attrition.png")
    p.header("Movement & Attrition", FOOT + "Hires and leavers found by comparing consecutive month-end snapshots. "
                                            "Groups under 5 leavers are hidden.")
    p.add("A", "waterfallChart", p.card_box("A"),
          query={"Category": {"projections": [proj(column("BridgeSteps", "Step"))]},
                 "Y": {"projections": [proj(measure("Bridge Value"), "Change")]}},
          sort=[{"field": column("BridgeSteps", "Step"), "direction": "Ascending"}],
          objects={"categoryAxis": [props(show=True, fontSize=9.0, labelColor=color(INK), showAxisTitle=False)],
                   "valueAxis": [props(show=False, showAxisTitle=False, gridlineShow=False)],
                   "labels": [props(show=True, fontSize=10.0, color=color(INK), labelPosition="OutsideEnd")],
                   "legend": [props(show=False)]},
          title=T("Title Bridge"), subtitle="Headcount bridge, last 12 months · the final bar is closing headcount",
          alt="Waterfall from headcount a year ago, through hires, leavers and transfers, to headcount today.")
    p.lines("B", [("Turnover R12 % Company", "Company"), ("Turnover R12 % Operations", "Operations")], [CONTEXT, ACCENT],
            title=T("Title Turnover Trend"), subtitle=T("Subtitle Turnover Trend"),
            alt="Line chart of rolling 12-month turnover: Operations versus the whole company.")
    p.bars("C", "clusteredBarChart", column("Movements", "Reason Short"), [("Leavers R12", "Leavers")],
           title=T("Title Leaver Reasons"), subtitle=T("Subtitle Leaver Reasons"), point_color="Color Leaver Reason",
           sort=[{"field": measure("Leavers R12"), "direction": "Descending"}],
           alt="Bar chart of leavers by reason over the last 12 months.")
    p.bars("D", "clusteredBarChart", column("DimDivision", "Division"), [("Early Leavers R12 %", "Early leavers")],
           title=T("Title Early Leavers"), subtitle="Leavers within 12 months of joining, % of leavers",
           point_color="Color Early Leavers", sort=[{"field": measure("Early Leavers R12 %"), "direction": "Descending"}],
           alt="Bar chart of the share of leavers who left within their first year, by division.")
    p.bars("E", "clusteredBarChart", column("DimTenureBand", "Tenure Band"), [("Turnover R12 %", "Turnover")],
           title=T("Title Tenure"), subtitle="Turnover by length of service, last 12 months, %",
           point_color="Color Tenure Band", sort=[{"field": column("DimTenureBand", "Tenure Band"), "direction": "Ascending"}],
           alt="Bar chart of turnover by length of service; first-year turnover is highest.")
    return p


def diversity() -> Page:
    p = Page("3_diversity_pay", "diversityPay", "Diversity & Pay", "bg_3_diversity_pay.png")
    p.header("Diversity & Pay", FOOT + "Pay = full-time-equivalent base salary in EUR (ECB monthly rates). "
                                       "Gap = (men's mean − women's mean) ÷ men's mean. Benchmark: Eurostat earn_gr_gpgr2.")
    for sid, label, value, note, alt in [
        ("K1", "Women, all staff", "Women %", "Women", "Share of women among all staff"),
        ("K2", "Women in leadership", "Women in Leadership %", "Women in Leadership", "Share of women in grades G6 and G7"),
        ("K3", "Pay gap, raw (mean)", "Pay Gap Mean %", "Pay Gap", "Raw gender pay gap"),
        ("K4", "Pay gap, like-for-like", "Pay Gap Like-for-like %", "Pay Gap LfL", "Gender pay gap within legal entity and grade"),
    ]:
        p.kpi(sid, label, value, f"Delta {note}", f"Color Delta {note}", alt)
    p.bars("A", "clusteredBarChart", column("Snapshot", "Pay Grade"), [("Women", "Women")],
           title=T("Title Women by Grade"), subtitle="Share of women by pay grade, internal staff, latest month · G5–G7 highlighted",
           point_color="Color Women by Grade", sort=[{"field": column("Snapshot", "Pay Grade"), "direction": "Descending"}],
           alt="Bar chart of the share of women in each pay grade; it drops sharply from grade G5 upwards.")
    p.bars("B", "clusteredBarChart", column("LegalEntities", "Location"),
           [("Pay Gap Mean %", "Our raw gap"), ("Sector Benchmark %", "Financial sector (Eurostat)")],
           title=T("Title Gap vs Benchmark"), subtitle="Raw gender pay gap (mean, FTE salary) vs Eurostat 2024 financial & insurance",
           series_colors=[ACCENT, CONTEXT], legend=True, sort=[{"field": measure("Pay Gap Mean %"), "direction": "Descending"}],
           alt="Bar chart of each entity's raw pay gap next to its country's financial-sector benchmark.")
    p.add("C", "pivotTable", p.card_box("C"),
          query={"Rows": {"projections": [proj(column("LegalEntities", "Location"), "Entity")]},
                 "Columns": {"projections": [proj(column("Snapshot", "Pay Grade"))]},
                 "Values": {"projections": [proj(measure("Like-for-like Cell"), "Gap")]}},
          sort=[{"field": column("Snapshot", "Pay Grade"), "direction": "Ascending"}],
          objects={"subTotals": [props(rowSubtotals=False, columnSubtotals=False)],
                   "values": [props(fontSize=10.0, backColorPrimary=color("#FFFFFF"), backColorSecondary=color("#FFFFFF")),
                              {**props(fontColor=color_by("Color LfL Cell")),
                               "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}],
                                            "metadata": ref(measure("Like-for-like Cell"))}}],
                   "columnHeaders": [props(fontSize=10.0, fontColor=color(INK_2))],
                   "rowHeaders": [props(fontSize=10.0, fontColor=color(INK))],
                   "grid": [props(rowPadding=2, gridVertical=False)]},
          title=T("Title Like-for-like"), subtitle="Gap within legal entity and grade · — = fewer than 5 women or 5 men",
          alt="Table of like-for-like pay gaps by legal entity and grade; values of 5% or more are flagged.")
    return p


def data_quality() -> Page:
    p = Page("4_data_quality", "dataQuality", "Data Quality", "bg_4_data_quality.png")
    p.header("Data Quality", FOOT + "Rules DQ01–DQ08 run on every refresh; every exception has a documented action.")
    for sid, label, value, note in [("K1", "Monthly files loaded", "Files Loaded", "DQ Note Files"),
                                    ("K2", "Rows loaded", "Rows Loaded", "DQ Note Rows"),
                                    ("K3", "Rule exceptions", "Rule Exceptions", "DQ Note Exceptions"),
                                    ("K4", "Rows excluded", "Rows Excluded", "DQ Note Excluded")]:
        p.kpi(sid, label, value, note, None, label)
    p.bars("A", "clusteredBarChart", column("DQ_Rules", "Rule Label"), [("Rule Exceptions", "Exceptions")],
           title=T("Title DQ Rules"), subtitle="Rule exceptions by rule, all files", point_color="Color DQ Rule",
           sort=[{"field": measure("Rule Exceptions"), "direction": "Descending"}],
           alt="Bar chart of data-quality exceptions by rule.")
    p.bars("B", "clusteredColumnChart", column("DimDate", "Month End"), [("Rule Exceptions", "Exceptions")],
           title=T("Title DQ Files"), subtitle="Rule exceptions per monthly export", point_color="Color DQ File",
           sort=[{"field": column("DimDate", "Month End"), "direction": "Ascending"}],
           alt="Column chart of data-quality exceptions per monthly file.")
    p.add("C", "tableEx", p.card_box("C"),
          query={"Values": {"projections": [proj(column("DQ_Exceptions", c), label) for c, label in
                                            (("Severity", "Severity"), ("Rule Label", "Rule"), ("File", "File"),
                                             ("Person ID External", "Person ID"), ("Action Taken", "Action taken"))]}},
          sort=[{"field": column("DQ_Exceptions", "Severity"), "direction": "Ascending"}],
          objects={"columnHeaders": [props(fontSize=10.0, fontColor=color(INK_2), autoSizeColumnWidth=False)],
                   "values": [props(fontSize=10.0, backColorPrimary=color("#FFFFFF"), backColorSecondary=color("#FFFFFF"))],
                   "grid": [props(rowPadding=3, gridVertical=False)],
                   "columnWidth": [{**props(value=float(wd)), "selector": {"metadata": f"DQ_Exceptions.{c}"}} for c, wd in
                                   (("Severity", 90), ("Rule Label", 260), ("File", 130), ("Person ID External", 120),
                                    ("Action Taken", 330))]},
          title="Every exception has a documented action", subtitle="Exception log, most severe first",
          alt="Table listing every data-quality exception with its severity, file and the action taken.")
    return p


# ---------------------------------------------------------------------------
# Writer
# ---------------------------------------------------------------------------

def write_report(folder: Path, model_folder_name: str) -> int:
    if folder.exists():
        shutil.rmtree(folder)
    d = folder / "definition"
    (d / "pages").mkdir(parents=True)
    pages = [board_summary(), movement(), diversity(), data_quality()]

    def dump(path: Path, obj: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    dump(folder / "definition.pbir", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
        "version": "4.0",
        "datasetReference": {"byPath": {"path": f"../{model_folder_name}"}}})
    dump(d / "version.json", {"$schema": f"{SCHEMA}/versionMetadata/1.0.0/schema.json", "version": "2.0.0"})

    res = folder / "StaticResources"
    (res / "SharedResources" / "BaseThemes").mkdir(parents=True)
    (res / "RegisteredResources").mkdir(parents=True)
    shutil.copy(BASE_THEME_FILE, res / "SharedResources" / "BaseThemes" / f"{BASE_THEME}.json")
    shutil.copy(ROOT / "powerbi" / "theme.json", res / "RegisteredResources" / "VltavaBoardPack.json")
    images = []
    for p in pages:
        shutil.copy(ROOT / "powerbi" / "backgrounds" / f"{p.key}.png", res / "RegisteredResources" / p.background)
        images.append({"name": p.background, "path": p.background, "type": "Image"})
    versions = {"visual": V_VISUAL, "report": V_REPORT, "page": V_PAGE}
    dump(d / "report.json", {
        "$schema": f"{SCHEMA}/report/{V_REPORT}/schema.json",
        "themeCollection": {
            "baseTheme": {"name": BASE_THEME, "reportVersionAtImport": versions, "type": "SharedResources"},
            "customTheme": {"name": "VltavaBoardPack.json", "reportVersionAtImport": versions, "type": "RegisteredResources"}},
        "resourcePackages": [
            {"name": "SharedResources", "type": "SharedResources",
             "items": [{"name": BASE_THEME, "path": f"BaseThemes/{BASE_THEME}.json", "type": "BaseTheme"}]},
            {"name": "RegisteredResources", "type": "RegisteredResources",
             "items": [{"name": "VltavaBoardPack.json", "path": "VltavaBoardPack.json", "type": "CustomTheme"}] + images}],
        "settings": {"useStylableVisualContainerHeader": True, "defaultDrillFilterOtherVisuals": True,
                     "useEnhancedTooltips": True, "allowChangeFilterTypes": True}})
    dump(d / "pages" / "pages.json", {"$schema": f"{SCHEMA}/pagesMetadata/1.1.0/schema.json",
                                      "pageOrder": [p.name for p in pages], "activePageName": pages[0].name})
    count = 0
    for p in pages:
        dump(d / "pages" / p.name / "page.json", p.page_json())
        for v in p.visuals:
            dump(d / "pages" / p.name / "visuals" / v["name"] / "visual.json", v)
            count += 1
    return count

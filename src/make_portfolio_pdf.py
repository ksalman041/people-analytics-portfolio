"""
make_portfolio_pdf.py - the 5-page portfolio PDF that goes with the application.

  python src/make_portfolio_pdf.py                         links to the public GitHub repository
  python src/make_portfolio_pdf.py --github ""             without a GitHub link

Output: portfolio/Kamal_Salman_People_Analytics_Portfolio.pdf (A4 landscape)
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "portfolio" / "Kamal_Salman_People_Analytics_Portfolio.pdf"
SHOTS = ROOT / "powerbi" / "screenshots"
W, H = landscape(A4)
M = 36  # page margin

INK, INK_2, ACCENT, CONTEXT, GRID, PAGE, CARD, BAD, GOOD = (
    "#0B0B0B", "#52514E", "#2A78D6", "#898781", "#E1E0D9", "#F9F9F7", "#FFFFFF", "#D03B3B", "#006300")

FONTS = {"R": "segoeui.ttf", "SB": "seguisb.ttf", "B": "segoeuib.ttf", "L": "segoeuil.ttf"}
for key, file in FONTS.items():
    pdfmetrics.registerFont(TTFont(f"Segoe-{key}", rf"C:\Windows\Fonts\{file}"))
pdfmetrics.registerFont(TTFont("Mono", r"C:\Windows\Fonts\consola.ttf"))


# ---------------------------------------------------------------------------
# Drawing helpers (y measured from the top, like the report canvas)
# ---------------------------------------------------------------------------

class Doc:
    def __init__(self, path: Path, footer: str):
        self.c = canvas.Canvas(str(path), pagesize=(W, H))
        self.c.setTitle("Kamal Salman · People Analytics portfolio")
        self.c.setAuthor("Kamal Salman")
        self.c.setSubject("People Analytics work samples: automation, board reporting, reorg validation, data quality")
        self.footer = footer
        self.page_no = 0

    def new_page(self, kicker: str = "", title: str = "", sub: str = "") -> None:
        if self.page_no:
            self.c.showPage()
        self.page_no += 1
        self.rect(0, 0, W, H, PAGE)
        if title:
            self.text(M, 30, kicker.upper(), 8, "SB", ACCENT, spacing=0.8)
            self.text(M, 52, title, 20, "SB")
            if sub:
                self.text(M, 72, sub, 10, "R", INK_2)
        self.text(M, H - 18, self.footer, 7, "R", INK_2)
        self.text(W - M, H - 18, f"{self.page_no} / 5", 7, "R", INK_2, align="right")

    def y(self, top: float) -> float:
        return H - top

    def rect(self, x, top, w, h, fill, stroke=None, r=0):
        c = self.c
        c.setFillColor(fill)
        c.setStrokeColor(stroke or fill)
        c.setLineWidth(0.6)
        if r:
            c.roundRect(x, self.y(top + h), w, h, r, fill=1, stroke=1 if stroke else 0)
        else:
            c.rect(x, self.y(top + h), w, h, fill=1, stroke=1 if stroke else 0)

    def card(self, x, top, w, h):
        self.rect(x, top, w, h, CARD, GRID, r=6)

    def text(self, x, top, s, size=10, weight="R", color=INK, align="left", spacing=0.0):
        c = self.c
        c.setFillColor(color)
        c.setFont(f"Segoe-{weight}", size)
        if spacing:
            c._code.append(f"{spacing} Tc")
        if align == "right":
            c.drawRightString(x, self.y(top), s)
        elif align == "center":
            c.drawCentredString(x, self.y(top), s)
        else:
            c.drawString(x, self.y(top), s)
        if spacing:
            c._code.append("0 Tc")

    def para(self, x, top, s, width, size=9.5, weight="R", color=INK, leading=None) -> float:
        """Wrapped text; returns the y (from top) just below it."""
        leading = leading or size * 1.38
        lines = simpleSplit(s, f"Segoe-{weight}", size, width)
        for i, line in enumerate(lines):
            self.text(x, top + i * leading, line, size, weight, color)
        return top + len(lines) * leading

    def bullets(self, x, top, items, width, size=9.5, gap=4) -> float:
        for item in items:
            if isinstance(item, tuple):
                lead, rest = item
                self.c.setFillColor(ACCENT)
                self.c.circle(x + 2.5, self.y(top - size * 0.35), 1.8, fill=1, stroke=0)
                lead_w = pdfmetrics.stringWidth(lead + " ", "Segoe-SB", size)
                self.text(x + 10, top, lead, size, "SB")
                first = simpleSplit(rest, "Segoe-R", size, width - 10 - lead_w)
                self.text(x + 10 + lead_w, top, first[0] if first else "", size)
                remainder = rest[len(first[0]):].strip() if first else ""
                top = self.para(x + 10, top + size * 1.38, remainder, width - 10, size) if remainder else top + size * 1.38
            else:
                self.c.setFillColor(ACCENT)
                self.c.circle(x + 2.5, self.y(top - size * 0.35), 1.8, fill=1, stroke=0)
                top = self.para(x + 10, top, item, width - 10, size)
            top += gap
        return top

    def image(self, path: Path, x, top, w, border=True) -> float:
        img = ImageReader(str(path))
        iw, ih = img.getSize()
        h = w * ih / iw
        if border:
            self.rect(x - 1, top - 1, w + 2, h + 2, CARD, GRID, r=3)
        self.c.drawImage(img, x, self.y(top + h), w, h, mask="auto")
        return top + h

    def table(self, x, top, rows, widths, size=9, header=True, bold_last=False, aligns=None) -> float:
        line_h = size * 1.75
        for i, row in enumerate(rows):
            is_head = header and i == 0
            weight = "SB" if is_head or (bold_last and i == len(rows) - 1) else "R"
            color = INK_2 if is_head else INK
            cx = x
            for j, (cell, w) in enumerate(zip(row, widths)):
                align = aligns[j] if aligns else ("right" if isinstance(cell, (int, float)) else "left")
                s = str(cell)
                if align == "right":
                    self.text(cx + w - 4, top + i * line_h, s, size, weight, color, align="right")
                else:
                    self.text(cx, top + i * line_h, s, size, weight, color)
                cx += w
            if is_head or (bold_last and i == len(rows) - 2):
                self.c.setStrokeColor(GRID if not is_head else INK_2)
                self.c.setLineWidth(0.6)
                self.c.line(x, self.y(top + i * line_h + size * 0.55), x + sum(widths), self.y(top + i * line_h + size * 0.55))
        return top + len(rows) * line_h

    def code(self, x, top, w, lines, label="", size=8.2) -> float:
        h = 22 + len(lines) * size * 1.5
        self.rect(x, top, w, h, "#F1F0EC", r=4)
        self.c.setFillColor(INK)
        self.c.setFont("Mono", size)
        for i, line in enumerate(lines):
            self.c.drawString(x + 12, self.y(top + 18 + i * size * 1.5), line)
        if label:
            self.text(x + w - 12, top + 16, label, 7.5, "SB", INK_2, align="right")
        return top + h

    def save(self):
        self.c.save()


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

DEMOS = [
    ("D1", "Refresh, don't rebuild", "25 monthly HRIS exports flow through Power Query into one model. A new month is one file "
     "and one click. 8 data-quality rules, each with a documented action.", "\u201cautomate manual recurring reports\u201d"),
    ("D2", "Board Pack in Power BI", "Four pages for the Executive Board. 91 DAX measures, chart titles computed from the data, "
     "a real Eurostat benchmark, row-level security.", "\u201creporting packages for Top Management and the Board\u201d"),
    ("D3", "Reorg in a box", "Excel mapping template that flags errors as HRBPs type; Python checks of spans, layers and "
     "headcount; a one-page memo.", "\u201cquarterly reorganizations across our global entities\u201d"),
    ("D4", "Ticket #4711", "\u201cMy list says 50, the dashboard says 47.\u201d SQL finds the three reasons; a KPI catalog "
     "stops it recurring.", "\u201ctroubleshoot discrepancies\u201d \u00b7 \u201cdefine new People KPIs\u201d"),
    ("Guide", "Visualization standards", "Message titles, one accent colour, IBCS notation, a palette tested for colour "
     "blindness, an accessibility checklist.", "\u201cestablish best practices for data visualization\u201d"),
]


def cover(d: Doc, contact: str) -> None:
    d.new_page()
    d.text(M, 52, "PEOPLE ANALYTICS PORTFOLIO", 9, "SB", ACCENT, spacing=1.0)
    d.text(M, 92, "Kamal Salman", 34, "SB")
    d.text(M, 116, "Prepared for: People Analytics Specialist (f/m/d) \u00b7 Deutsche B\u00f6rse Group, Prague \u00b7 October 2026",
           10, "R", INK_2)
    top = d.para(M, 150, "Four small, working demos built on one fictional company, Vltava Market Group (about 240 people "
                 "in Frankfurt, Prague, Luxembourg and London), to show how I would do this job: automate the monthly "
                 "people report, brief the Board, validate a reorganisation and resolve a \u201cthe numbers don't "
                 "match\u201d ticket, following written visualization standards.", 330, 10.5, leading=15)
    top = d.para(M, top + 10, "Every number is tested. An independent Python calculation matches the Power BI measures "
                 "on 240 out of 240 values.", 330, 10.5, "SB", leading=15)
    d.text(M, top + 18, "Tools", 8.5, "SB", INK_2)
    d.para(M, top + 32, "Power BI (Power Query, DAX, PBIP/TMDL) \u00b7 Excel (XLOOKUP, data validation) \u00b7 SQL (DuckDB) "
           "\u00b7 Python (pandas, matplotlib)", 330, 9, color=INK)
    d.image(SHOTS / "1_board_summary.png", 400, 128, W - M - 400)

    tile_w, gap, tile_top, tile_h = (W - 2 * M - 4 * 10) / 5, 10, 378, 160
    for i, (code, title, body, posting) in enumerate(DEMOS):
        x = M + i * (tile_w + gap)
        d.card(x, tile_top, tile_w, tile_h)
        d.text(x + 12, tile_top + 20, code, 8.5, "SB", ACCENT)
        d.text(x + 12, tile_top + 38, title, 11, "SB")
        d.para(x + 12, tile_top + 56, body, tile_w - 24, 8.2, leading=11)
        d.para(x + 12, tile_top + tile_h - 26, posting, tile_w - 24, 7.8, "R", INK_2, leading=10)
    d.text(M, H - 34, contact, 9, "SB", INK)


def board_pack(d: Doc) -> None:
    d.new_page("D2 \u00b7 Board pack in Power BI", "One page tells the Board what changed",
               "Board Summary, as rendered by Power BI Desktop after refresh (September 2026)")
    bottom = d.image(SHOTS / "1_board_summary.png", M, 90, 520)
    x = M + 540
    width = W - M - x
    d.text(x, 100, "What the Board learns", 11, "SB")
    top = d.bullets(x, 120, [
        ("Turnover is rising:", "14.0% over 12 months, +2.7 pp. Operations is the hotspot at 21.9%, and 7 in 10 of its "
         "leavers quit in year one, which points to onboarding, not pay."),
        ("Growth is Prague-led:", "+29 people in two years while the other entities shrank by 7."),
        ("Pay gap is mostly structure:", "raw 19.6%, like-for-like 3.2%; Luxembourg is double its sector benchmark."),
    ], width, 9.2)
    d.text(x, top + 14, "How it's built", 11, "SB")
    d.bullets(x, top + 34, [
        "Star schema: month-end snapshot and movements facts; date, division, entity dimensions.",
        "91 DAX measures. Rolling-12-month turnover divides by average headcount, not closing.",
        "Every chart title is a measure, so it can't contradict the chart.",
        "Row-level security role per HR Business Partner; figures for fewer than 5 people are hidden.",
        "Generated as a Power BI Project (PBIP): every visual and measure is text, reviewable in Git.",
    ], width, 9.2)
    d.para(M, bottom + 14, "KPI tiles compare with the same month last year; green and red appear only when a change "
           "matters (0.5 pp or more) and always come with an arrow and a sign.", 520, 8.5, color=INK_2)
    cw = (520 - 12) / 2
    d.code(M, bottom + 44, cw, [
        "Turnover R12 % =",
        "VAR _avg = [Avg Headcount R12]",
        "RETURN IF ( [Has Full Year] && _avg >= 5,",
        "    DIVIDE ( [Leavers R12] + 0, _avg ) )",
    ], "DAX")
    d.code(M + cw + 12, bottom + 44, cw, [
        "Title Turnover by Division =",
        "VAR _t = ADDCOLUMNS ( ALLSELECTED (",
        "    DimDivision[Division] ), \"@v\", [Turnover R12 %] )",
        "VAR _top = TOPN ( 1, _t, [@v], DESC ) ...",
    ], "DAX")


def detail_pages(d: Doc) -> None:
    d.new_page("D1 \u00b7 D2 \u00b7 Detail pages and automation", "Detail on demand, and a report that refreshes itself",
               "The other three pages of the Board Pack")
    w = (W - 2 * M - 16) / 2
    b1 = d.image(SHOTS / "2_movement_attrition.png", M, 88, w)
    d.para(M, b1 + 14, "Movement & Attrition: the headcount bridge closes exactly (229 + 43 \u2212 33 = 239); first-year "
           "turnover is 5\u00d7 the rate after year one.", w, 8.5, color=INK_2)
    b2 = d.image(SHOTS / "3_diversity_pay.png", M + w + 16, 88, w)
    d.para(M + w + 16, b2 + 14, "Diversity & Pay: women hold 40\u201347% of G2\u2013G4 roles but at most 31% from G5 up; "
           "one comparable group exceeds the 5% EU Pay Transparency trigger.", w, 8.5, color=INK_2)
    top = b1 + 46
    sw = w * 0.86
    b3 = d.image(SHOTS / "4_data_quality.png", M, top, sw)
    x = M + sw + 18
    d.text(x, top + 10, "D1 \u00b7 Refresh, don't rebuild", 11, "SB")
    d.bullets(x, top + 30, [
        ("One folder, one click:", "Power Query reads all 25 monthly exports; adding October means dropping in one file."),
        ("Rules, not hand fixes:", "8 data-quality checks (duplicates, future-dated records, wrong currency\u2026), each with a severity and an action."),
        ("Tested:", "19 errors planted with an answer key; all 19 found, no false alarms."),
        ("Privacy first:", "names are dropped in the first step; no KPI needs them."),
    ], W - M - x, 9)


def reorg_and_ticket(d: Doc) -> None:
    d.new_page("D3 \u00b7 D4 \u00b7 Reorganisation and a support ticket", "Checks that run before anything goes live",
               "Q3 2026 Technology reorganisation \u00b7 Ticket #4711 from the HR Business Partner for Operations")
    half = (W - 2 * M - 24) / 2
    # D3
    x = M
    d.text(x, 100, "D3 \u00b7 Reorg in a box", 12, "SB")
    top = d.bullets(x, 120, [
        ("First mapping blocked:", "6 issues, including a whole unit missing; 15 people would have dropped out of reporting."),
        ("Final mapping:", "97 positions before and after; the July HRIS matches it for 97 of 97 people."),
        ("For the business to decide:", "the merge adds a management layer (5 \u2192 6) for IT Infrastructure."),
    ], half, 9)
    cw = half * 0.92
    chart_bottom = d.image(ROOT / "portfolio" / "reorg" / "spans.png", x, top + 4, cw)
    metrics = pd.read_csv(ROOT / "data" / "reorg" / "reorg_metrics.csv", index_col=0)
    rows = [["Structure (v2 mapping)", "Before", "After"]]
    for k in ["Positions", "Units", "Average span", "Spans above 12", "Single-report managers", "Layers (CEO to front line)"]:
        b, a = metrics.loc[k, "Before"], metrics.loc[k, "After"]
        fmt = (lambda v: f"{float(v):.1f}") if k == "Average span" else (lambda v: f"{int(float(v))}")
        rows.append([k, fmt(b), fmt(a)])
    d.table(x, chart_bottom + 22, rows, [cw - 120, 60, 60], 8.8, aligns=["left", "right", "right"])
    # D4
    x = M + half + 24
    d.text(x, 100, "D4 \u00b7 Ticket #4711: \u201c50 on my list, 47 on the dashboard\u201d", 12, "SB")
    rec = pd.read_csv(ROOT / "data" / "ticket" / "ticket_4711_reconciliation.csv")
    rows = [["", "People"]]
    labels = {0: "Dashboard, Operations, 30 Sep 2026"}
    for i, r in rec.iterrows():
        text = labels.get(i, r["line"])
        text = (text.replace("+ Scope: external contractor - not an employee, never in headcount", "+ external contractor (not headcount)")
                .replace("= HRBP list, pulled 2 Oct 2026", "= HRBP list, pulled 2 Oct 2026"))
        if text.startswith("+ Cut-off"):
            text = "+ transfer into Operations effective 1 Oct (after cut-off)"
        if text.startswith("+ Future-dated"):
            text = "+ new hire starting 15 Oct (future-dated record)"
        rows.append([text, int(r["people"])])
    d.card(x, 116, half, 128)
    top = d.table(x + 14, 136, rows, [half - 80, 50], 9.5, bold_last=True, aligns=["left", "right"])
    top = d.bullets(x, 262, [
        ("Method:", "reproduce both numbers, anti-join the lists both ways, classify every difference, make it add up."),
        ("Answer:", "both numbers are right; they answer different questions (employees at month-end vs everyone linked on 2 Oct)."),
        ("Prevention:", "one written definition per KPI in the catalog; future-dated records shown on the Data Quality page."),
    ], half, 9)
    d.code(x, top + 6, half, ["SELECT h.* FROM hrbp h", "WHERE NOT EXISTS (", "  SELECT 1 FROM sep_headcount s",
                              "  WHERE s.person_id = h.\"Person ID External\"", "    AND s.division = 'Operations');"],
           "DuckDB", 8.5)


def standards(d: Doc) -> None:
    d.new_page("Standards \u00b7 testing \u00b7 governance", "Written down, tested, safe with people data",
               "From docs/viz_style_guide.md, docs/kpi_catalog.md and docs/governance.md")
    col = (W - 2 * M - 2 * 18) / 3
    x1, x2, x3 = M, M + col + 18, M + 2 * (col + 18)
    for x in (x1, x2, x3):
        d.card(x, 92, col, 352)
    d.text(x1 + 14, 116, "Visualization standards", 11.5, "SB")
    d.bullets(x1 + 14, 138, [
        ("Say the message:", "titles are findings (\u201cOperations loses more than 1 in 5 people a year\u201d), not topics."),
        ("One accent:", "blue for what matters, grey for context; status colours only on changes, with an arrow and a sign."),
        ("IBCS notation:", "actual, previous year and plan always look the same."),
        ("Measured, not eyeballed:", "palette checked under simulated colour blindness; text contrast at least 4.5:1."),
        ("Banned:", "two-axis charts, gauges, 3D, pies for close values."),
        ("Accessible:", "alt text on every chart, set tab order, a table view for every visual."),
    ], col - 28, 8.8)
    d.text(x2 + 14, 116, "How the numbers are tested", 11.5, "SB")
    d.table(x2 + 14, 140, [
        ["Check", "Result"],
        ["DQ rules vs 19 planted errors", "19 / 19"],
        ["Headcount bridge closes", "every month"],
        ["Power BI vs pandas reference", "240 / 240"],
        ["Reorg v1 vs answer key", "6 / 6"],
        ["Reorg v2 vs July HRIS", "97 / 97"],
        ["Ticket reconciliation", "47 + 3 = 50"],
        ["Excel template (calculated by Excel)", "0 errors"],
    ], [col - 110, 80], 8.8, aligns=["left", "right"])
    d.text(x2 + 14, 296, "One definition per KPI", 10, "SB")
    d.para(x2 + 14, 314, "Turnover (rolling 12 months) = leavers in the last 12 months \u00f7 the average of the 12 "
           "month-end headcounts. Dividing by closing headcount would flatter a growing team and penalise a shrinking one.",
           col - 28, 8.8, leading=12.5)
    d.para(x2 + 14, 378, "Each KPI in the catalog names its population, cut-off date, DAX measure and caveats, and the "
           "same definition appears when you hover the measure in Power BI.", col - 28, 8.8, color=INK_2, leading=12.5)
    d.text(x3 + 14, 116, "Governance and confidentiality", 11.5, "SB")
    d.bullets(x3 + 14, 138, [
        ("Synthetic people:", "only Eurostat and ECB data are real, and both are public."),
        ("Data minimisation:", "names never enter the model; pseudonymous IDs only (GDPR Art. 5)."),
        ("Minimum group of 5:", "rates, pay and diversity figures for smaller groups are hidden."),
        ("Least privilege:", "row-level security per HR Business Partner."),
        ("No individual risk scores:", "the EU AI Act treats AI in employment decisions as high-risk; aggregate drivers answer the question."),
        ("Change control:", "the report is generated from code and versioned in Git."),
    ], col - 28, 8.8)
    d.card(M, 458, W - 2 * M, 76)
    d.text(M + 14, 480, "Where to find it", 10.5, "SB")
    d.para(M + 14, 498, "docs/OVERVIEW.md: a short tour and a 5-minute demo script  \u00b7  powerbi/Board_Pack.pbip: the report "
           "(open, then Refresh)  \u00b7  docs/reorg_memo.md and docs/ticket_case.md: the two case studies  \u00b7  "
           "src/run_all.py: rebuilds everything from scratch", W - 2 * M - 28, 9, color=INK_2)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--github", default="https://github.com/ksalman041/people-analytics-portfolio",
                    help="URL of the public GitHub repository")
    args = ap.parse_args()
    links = ["linkedin.com/in/kamal-salman-091411244"]
    if args.github:
        links.insert(0, args.github.replace("https://", ""))
    d = Doc(OUT, "Kamal Salman \u00b7 People Analytics portfolio \u00b7 all people are synthetic; Eurostat and ECB data are real")
    cover(d, "   \u00b7   ".join(links))
    board_pack(d)
    detail_pages(d)
    reorg_and_ticket(d)
    standards(d)
    d.save()
    print(f"Wrote {OUT.relative_to(ROOT)}" + ("" if args.github else "  (no GitHub link: rerun with --github <url> before sending)"))


if __name__ == "__main__":
    main()

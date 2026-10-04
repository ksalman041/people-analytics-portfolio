"""
make_design_assets.py - page backgrounds, wireframes and a layout table for the Power BI pack.

Every page is a 1280 x 720 canvas on an 8 px grid with 24 px margins and 16 px gutters.
The rounded white cards live in a background image, so every page lines up identically
and visuals simply sit inside them with transparent backgrounds.

Outputs
  powerbi/backgrounds/<page>.png     clean background, 2x resolution (2560 x 1440)
  powerbi/wireframes/<page>.png      the same with each slot labelled
  powerbi/wireframes/layout.md       exact x / y / width / height for every visual

Run: python src/make_design_assets.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from viz_style import TOKENS, apply

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "powerbi"
W, H = 1280, 720
INSET = 4  # visuals sit 4 px inside their card so the rounded corners stay visible

# Each slot: (id, x, y, w, h, visual, example message title)
HEADER = [("title", 24, 24, 640, 48, "Textbox", "Page title + 'Vltava Market Group · synthetic data'"),
          ("filters", 856, 24, 400, 48, "Slicers", "One filter row: Month · Division · Legal entity")]


def kpi_row(n: int, y: int = 88, h: int = 104) -> list[tuple]:
    w = (1232 - (n - 1) * 16) // n
    return [(f"K{i + 1}", 24 + i * (w + 16), y, w, h, "Card", "") for i in range(n)]


PAGES = {
    "1_board_summary": {
        "name": "Board Summary",
        "slots": HEADER + [
            *[(k, x, y, w, h, "Card (new)", t) for (k, x, y, w, h, _, _), t in zip(kpi_row(6), [
                "Headcount", "Hires (R12)", "Turnover (R12)", "Voluntary turnover (R12)",
                "Women in leadership", "Gender pay gap (raw, mean)"])],
            ("A", 24, 208, 800, 236, "Line chart (small multiples by entity)", "Headcount +14% in two years - all of it in Prague"),
            ("B", 840, 208, 416, 236, "Textbox", "Three key messages for the Board"),
            ("C", 24, 460, 608, 236, "Bar chart, emphasis", "Operations and Technology lose 1 in 5 people a year"),
            ("D", 648, 460, 608, 236, "Clustered bar: AC vs PY", "Prague +9 people vs last year; other entities flat"),
        ],
    },
    "2_movement_attrition": {
        "name": "Movement & Attrition",
        "slots": HEADER + [
            ("A", 24, 88, 752, 344, "Waterfall", "Headcount bridge, last 12 months: hires outpaced leavers"),
            ("B", 792, 88, 464, 344, "Line chart, emphasis", "Operations turnover runs well above the company"),
            ("C", 24, 448, 368, 248, "Bar chart", "Personal reasons drive 3 in 10 exits"),
            ("D", 408, 448, 368, 248, "Bar chart, emphasis", "60% of Operations leavers quit in year one"),
            ("E", 792, 448, 464, 248, "Bar chart, emphasis", "First-year turnover is twice the later-year rate"),
        ],
    },
    "3_diversity_pay": {
        "name": "Diversity & Pay",
        "slots": HEADER + [
            *[(k, x, y, w, h, "Card (new)", t) for (k, x, y, w, h, _, _), t in zip(kpi_row(4), [
                "Women, all staff", "Women in leadership", "Pay gap, raw (mean)", "Pay gap, like-for-like"])],
            ("A", 24, 208, 608, 488, "100% stacked bar", "Women thin out above grade G4"),
            ("B", 648, 208, 608, 236, "Clustered bar: ours vs Eurostat", "Our raw gaps sit below each country's financial sector"),
            ("C", 648, 460, 608, 236, "Table (n<5 suppressed)", "Like-for-like gaps stay under the 5% Directive trigger"),
        ],
    },
    "4_data_quality": {
        "name": "Data Quality",
        "slots": HEADER + [
            *[(k, x, y, w, h, "Card (new)", t) for (k, x, y, w, h, _, _), t in zip(kpi_row(4), [
                "Files loaded", "Rows loaded", "Rule exceptions", "Rows excluded"])],
            ("A", 24, 208, 608, 276, "Bar chart", "Non-standard location labels are the most common issue"),
            ("B", 648, 208, 608, 276, "Column chart", "Exceptions by monthly file"),
            ("C", 24, 500, 1232, 196, "Table", "Exception detail: rule, file, person, action taken"),
        ],
    },
}


def draw(page: dict, labelled: bool) -> plt.Figure:
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=200)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)
    ax.axis("off")
    fig.patch.set_facecolor(TOKENS["page"])
    for sid, x, y, w, h, visual, note in page["slots"]:
        if sid in ("title", "filters"):  # these sit straight on the page, no card
            if labelled:
                ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=6",
                                            fill=False, ec=TOKENS["baseline"], lw=0.8, ls=(0, (4, 3))))
                ax.text(x + 10, y + h / 2, f"{visual}: {note}", va="center", fontsize=7.5, color=TOKENS["ink_2"])
            continue
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=8",
                                    fc=TOKENS["card"], ec=TOKENS["card_border"], lw=0.6))
        if labelled:
            ax.text(x + 14, y + 20, sid, fontsize=10, fontweight="semibold", color=TOKENS["accent"])
            ax.text(x + 14 + 9 * len(sid) + 8, y + 20, visual, fontsize=8, color=TOKENS["ink_2"])
            if note:
                ax.text(x + 14, y + 40, note, fontsize=8.5 if h > 110 else 8, color=TOKENS["ink"],
                        wrap=True)
    if labelled:
        ax.text(W - 24, H - 8, f"{page['name']} - wireframe - 1280 x 720, 8 px grid", ha="right",
                va="bottom", fontsize=7, color=TOKENS["ink_2"])
    return fig


def main() -> None:
    apply()
    (OUT / "backgrounds").mkdir(parents=True, exist_ok=True)
    (OUT / "wireframes").mkdir(parents=True, exist_ok=True)
    rows = ["# Visual positions", "",
            "Power BI: select a visual > Format > General > Properties > Size and position, then type these values.",
            f"Visuals sit {INSET} px inside their card. Canvas: 1280 x 720 (Format page > Canvas settings > 16:9).", ""]
    for key, page in PAGES.items():
        for labelled, folder in ((False, "backgrounds"), (True, "wireframes")):
            fig = draw(page, labelled)
            fig.savefig(OUT / folder / f"{key}.png", dpi=200, facecolor=TOKENS["page"])
            plt.close(fig)
        rows += [f"## {page['name']}  (`backgrounds/{key}.png`)", "",
                 "| Slot | Visual | X | Y | Width | Height | Title (states the message) |",
                 "|---|---|---|---|---|---|---|"]
        for sid, x, y, w, h, visual, note in page["slots"]:
            i = 0 if sid in ("title", "filters") else INSET
            rows.append(f"| {sid} | {visual} | {x + i} | {y + i} | {w - 2 * i} | {h - 2 * i} | {note} |")
        rows.append("")
    (OUT / "wireframes" / "layout.md").write_text("\n".join(rows), encoding="utf-8")
    print("Wrote", len(PAGES), "backgrounds, wireframes and layout.md")


if __name__ == "__main__":
    main()

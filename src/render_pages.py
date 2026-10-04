"""
render_pages.py - the four Board Pack pages, drawn from the reference numbers.

Same layout (make_design_assets.PAGES), colours (viz_style.TOKENS) and rules
(docs/viz_style_guide.md) as the Power BI report, so these images can go into the
README, the portfolio PDF and the board memo. Every chart title is computed from the
data, so a title can never contradict its chart.

Output: portfolio/pages/<page>.png (2560 x 1440)
Run:    python src/render_pages.py
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch

import reference_kpis as rk
from make_design_assets import PAGES, H, W
from viz_style import TOKENS as T, apply

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "portfolio" / "pages"
MONTH, PY = "2026-09", "2025-09"
MONTH_LABEL, PY_LABEL = "Sep 2026", "Sep 2025"
MIN_GROUP = rk.MIN_GROUP
SHORT_ENTITY = {"VMG Czech Republic s.r.o.": "Prague", "VMG Deutschland GmbH": "Frankfurt",
                "VMG Luxembourg S.A.": "Luxembourg", "VMG UK Ltd": "London"}
ENTITY_COUNTRY = {"VMG Czech Republic s.r.o.": "Czechia", "VMG Deutschland GmbH": "Germany",
                  "VMG Luxembourg S.A.": "Luxembourg", "VMG UK Ltd": "United Kingdom"}
SOURCE = "Source: monthly HRIS exports, Vltava Market Group (synthetic data). "
FOOTNOTES = {
    "1_board_summary": SOURCE + "Turnover = leavers in last 12 months ÷ average month-end headcount. Groups under 5 people are hidden (—).",
    "2_movement_attrition": SOURCE + "Hires and leavers found by comparing consecutive month-end snapshots. Groups under 5 leavers are hidden (—).",
    "3_diversity_pay": SOURCE + "Pay = full-time-equivalent base salary in EUR (ECB monthly rates). Gap = (men's mean − women's mean) ÷ men's mean. "
                       "Benchmark: Eurostat earn_gr_gpgr2.",
    "4_data_quality": SOURCE + "Rules DQ01–DQ08 run on every refresh; every exception has a documented action.",
}

# Font sizes: the canvas is 1280 x 720 "px"; 1 px = 0.72 pt here, so Power BI's 14 pt ≈ 13.5 pt.
F_PAGE, F_TITLE, F_SUB, F_BODY, F_TICK, F_LABEL, F_KPI, F_FOOT = 17, 13, 9, 10, 8.5, 8.5, 23, 7.5


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

def load() -> dict:
    raw = rk.load_exports()
    fx = pd.read_csv(rk.DATA / "external" / "fx_rates_monthly.csv")
    reasons = pd.read_csv(rk.DATA / "reference" / "termination_reasons.csv")
    snap = rk.clean(raw, fx)
    mv = rk.movements(snap, reasons)
    kpis = pd.read_csv(rk.DATA / "reference" / "reference_kpis.csv")
    found = rk.dq_exceptions(raw)
    gpg = pd.read_csv(rk.DATA / "external" / "eurostat_gender_pay_gap.csv")
    return {"raw": raw, "snap": snap, "mv": mv, "kpis": kpis, "dq": found, "gpg": gpg}


def kpi(d: dict, name: str, scope: str = "Company", month: str = MONTH) -> float:
    k = d["kpis"]
    v = k[(k["Scope"] == scope) & (k["KPI"] == name) & (k["Month"] == month)]["Value"]
    return float(v.iloc[0]) if len(v) else np.nan


def series(d: dict, name: str, scope: str = "Company") -> pd.Series:
    k = d["kpis"]
    return k[(k["Scope"] == scope) & (k["KPI"] == name)].set_index("Month")["Value"].sort_index()


def r12_months(month: str = MONTH) -> list[str]:
    end = pd.Period(month, "M")
    return [str(end - i) for i in range(11, -1, -1)]


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

def signed(v: float, decimals: int = 0) -> str:
    """+3 / −3 / ±0, with a real minus sign."""
    if round(v, decimals) == 0:
        return "±0"
    return f"{v:+.{decimals}f}".replace("-", "−")


def fmt_delta(delta: float, unit: str, direction: str) -> tuple[str, str]:
    """Arrow + signed change + colour. direction: 'up_good', 'down_good' or 'neutral'.
    Changes under 0.5 pp are shown in neutral grey: too small to call good or bad."""
    if np.isnan(delta):
        return "", T["ink_2"]
    decimals = 1 if unit == " pp" else 0
    if round(delta, decimals) == 0:
        return f"► ±0{unit}", T["ink_2"]
    arrow = "▲" if delta > 0 else "▼"
    text = f"{arrow} {signed(delta, decimals)}{unit}"
    good = (delta > 0) == (direction == "up_good")
    material = not (unit == " pp" and abs(delta) < 0.5)
    color = T["ink_2"] if direction == "neutral" or not material else (T["good_text"] if good else T["bad"])
    return text, color


class Page:
    def __init__(self, key: str, title: str):
        self.key = key
        self.slots = {s[0]: s[1:5] for s in PAGES[key]["slots"]}
        self.fig = plt.figure(figsize=(W / 100, H / 100), dpi=200)
        self.fig.patch.set_facecolor(T["page"])
        b = self.base = self.fig.add_axes([0, 0, 1, 1], zorder=0)
        b.set_xlim(0, W)
        b.set_ylim(H, 0)
        b.axis("off")
        b.text(24, 41, title, fontsize=F_PAGE, fontweight="semibold", color=T["ink"], va="center")
        b.text(24, 64, f"Vltava Market Group  ·  {MONTH_LABEL}  ·  synthetic data", fontsize=F_SUB,
               color=T["ink_2"], va="center")
        for i, (label, value) in enumerate([("Month", MONTH_LABEL), ("Division", "All"), ("Legal entity", "All")]):
            x = 856 + i * 136
            b.add_patch(FancyBboxPatch((x, 30), 128, 36, boxstyle="round,pad=0,rounding_size=6",
                                       fc=T["card"], ec=T["card_border"], lw=0.6))
            b.text(x + 10, 42, label, fontsize=7, color=T["ink_2"], va="center")
            b.text(x + 10, 56, value, fontsize=8.5, color=T["ink"], va="center")
            b.text(x + 116, 49, "▼", fontsize=5.5, color=T["ink_2"], va="center", ha="right")
        b.text(24, H - 9, FOOTNOTES[key], fontsize=F_FOOT, color=T["ink_2"], va="center")

    def card(self, sid: str, title: str = "", subtitle: str = "") -> tuple:
        """Draw a card with a message title. If the title wraps to two lines, the returned
        content box starts lower, so charts placed relative to it never collide with the title."""
        x, y, w, h = self.slots[sid]
        self.base.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=8",
                                           fc=T["card"], ec=T["card_border"], lw=0.6))
        extra = 0
        if title:
            lines = textwrap.wrap(title, int(w / 8.6))
            assert len(lines) <= 2, f"title too long for card {sid}: {title}"
            extra = 19 * (len(lines) - 1)
            self.base.text(x + 16, y + 22, "\n".join(lines), fontsize=F_TITLE, fontweight="semibold",
                           color=T["ink"], va="center", linespacing=1.25)
            if subtitle:
                self.base.text(x + 16, y + 41 + extra, subtitle, fontsize=F_SUB, color=T["ink_2"], va="center")
        return x, y + extra, w, h - extra

    def axes(self, x: float, y: float, w: float, h: float) -> plt.Axes:
        ax = self.fig.add_axes([x / W, 1 - (y + h) / H, w / W, h / H], zorder=1)
        ax.set_facecolor("none")
        return ax

    def text(self, x, y, s, **kw):
        kw.setdefault("fontsize", F_BODY)
        kw.setdefault("color", T["ink"])
        return self.base.text(x, y, s, **kw)

    def save(self) -> Path:
        OUT.mkdir(parents=True, exist_ok=True)
        path = OUT / f"{self.key}.png"
        self.fig.savefig(path, dpi=200, facecolor=T["page"])
        plt.close(self.fig)
        return path


def kpi_tile(p: Page, sid: str, label: str, value: str, delta: tuple[str, str], spark: pd.Series | None):
    x, y, w, h = p.card(sid)
    p.text(x + 14, y + 20, label, fontsize=F_SUB, color=T["ink_2"], va="center")
    p.text(x + 14, y + 53, value, fontsize=F_KPI, fontweight="semibold", va="center")
    text, color = delta
    if text:
        t = p.text(x + 14, y + 86, text, fontsize=F_LABEL, color=color, va="center", fontweight="semibold")
        p.text(x + 14 + 7.2 * len(text) + 6, y + 86, f"vs {PY_LABEL}", fontsize=F_LABEL, color=T["ink_2"], va="center")
    if spark is not None and spark.notna().sum() > 2:
        s = spark.dropna()
        ax = p.axes(x + w - 76, y + 38, 62, 30)
        ax.plot(range(len(s)), s.values, color=T["context"], lw=1.3, solid_capstyle="round")
        ax.scatter([len(s) - 1], [s.values[-1]], s=14, color=T["accent"], zorder=3, edgecolors=T["card"], linewidths=1)
        ax.axis("off")
        pad = (s.max() - s.min()) * 0.15 or 1
        ax.set_ylim(s.min() - pad, s.max() + pad)


def style_axis(ax, grid: str = "x"):
    """Recessive chrome: no spines, no tick marks, a light solid grid on one axis (or none)."""
    ax.tick_params(labelsize=F_TICK, colors=T["ink_2"], length=0)
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(False)
    ax.grid(False)
    if grid in ("x", "y"):
        ax.grid(axis=grid, color=T["grid"], lw=0.7)
    ax.set_axisbelow(True)


def hbars(ax, labels, values, colors, fmt="{:.1f}%", suppressed=None, xmax=None, ref=None, ref_label=""):
    """Horizontal bars, top-to-bottom in the given order, value at the tip; '—' for suppressed."""
    n = len(labels)
    ypos = np.arange(n)[::-1]
    vals = [0 if (suppressed and suppressed[i]) or pd.isna(v) else v for i, v in enumerate(values)]
    xmax = xmax or max(vals) * 1.22
    ax.barh(ypos, vals, height=0.56, color=colors, zorder=2)
    for i, (yp, v) in enumerate(zip(ypos, values)):
        hidden = (suppressed and suppressed[i]) or pd.isna(v)
        ax.text((0 if hidden else v) + xmax * 0.015, yp, "—" if hidden else fmt.format(v), va="center",
                fontsize=F_LABEL, color=T["ink"] if not hidden else T["ink_2"], zorder=5,
                bbox=dict(fc=T["card"], ec="none", pad=0.8))
    ax.set_yticks(ypos, labels)
    ax.set_xlim(0, xmax)
    ax.set_xticks([])
    style_axis(ax, grid="none")
    ax.grid(False)
    ax.axvline(0, color=T["baseline"], lw=0.8, zorder=1)
    if ref is not None:
        ax.axvline(ref, color=T["ink"], lw=1, zorder=4)
        ax.text(ref + xmax * 0.012, n - 0.45, f"{ref_label} {ref:.1f}%", fontsize=F_LABEL - 0.5, color=T["ink"],
                ha="left", va="bottom")
        ax.set_ylim(-0.6, n - 0.05)


# ---------------------------------------------------------------------------
# Page 1 - Board Summary
# ---------------------------------------------------------------------------

def page_board_summary(d: dict) -> Path:
    snap, mv = d["snap"], d["mv"]
    p = Page("1_board_summary", "Board Summary")
    hc_s = series(d, "Headcount")
    hires_r12 = series(d, "Hires").rolling(12).sum()

    tiles = [
        ("K1", "Headcount", f"{kpi(d, 'Headcount'):.0f}", kpi(d, "Headcount") - kpi(d, "Headcount", month=PY), "", "neutral", hc_s),
        ("K2", "Hires, last 12 months", f"{hires_r12[MONTH]:.0f}", hires_r12[MONTH] - hires_r12[PY], "", "neutral", hires_r12),
        ("K3", "Turnover, last 12 months", f"{kpi(d, 'Turnover R12 %'):.1f}%",
         kpi(d, "Turnover R12 %") - kpi(d, "Turnover R12 %", month=PY), " pp", "down_good", series(d, "Turnover R12 %")),
        ("K4", "Voluntary turnover, 12 months", f"{kpi(d, 'Voluntary Turnover R12 %'):.1f}%",
         kpi(d, "Voluntary Turnover R12 %") - kpi(d, "Voluntary Turnover R12 %", month=PY), " pp", "down_good",
         series(d, "Voluntary Turnover R12 %")),
        ("K5", "Women in leadership", f"{kpi(d, 'Women in Leadership %'):.1f}%",
         kpi(d, "Women in Leadership %") - kpi(d, "Women in Leadership %", month=PY), " pp", "up_good",
         series(d, "Women in Leadership %")),
        ("K6", "Gender pay gap (raw, mean)", f"{kpi(d, 'Pay Gap Mean %'):.1f}%",
         kpi(d, "Pay Gap Mean %") - kpi(d, "Pay Gap Mean %", month=PY), " pp", "down_good", series(d, "Pay Gap Mean %")),
    ]
    for sid, label, value, delta, unit, direction, spark in tiles:
        kpi_tile(p, sid, label, value, fmt_delta(delta, unit, direction), spark)

    # A - headcount by entity, small multiples on one shared scale
    hc = snap[snap["Is Headcount"]].groupby(["Month", "Legal Entity"]).size().unstack().sort_index()
    first = hc.index[0]
    change = hc.loc[MONTH] - hc.loc[first]
    cz = "VMG Czech Republic s.r.o."
    rest = change.drop(cz).sum()
    total_pct = (hc.loc[MONTH].sum() / hc.loc[first].sum() - 1) * 100
    title = (f"Headcount +{total_pct:.0f}% in two years: Prague added {change[cz]:.0f}, "
             f"the other entities {'lost' if rest < 0 else 'added'} {abs(rest):.0f}")
    x, y, w, h = p.card("A", title, f"Headcount at month-end by legal entity, {first[:4]}–{MONTH[:4]}, same scale")
    order = [cz, "VMG Deutschland GmbH", "VMG Luxembourg S.A.", "VMG UK Ltd"]
    ymax = hc.values.max() * 1.18
    pw = (w - 32 - 3 * 20) / 4
    for i, ent in enumerate(order):
        ax = p.axes(x + 16 + i * (pw + 20), y + 92, pw, h - 92 - 30)
        s = hc[ent]
        color = T["accent"] if ent == cz else T["context"]
        ax.plot(range(len(s)), s.values, color=color, lw=2, solid_capstyle="round", zorder=3)
        ax.scatter([len(s) - 1], [s.values[-1]], s=16, color=color, zorder=4, edgecolors=T["card"], linewidths=1.2)
        ax.text(len(s) - 1, s.values[-1] + ymax * 0.06, f"{s.values[-1]:.0f}", ha="right", fontsize=F_LABEL,
                fontweight="semibold", color=T["ink"])
        ax.set_ylim(0, ymax)
        ax.set_xlim(-0.5, len(s) - 0.5)
        ax.set_xticks([0, len(s) - 1], [pd.Period(s.index[0]).strftime("%b %y"), pd.Period(s.index[-1]).strftime("%b %y")])
        for lbl, ha in zip(ax.get_xticklabels(), ("left", "right")):
            lbl.set_horizontalalignment(ha)
        ax.set_yticks([0, 50, 100] if i == 0 else [])
        style_axis(ax, grid="y")
        ax.axhline(0, color=T["baseline"], lw=0.8)
        delta = change[ent]
        p.text(x + 16 + i * (pw + 20), y + 82, f"{SHORT_ENTITY[ent]}", fontsize=F_LABEL + 0.5, fontweight="semibold", va="center")
        p.text(x + 16 + i * (pw + 20) + 8.0 * len(SHORT_ENTITY[ent]) + 8, y + 82, signed(delta),
               fontsize=F_LABEL, color=T["ink_2"], va="center")

    # B - key messages
    x, y, w, h = p.card("B", "What the Board should know")
    ops_to, co_to = kpi(d, "Turnover R12 %", "Operations"), kpi(d, "Turnover R12 %")
    ops_early = kpi(d, "Early Leavers R12 %", "Operations")
    lu = "VMG Luxembourg S.A."
    lu_gap = kpi(d, "Pay Gap Mean %", lu)
    lu_bench = d["gpg"].query("Geo == 'Luxembourg' and Activity == 'Financial & insurance'").sort_values("Year")["Pay Gap %"].iloc[-1]
    msgs = [
        ("Turnover is rising.", f"{co_to:.1f}% over 12 months ({signed(kpi(d, 'Turnover R12 %') - kpi(d, 'Turnover R12 %', month=PY), 1)} pp). "
         f"Operations is the hotspot at {ops_to:.1f}%, and {ops_early / 10:.0f} in 10 of its leavers quit in year one: "
         "review onboarding."),
        ("Growth is Prague-led.", f"Prague {signed(change[cz])} people in two years; the other entities {signed(rest)}."),
        ("Pay gap is mostly structure.", f"Raw gap {kpi(d, 'Pay Gap Mean %'):.1f}%, like-for-like {kpi(d, 'Pay Gap Adjusted %'):.1f}% "
         f"(under the 5% EU trigger). Luxembourg's raw gap is {'double' if 1.8 <= lu_gap / lu_bench < 2.3 else f'{lu_gap / lu_bench:.1f}x'} its sector benchmark: investigate."),
    ]
    ty = y + 52
    for i, (lead, body) in enumerate(msgs, 1):
        p.text(x + 16, ty, f"{i}", fontsize=F_BODY + 1, fontweight="semibold", color=T["accent"], va="top")
        wrapped = textwrap.wrap(f"{lead} {body}", 58)
        p.text(x + 34, ty, lead, fontsize=F_BODY - 0.5, fontweight="semibold", va="top")
        rest_text = "\n".join(textwrap.wrap(body, 60))
        p.text(x + 34, ty + 15, rest_text, fontsize=F_BODY - 0.8, color=T["ink"], va="top", linespacing=1.35)
        ty += 15 + 15 * len(textwrap.wrap(body, 60)) + 10
        del wrapped

    # C - turnover by division
    divs = ["Operations", "Markets", "Technology", "Corporate Functions", "Executive Board"]
    vals = [kpi(d, "Turnover R12 %", dv) for dv in divs]
    order_idx = sorted(range(len(divs)), key=lambda i: (np.isnan(vals[i]), -np.nan_to_num(vals[i])))
    divs, vals = [divs[i] for i in order_idx], [vals[i] for i in order_idx]
    top = divs[0]
    frac = vals[0] / 100
    in_n = round(1 / frac) if frac > 0 else 0
    x, y, w, h = p.card("C", f"{top} loses more than 1 in {in_n} people a year" if frac > 1 / in_n else
                        f"{top} loses about 1 in {in_n} people a year",
                        f"Turnover, last 12 months to {MONTH_LABEL}, % · line = company")
    ax = p.axes(x + 150, y + 72, w - 150 - 24, h - 72 - 14)
    hbars(ax, divs, vals, [T["accent"] if dv == top else T["context"] for dv in divs],
          suppressed=[np.isnan(v) for v in vals], ref=co_to, ref_label="Company", xmax=max(np.nan_to_num(vals)) * 1.25)
    ax.tick_params(axis="y", labelsize=F_TICK + 0.5, colors=T["ink"])

    # D - headcount by entity, this year vs last year
    ents = order
    ac = [hc.loc[MONTH, e] for e in ents]
    py = [hc.loc[PY, e] for e in ents]
    yoy = [a - b for a, b in zip(ac, py)]
    best = ents[int(np.argmax(yoy))]
    others = [v for e, v in zip(ents, yoy) if e != best]
    others_txt = "others flat" if all(v == 0 for v in others) else f"others {signed(sum(others))}"
    x, y, w, h = p.card("D", f"{SHORT_ENTITY[best]} +{max(yoy):.0f} people vs last year; {others_txt}",
                        f"Headcount by legal entity, {MONTH_LABEL} (blue) vs {PY_LABEL} (grey)")
    ax = p.axes(x + 104, y + 72, w - 104 - 70, h - 72 - 14)
    ypos = np.arange(len(ents))[::-1]
    ax.barh(ypos + 0.17, py, height=0.32, color=T["context"], zorder=2)
    ax.barh(ypos - 0.17, ac, height=0.32, color=T["accent"], zorder=2)
    xmax = max(ac + py) * 1.12
    for yp, a, dlt in zip(ypos, ac, yoy):
        ax.text(a + xmax * 0.012, yp - 0.17, f"{a:.0f}", va="center", fontsize=F_LABEL, color=T["ink"])
        txt, col = fmt_delta(dlt, "", "neutral")
        ax.text(xmax * 1.02, yp, txt if txt else "", va="center", fontsize=F_LABEL, color=T["ink_2"], clip_on=False)
    ax.set_yticks(ypos, [SHORT_ENTITY[e] for e in ents])
    ax.set_xlim(0, xmax)
    ax.set_xticks([])
    style_axis(ax, grid="none")
    ax.grid(False)
    ax.tick_params(axis="y", labelsize=F_TICK + 0.5, colors=T["ink"])
    ax.axvline(0, color=T["baseline"], lw=0.8)
    return p.save()


# ---------------------------------------------------------------------------
# Page 2 - Movement & Attrition
# ---------------------------------------------------------------------------

def page_movement(d: dict) -> Path:
    snap, mv = d["snap"], d["mv"]
    p = Page("2_movement_attrition", "Movement & Attrition")
    window = r12_months()
    m12 = mv[mv["Month"].isin(window)]
    leavers = m12[m12["Movement"] == "Leaver"]
    opening, closing = kpi(d, "Headcount", month=PY), kpi(d, "Headcount")
    hires = (m12["Movement"] == "Hire").sum()
    cats = leavers["Leaver Category"].value_counts()

    # A - headcount bridge (waterfall)
    steps = [("Opening\n" + PY_LABEL, opening, "total"), ("Hires", hires, "up"),
             ("Voluntary\nleavers", -cats.get("Voluntary", 0), "down"),
             ("Involuntary\nleavers", -cats.get("Involuntary", 0), "down"),
             ("Retirements", -cats.get("Retirement", 0), "down"), ("Closing\n" + MONTH_LABEL, closing, "total")]
    assert opening + hires - len(leavers) == closing, "bridge does not close"
    x, y, w, h = p.card("A", f"Headcount {closing - opening:+.0f} in 12 months: {hires} hires outpaced {len(leavers)} leavers",
                        f"Headcount bridge, {PY_LABEL} → {MONTH_LABEL} · internal transfers net to zero at company level")
    ax = p.axes(x + 24, y + 76, w - 48, h - 76 - 40)
    level = 0
    lo = 0  # bars start at zero (IBCS "Check"): a cut axis would exaggerate the changes
    peak = opening + hires
    for i, (label, v, kind) in enumerate(steps):
        if kind == "total":
            bottom, height, color = lo, v - lo, T["ink_2"]
            level = v
            top = v
        else:
            bottom = level if v > 0 else level + v
            height, color = abs(v), (T["accent"] if v > 0 else T["context"])
            top = level + max(v, 0)
            level += v
        ax.bar(i, height, bottom=bottom, width=0.56, color=color, zorder=2)
        ax.text(i, top + peak * 0.012, f"{v:.0f}" if kind == "total" else signed(v), ha="center",
                va="bottom", fontsize=F_LABEL + 0.5, fontweight="semibold", color=T["ink"])
        if i < len(steps) - 1:
            ax.plot([i + 0.28, i + 0.72], [level, level], color=T["baseline"], lw=0.8, zorder=1)
    ax.set_xticks(range(len(steps)), [s[0] for s in steps])
    ax.set_ylim(0, peak * 1.1)
    ax.set_yticks([])
    style_axis(ax, grid="none")
    ax.tick_params(axis="x", labelsize=F_TICK, colors=T["ink"])
    ax.axhline(0, color=T["baseline"], lw=0.8)

    # B - rolling turnover: company vs Operations
    co = series(d, "Turnover R12 %").dropna()
    ops = series(d, "Turnover R12 %", "Operations").reindex(co.index)
    gap = (ops - co).mean()
    always_above = bool((ops > co).all())
    x, y, w, h = p.card("B", f"Operations turnover {'above the company all year' if always_above else 'runs above the company'}",
                        f"Turnover, rolling 12 months, % · gap averages {gap:.0f} pp")
    ax = p.axes(x + 40, y + 88, w - 40 - 96, h - 88 - 34)
    xs = range(len(co))
    ax.plot(xs, co.values, color=T["context"], lw=2, zorder=3)
    ax.plot(xs, ops.values, color=T["accent"], lw=2, zorder=3)
    for s, name, color in ((co, "Company", T["context"]), (ops, "Operations", T["accent"])):
        ax.scatter([len(s) - 1], [s.values[-1]], s=16, color=color, zorder=4, edgecolors=T["card"], linewidths=1.2)
        ax.text(len(s) - 0.6, s.values[-1], f"{name} {s.values[-1]:.1f}%", va="center", fontsize=F_LABEL,
                color=T["ink"], clip_on=False)
    ax.set_ylim(0, max(ops.max(), co.max()) * 1.2)
    ax.set_xticks([0, len(co) // 2, len(co) - 1],
                  [pd.Period(co.index[i]).strftime("%b %y") for i in (0, len(co) // 2, len(co) - 1)])
    style_axis(ax, grid="y")
    ax.axhline(0, color=T["baseline"], lw=0.8)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")

    # C - leavers by reason
    short = {"Resignation - Career Opportunity": "Career move", "Resignation - Compensation": "Pay",
             "Resignation - Personal Reasons": "Personal", "Resignation - Relocation": "Relocation",
             "End of Fixed-Term Contract": "Contract ended", "Dismissal - Performance": "Performance",
             "Redundancy": "Redundancy", "Retirement": "Retirement"}
    phrase = {"Career move": "Career moves", "Pay": "Pay", "Personal": "Personal reasons", "Relocation": "Relocation",
              "Contract ended": "Contract ends", "Performance": "Performance exits", "Redundancy": "Redundancies",
              "Retirement": "Retirements"}
    reasons = leavers["Event Reason"].map(short).value_counts()
    top_share = reasons.iloc[0] / reasons.sum()
    x, y, w, h = p.card("C", f"{phrase[reasons.index[0]]} drive {top_share * 10:.0f} in 10 exits",
                        f"Leavers by reason, last 12 months (n={reasons.sum()})")
    ax = p.axes(x + 104, y + 70, w - 104 - 24, h - 70 - 8)
    hbars(ax, list(reasons.index), list(reasons.values), [T["accent"]] + [T["context"]] * (len(reasons) - 1), fmt="{:.0f}")
    ax.tick_params(axis="y", labelsize=F_TICK, colors=T["ink"])

    # D - early leavers by division (share of leavers who left within 12 months)
    divs = ["Operations", "Markets", "Technology", "Corporate Functions"]
    shares, hidden = [], []
    for dv in divs:
        lv = leavers[leavers["Division"] == dv]
        shares.append((lv["Tenure Months At Exit"] < 12).mean() * 100 if len(lv) else np.nan)
        hidden.append(len(lv) < MIN_GROUP)
    ops_share = shares[0]
    x, y, w, h = p.card("D", f"{ops_share / 10:.0f} in 10 Operations leavers quit in year 1",
                        "Leavers within 12 months of joining, % of leavers")
    ax = p.axes(x + 128, y + 72, w - 128 - 24, h - 72 - 10)
    hbars(ax, divs, shares, [T["accent"]] + [T["context"]] * 3, suppressed=hidden, xmax=100)
    ax.tick_params(axis="y", labelsize=F_TICK, colors=T["ink"])

    # E - turnover by tenure band
    hc12 = snap[snap["Is Headcount"] & snap["Month"].isin(window)].copy()
    bins, labels = [0, 12, 24, 60, 1e9], ["< 1 year", "1–2 years", "2–5 years", "5+ years"]
    hc12["band"] = pd.cut(hc12["Tenure Months"], bins, labels=labels, right=False)
    lv = leavers.copy()
    lv["band"] = pd.cut(lv["Tenure Months At Exit"], bins, labels=labels, right=False)
    avg = hc12.groupby("band", observed=False).size() / 12
    rate = (lv.groupby("band", observed=False).size() / avg * 100).reindex(labels)
    later = len(lv[lv["band"] != "< 1 year"]) / avg.drop("< 1 year").sum() * 100
    ratio = rate["< 1 year"] / later
    x, y, w, h = p.card("E", f"First-year turnover is {ratio:.0f}x the rate after year one" if ratio >= 3 else f"First-year turnover is {ratio:.1f}x the rate after year one",
                        "Turnover by length of service, last 12 months, %")
    ax = p.axes(x + 96, y + 72, w - 96 - 24, h - 72 - 10)
    hbars(ax, labels, list(rate.values), [T["accent"]] + [T["context"]] * 3)
    ax.tick_params(axis="y", labelsize=F_TICK, colors=T["ink"])
    return p.save()


# ---------------------------------------------------------------------------
# Page 3 - Diversity & Pay
# ---------------------------------------------------------------------------

def page_diversity(d: dict) -> Path:
    snap = d["snap"]
    p = Page("3_diversity_pay", "Diversity & Pay")
    now = snap[(snap["Month"] == MONTH) & snap["Is Headcount"]]
    before = snap[(snap["Month"] == PY) & snap["Is Headcount"]]
    women = lambda df: (df["Gender"] == "Female").mean() * 100  # noqa: E731

    tiles = [
        ("K1", "Women, all staff", women(now), women(now) - women(before), "up_good", None),
        ("K2", "Women in leadership (G6–G7)", kpi(d, "Women in Leadership %"),
         kpi(d, "Women in Leadership %") - kpi(d, "Women in Leadership %", month=PY), "up_good", series(d, "Women in Leadership %")),
        ("K3", "Pay gap, raw (mean)", kpi(d, "Pay Gap Mean %"), kpi(d, "Pay Gap Mean %") - kpi(d, "Pay Gap Mean %", month=PY),
         "down_good", series(d, "Pay Gap Mean %")),
        ("K4", "Pay gap, like-for-like", kpi(d, "Pay Gap Adjusted %"),
         kpi(d, "Pay Gap Adjusted %") - kpi(d, "Pay Gap Adjusted %", month=PY), "down_good", series(d, "Pay Gap Adjusted %")),
    ]
    women_series = snap[snap["Is Headcount"]].groupby("Month")["Gender"].apply(lambda g: (g == "Female").mean() * 100)
    for sid, label, value, delta, direction, spark in tiles:
        kpi_tile(p, sid, label, f"{value:.1f}%", fmt_delta(delta, " pp", direction),
                 women_series if sid == "K1" else spark)

    # A - gender mix by grade (100% stacked)
    known = now[now["Gender"].isin(["Female", "Male"])]
    grades = sorted(known["Grade"].dropna().unique())
    share = known.groupby("Grade")["Gender"].apply(lambda g: (g == "Female").mean() * 100).reindex(grades)
    count = known.groupby("Grade").size().reindex(grades)
    mid, senior = share[[2, 3, 4]], share[[5, 6, 7]]
    x, y, w, h = p.card("A", f"Women hold {mid.min():.0f}–{mid.max():.0f}% of G2–G4 roles, but at most {senior.max():.0f}% from G5 up",
                        f"Share of women and men by pay grade, {MONTH_LABEL}, internal staff")
    ax = p.axes(x + 130, y + 104, w - 130 - 70, h - 104 - 40)
    ypos = np.arange(len(grades))  # G1 at the bottom, seniority goes up
    ax.barh(ypos, share.values, height=0.6, color=T["series"][0], zorder=2)
    ax.barh(ypos, 100 - share.values, left=share.values + 0.6, height=0.6, color=T["series"][1], zorder=2)
    yaxis = ax.get_yaxis_transform()  # x in axes fraction, y in data units
    for yp, g in zip(ypos, grades):
        # labels sit outside the bars in dark text: white on blue is only 4.4:1
        ax.text(-0.25, yp, f"G{g:.0f}", ha="left", va="center", fontsize=F_TICK + 0.5, color=T["ink"], transform=yaxis)
        ax.text(-0.02, yp, f"{share[g]:.0f}% women", ha="right", va="center", fontsize=F_LABEL, color=T["ink"],
                fontweight="semibold", transform=yaxis)
        ax.text(102, yp, f"n={count[g]:.0f}", va="center", fontsize=F_LABEL - 0.5, color=T["ink_2"])
    ax.set_xlim(0, 100)
    ax.axis("off")
    ax.axvline(50, color=T["card"], lw=1.2, zorder=3)
    lx, ly = x + 130, y + 84
    for i, (name, color) in enumerate((("Women", T["series"][0]), ("Men", T["series"][1]))):
        p.base.add_patch(FancyBboxPatch((lx + i * 80, ly - 5), 10, 10, boxstyle="round,pad=0,rounding_size=2", fc=color, ec="none"))
        p.text(lx + i * 80 + 16, ly, name, fontsize=F_LABEL, color=T["ink"], va="center")
    undeclared = (now["Gender"] == "Undeclared").sum()
    if undeclared:
        p.text(x + 16, y + h - 14, f"{undeclared} {'person' if undeclared == 1 else 'people'} with undeclared gender "
               "not shown (fewer than 5). White line = parity (50%).",
               fontsize=F_FOOT, color=T["ink_2"], va="center")

    # B - raw pay gap by entity vs Eurostat financial-sector benchmark
    gpg = d["gpg"]
    bench_year = int(gpg["Year"].max())
    ents = ["VMG Czech Republic s.r.o.", "VMG Deutschland GmbH", "VMG Luxembourg S.A.", "VMG UK Ltd"]
    ours = [kpi(d, "Pay Gap Mean %", e) for e in ents]
    bench = []
    for e in ents:
        b = gpg[(gpg["Geo"] == ENTITY_COUNTRY[e]) & (gpg["Activity"] == "Financial & insurance") & (gpg["Year"] == bench_year)]
        bench.append(float(b["Pay Gap %"].iloc[0]) if len(b) else np.nan)
    ratios = {e: o / b for e, o, b in zip(ents, ours, bench) if not np.isnan(o) and not np.isnan(b)}
    worst = max(ratios, key=ratios.get)
    times = "double" if 1.8 <= ratios[worst] < 2.3 else f"{ratios[worst]:.1f}x"
    x, y, w, h = p.card("B", f"{SHORT_ENTITY[worst]}'s raw gap is {times} its sector benchmark",
                        f"Raw gender pay gap (mean, FTE salary), {MONTH_LABEL} · tick = Eurostat {bench_year} financial sector")
    ax = p.axes(x + 104, y + 70, w - 104 - 30, h - 70 - 14)
    labels = [SHORT_ENTITY[e] for e in ents]
    colors = [T["accent"] if e == worst else T["context"] for e in ents]
    xmax = np.nanmax(ours + bench) * 1.18
    hbars(ax, labels, ours, colors, suppressed=[np.isnan(o) for o in ours], xmax=xmax)
    ypos = np.arange(len(ents))[::-1]
    for yp, b in zip(ypos, bench):
        if not np.isnan(b):
            ax.plot([b, b], [yp - 0.36, yp + 0.36], color=T["ink"], lw=2, zorder=4, solid_capstyle="butt")
            ax.text(b, yp + 0.4, f"{b:.1f}%", ha="center", va="bottom", fontsize=F_LABEL - 1, color=T["ink_2"])
    ax.tick_params(axis="y", labelsize=F_TICK + 0.5, colors=T["ink"])

    # C - like-for-like gap table (entity x grade), suppressed below 5 per gender
    pay = now[now["Pay Valid"]]
    tgrades = [g for g in range(1, 8) if any(
        not np.isnan(rk.pay_gap(pay[(pay["Legal Entity"] == e) & (pay["Grade"] == g)], "mean")) for e in ents)]
    rows, flagged, comparable = [], 0, 0
    for e in ents:
        cells = []
        for g in tgrades:
            grp = pay[(pay["Legal Entity"] == e) & (pay["Grade"] == g)]
            gap = rk.pay_gap(grp, "mean")
            cells.append(gap)
            if not np.isnan(gap):
                comparable += 1
                flagged += gap >= 5
        rows.append(cells)
    title = (f"All {comparable} comparable groups are under the 5% EU trigger" if flagged == 0 else
             f"{flagged} of {comparable} comparable groups {'exceeds' if flagged == 1 else 'exceed'} the 5% EU trigger: review")
    x, y, w, h = p.card("C", title, f"Like-for-like gap (mean) within legal entity and grade, %, {MONTH_LABEL}")
    col_w, row_h = (w - 32 - 110) / len(tgrades), 25
    tx, ty = x + 16, y + 74
    p.text(tx, ty, "Entity", fontsize=F_LABEL, color=T["ink_2"], va="center", fontweight="semibold")
    for j, g in enumerate(tgrades):
        p.text(tx + 110 + j * col_w + col_w / 2, ty, f"G{g}", fontsize=F_LABEL, color=T["ink_2"], ha="center",
               va="center", fontweight="semibold")
    p.base.plot([tx, x + w - 16], [ty + 12, ty + 12], color=T["grid"], lw=0.8)
    for i, (e, cells) in enumerate(zip(ents, rows)):
        ry = ty + 12 + row_h * (i + 0.5) + 2
        p.text(tx, ry, SHORT_ENTITY[e], fontsize=F_LABEL + 0.5, va="center")
        for j, v in enumerate(cells):
            cx = tx + 110 + j * col_w + col_w / 2
            if np.isnan(v):
                p.text(cx, ry, "—", fontsize=F_LABEL, color=T["ink_2"], ha="center", va="center")
            elif v >= 5:
                p.text(cx, ry, f"▲ {v:.1f}%", fontsize=F_LABEL, color=T["bad"], ha="center", va="center", fontweight="semibold")
            else:
                p.text(cx, ry, f"{v:.1f}%".replace("-", "−"), fontsize=F_LABEL, color=T["ink"], ha="center", va="center")
        p.base.plot([tx, x + w - 16], [ry + row_h / 2, ry + row_h / 2], color=T["grid"], lw=0.5)
    p.text(tx, y + h - 13, "— = fewer than 5 women or 5 men in the group. Negative = women paid more.",
           fontsize=F_FOOT, color=T["ink_2"], va="center")
    return p.save()


# ---------------------------------------------------------------------------
# Page 4 - Data Quality
# ---------------------------------------------------------------------------

def page_data_quality(d: dict) -> Path:
    raw, dq = d["raw"], d["dq"]
    p = Page("4_data_quality", "Data Quality")
    rules = pd.DataFrame([
        ("DQ01", "Duplicate row", "Medium", "Extra copy removed"),
        ("DQ02", "Missing manager", "Medium", "Kept; flagged to HR Services"),
        ("DQ03", "Manager not found", "Medium", "Kept; flagged to HR Services"),
        ("DQ04", "Future-dated record", "High", "Excluded until effective"),
        ("DQ05", "Location label not standard", "Low", "Standardised"),
        ("DQ06", "Non-ISO date format (file)", "Low", "Parsed as dd.MM.yyyy"),
        ("DQ07", "Currency ≠ legal entity", "High", "Excluded from pay metrics"),
        ("DQ08", "FTE outside 0–1", "High", "Excluded from FTE and pay"),
    ], columns=["Rule ID", "Rule", "Severity", "Action"])
    files = sorted(raw["File"].unique())
    excluded = len(raw) - len(d["snap"])
    tiles = [("K1", "Monthly files loaded", f"{len(files)}"), ("K2", "Rows loaded", f"{len(raw):,}"),
             ("K3", "Rule exceptions", f"{len(dq)}"), ("K4", "Rows excluded", f"{excluded}")]
    for sid, label, value in tiles:
        kpi_tile(p, sid, label, value, ("", T["ink_2"]), None)
    notes = {"K2": f"{len(raw) / len(files):.0f} rows per file on average", "K3": f"{dq['Rule ID'].nunique()} of 8 rules fired",
             "K4": "duplicates + future-dated", "K1": f"{pd.Period(files[0][:7]).strftime('%b %Y')} – {pd.Period(files[-1][:7]).strftime('%b %Y')}"}
    for sid, note in notes.items():
        x, y, w, h = p.slots[sid]
        p.text(x + 14, y + 86, note, fontsize=F_LABEL, color=T["ink_2"], va="center")

    # A - exceptions by rule
    by_rule = dq.groupby("Rule ID").size().reindex(rules["Rule ID"], fill_value=0)
    by_rule = by_rule.sort_values(ascending=False)
    names = [f"{rid} {rules.set_index('Rule ID').loc[rid, 'Rule']}" for rid in by_rule.index]
    top = rules.set_index("Rule ID").loc[by_rule.index[0], "Rule"]
    x, y, w, h = p.card("A", f"'{top}' is the most frequent issue", "Rule exceptions by rule, all files")
    ax = p.axes(x + 190, y + 68, w - 190 - 70, h - 68 - 8)
    hbars(ax, names, list(by_rule.values), [T["accent"]] + [T["context"]] * (len(names) - 1), fmt="{:.0f}")
    ax.tick_params(axis="y", labelsize=F_TICK - 0.5, colors=T["ink"])
    sev = rules.set_index("Rule ID")["Severity"]
    for yp, rid in zip(np.arange(len(names))[::-1], by_rule.index):
        ax.text(ax.get_xlim()[1] * 1.0, yp, sev[rid], va="center", ha="left", fontsize=F_LABEL - 1,
                color=T["bad"] if sev[rid] == "High" else T["ink_2"], clip_on=False)

    # B - exceptions by monthly file
    by_file = dq.groupby("File").size().reindex(files, fill_value=0)
    n_files = (by_file > 0).sum()
    x, y, w, h = p.card("B", f"{n_files} of {len(files)} monthly files had at least one issue", "Rule exceptions per monthly export")
    ax = p.axes(x + 36, y + 70, w - 36 - 20, h - 70 - 30)
    colors = [T["accent"] if v > 0 else T["context"] for v in by_file.values]
    ax.bar(range(len(files)), by_file.values, width=0.6, color=colors, zorder=2)
    for i, v in enumerate(by_file.values):
        if v:
            ax.text(i, v + 0.15, f"{v}", ha="center", va="bottom", fontsize=F_LABEL - 1, color=T["ink"])
    ticks = [i for i, f in enumerate(files) if f[5:7] in ("01", "07") or i == 0]
    ticks = [t for t in ticks if len(files) - 1 - t >= 3] + [len(files) - 1]
    ax.set_xticks(ticks, [pd.Period(files[i][:7]).strftime("%b %y") for i in ticks])
    ax.set_yticks([])
    ax.set_ylim(0, by_file.max() * 1.3)
    style_axis(ax, grid="none")
    ax.grid(False)
    ax.axhline(0, color=T["baseline"], lw=0.8)

    # C - exception detail
    detail = dq.merge(rules, on="Rule ID")
    detail["sev_order"] = detail["Severity"].map({"High": 0, "Medium": 1, "Low": 2})
    detail = detail.sort_values(["sev_order", "File", "Rule ID"])
    x, y, w, h = p.card("C", "Every exception has a documented action",
                        "Exception log, most severe first (full table in the Power BI report)")
    cols = [("Severity", 0, 70), ("Rule", 70, 230), ("File", 300, 110), ("Person ID", 410, 100), ("Action taken", 510, 300)]
    tx, ty = x + 16, y + 70
    for name, off, _ in cols:
        p.text(tx + off, ty, name, fontsize=F_LABEL, color=T["ink_2"], fontweight="semibold", va="center")
    p.base.plot([tx, x + w - 16], [ty + 10, ty + 10], color=T["grid"], lw=0.8)
    shown = 7
    for i, (_, r) in enumerate(detail.head(shown).iterrows()):
        ry = ty + 26 + i * 17.5
        sev_color = T["bad"] if r["Severity"] == "High" else T["ink"]
        vals = [r["Severity"], f"{r['Rule ID']} {r['Rule']}", r["File"], r["Person ID External"] or "(whole file)", r["Action"]]
        for (name, off, _), v in zip(cols, vals):
            p.text(tx + off, ry, v, fontsize=F_LABEL, color=sev_color if name == "Severity" else T["ink"], va="center")
    p.text(tx, y + h - 13, f"+ {len(detail) - shown} more exceptions", fontsize=F_FOOT, color=T["ink_2"], va="center")
    # second column: counts by severity
    sx = x + w - 260
    p.text(sx, ty, "By severity", fontsize=F_LABEL, color=T["ink_2"], fontweight="semibold", va="center")
    for i, sv in enumerate(["High", "Medium", "Low"]):
        n = (detail["Severity"] == sv).sum()
        p.text(sx, ty + 30 + i * 30, f"{n}", fontsize=18, fontweight="semibold",
               color=T["bad"] if sv == "High" else T["ink"], va="center")
        p.text(sx + 40, ty + 30 + i * 30, sv, fontsize=F_BODY, color=T["ink_2"], va="center")
    return p.save()


def main() -> None:
    apply()
    d = load()
    for fn in (page_board_summary, page_movement, page_diversity, page_data_quality):
        print("wrote", fn(d).relative_to(ROOT))


if __name__ == "__main__":
    main()

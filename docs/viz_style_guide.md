# People Reporting: Visualization Style Guide

*Vltava Market Group People Analytics · v1.0 · October 2026*

This guide says how every People report should look and why, so the Board sees the same visual language every time and any analyst can build a page that fits. It combines three published standards:

1. **A tested charting method.** Choose the chart from the data's job, give colour a job, and **test** the palette for colour blindness rather than eyeballing it.
2. **IBCS® SUCCESS rules** ([ibcs.com](https://ibcs.com/standards/), aligned with ISO 24896). This reporting standard is widely used in German-speaking finance and controlling. Its rules are Say, Unify, Condense, Check, Express, Simplify, Structure.
3. **Microsoft's Power BI accessibility guidance** ([Microsoft Learn](https://learn.microsoft.com/power-bi/create-reports/desktop-accessibility-creating-reports)): alt text, tab order, contrast and no colour-only meaning.

---

## 1. Five principles

| # | Principle | In practice |
|---|---|---|
| 1 | **Say the message** (IBCS *Say*) | The title is the finding ("Operations loses 1 in 5 people a year"), not the topic ("Turnover by division"). |
| 2 | **One accent, everything else grey** | Blue marks what matters; grey is context. If everything is coloured, nothing stands out. |
| 3 | **Same thing, same look** (IBCS *Unify*) | Actuals, last year and plan are always drawn the same way, on every page. |
| 4 | **Accessible by default** | Readable with colour blindness, in print, by keyboard and with a screen reader. |
| 5 | **Confidential by default** | No figure is ever shown for fewer than 5 people. |

## 2. Layout

- **Canvas:** 1280 × 720 (16:9) on an **8 px grid**, with **24 px** outer margins and **16 px** gutters.
- **Reading order** (Z-pattern): one **filter row** at the top → **KPI tiles** → the **main chart** (largest, top-left) → supporting detail.
- **At most about 6 visuals per page.** More than that is a second page or a drill-through.
- **Cards** are drawn in the page background image (`powerbi/backgrounds/`), so every page lines up exactly. Visuals are transparent and sit 4 px inside their card.
- **Positions:** exact values for every slot are in `powerbi/wireframes/layout.md`.

## 3. Choosing the chart

Decide this **before** colour. The data's job picks the form.

| The reader needs to… | Use | Not |
|---|---|---|
| See one headline number | **KPI tile**: value + change vs last year (+ a small trend line in static packs) | Gauge, one-bar chart |
| Compare categories | **Sorted bar**, one colour, the focus bar highlighted | Rainbow bars, pie |
| See a trend | **Line**, 2 px; one line highlighted, the others grey | Area stacks, markers on every point |
| Explain a change from A to B | **Waterfall** (headcount bridge) | Two separate cards |
| See a share across an ordered scale | **100% stacked bar** (gender by grade) | Donut |
| Compare against a benchmark | **Bar + benchmark marker**, or a dumbbell | Two y-axes |
| Look up exact values | **Table** with the same suppression rules | Tooltip-only |

**Never:** two y-axes (Power BI's *Line and clustered column* chart). Two scales on one chart invent a relationship that isn't in the data. Use two charts, or index both series to 100.
**Also never:** 3D, gauges, pies or donuts for comparing close values, or more than ~7 colours.

## 4. Colour

### Tokens (also in `powerbi/theme.json` and `src/viz_style.py`)

| Role | Hex | Use |
|---|---|---|
| **Accent** | `#2A78D6` | Actuals, the focus series or bar |
| **Context** | `#898781` | Last year, other bars and lines. *Marks only: never text.* |
| Series 2 | `#EB6834` | Second series when two series *are* the subject (e.g. Female / Male) |
| Series 3–4 | `#1BAF7A`, `#EDA100` | Only if unavoidable, and always with direct labels (see the check below) |
| Good / bad | `#0CA30C` / `#D03B3B` | **Only** on variances, always with ▲/▼ and a +/− sign |
| Good as text | `#006300` | Green text (7.5:1 contrast) |
| Sequential | `#CDE2FB` → `#0D366B` | Heatmaps: one hue, light = low |
| Text | `#0B0B0B` / `#52514E` | Titles and values / axis labels and subtitles |
| Grid | `#E1E0D9` | Solid 1 px hairlines, never dashed |
| Page / card | `#F9F9F7` / `#FFFFFF` | |

### Tested, not eyeballed

The palette was run through a colour-vision checker (`validate_palette.js`). It measures how far apart colours are under simulated protanopia and deuteranopia, which are red-green colour blindness and affect about 1 in 12 men. Results on the white card:

| Palette | Result |
|---|---|
| Accent + Series 2 (blue / orange) | **Pass on every check.** Colour-blind separation ΔE 24.7 (target ≥ 8), contrast ≥ 3:1 |
| First 4 series | Pass on separation, but **aqua (2.8:1) and yellow (2.2:1) fail the 3:1 contrast check**, so they need direct labels. That's why this guide prefers **small multiples** to a 4-colour chart. |
| Blue ordinal ramp (tenure bands) | Pass: lightness rises in order, one hue |

Text contrast (WCAG): primary 19.7:1 · secondary 7.9:1 · context grey 3.6:1 (**too low for text**, fine for marks) · accent blue 4.4:1 (**not for small text**: labels stay dark and sit outside bars).

### Rules

- **Colour follows the entity, never its rank.** Each legal entity always has the same colour. Set it explicitly under *Format → Colors*, so filtering never repaints the remaining bars.
- **Status colours mean good or bad and nothing else.** Whether "up" is good depends on the KPI: hires up is good, turnover up is bad.
- **No meaning by colour alone.** Every coloured variance also has an arrow and a sign, and every multi-series chart has a legend or direct labels.

## 5. Notation (IBCS *Unify*)

| Scenario | Look |
|---|---|
| **AC**: actual, current period | Solid accent blue |
| **PY**: same period last year | Solid context grey |
| **PL**: plan or target | Outline only (white fill, dark border) |
| **Variance** | ▲ +2.1 pp in green when good, ▼ −1.4 pp in red when bad |

- **Units:** a percentage is written `%`, a change in a percentage is written **pp** (percentage points). Turnover going from 12% to 14% is **+2 pp**, not +17%.

## 6. Type and numbers

- **Font:** Segoe UI everywhere. Titles 14 pt semibold, labels 10–11 pt, KPI values 28 pt semibold. No serif or display fonts, even for big numbers.
- **One format per KPI**, everywhere:

| KPI | Format | Example |
|---|---|---|
| Headcount | whole number with thousands separator | 248 |
| Rates | 1 decimal + % | 13.7% |
| Changes in rates | 1 decimal + pp | +1.2 pp |
| Money | € with K / M, 0–1 decimal | €78.4K |

- **Data labels:** selective only. Label the latest point, the extreme, or the bar the title talks about; never every point.

## 7. Titles, subtitles, footnotes

- **Title** = the message, written as a short sentence with numbers: *"Women thin out above grade G4"*.
- **Subtitle** = measure · unit · period · population: *"Share of women by pay grade, %, Sep 2026, internal staff"*.
- **Footnote** (a textbox, never baked into the image, so screen readers can read it) = source + definition: *"Source: monthly HRIS exports (synthetic). Turnover = leavers in last 12 months ÷ average headcount."*

## 8. Interaction

- **One filter row** at the top of every page (Division, Legal entity), applying to everything on it. No filters inside chart cards.
- **Titles are measures:** chart titles are computed from the data, so they stay true when a filter changes.
- **Definitions travel with the data:** every KPI measure carries its definition as a description (shown when hovering
  the field list), word for word from `docs/kpi_catalog.md`.
- **Tooltips enhance, never gate:** every value can also be read from a label or the table view.

## 9. Accessibility checklist (every page)

- [ ] Alt text on every non-decorative visual (*Format → General → Alt text*), stating the message, not "bar chart".
- [ ] Tab order set (*View → Selection → Tab order*); decorative shapes hidden from it.
- [ ] Title, label and axis text ≥ 4.5:1 contrast.
- [ ] Nothing meaningful conveyed by colour alone.
- [ ] Page still reads with **Windows colour filters → red-green** turned on.
- [ ] "Show as a table" works on every visual.

## 10. Confidentiality

- **Minimum group size 5.** Any rate, average, pay figure or diversity share based on fewer than 5 people shows **"—"**, and its tooltip says *"Hidden: fewer than 5 people"*. Counts like headcount are shown.
- **Row-level security:** an HR Business Partner sees only their own division.
- **No names in the model.** They are removed in Power Query (data minimisation).

## 11. Review checklist (used in design reviews)

A page is not done until it passes all of these:

1. Does every title state a message, with a number?
2. Is there one accent colour, with everything else grey or neutral?
3. Any two-axis chart, pie with more than 6 slices, gauge or 3D? (→ fix)
4. Are the same KPI's format and colours identical on every page?
5. Do bars side by side use the same scale?
6. Are labels selective, never one on every point?
7. Do the gridlines recede (light, solid, or none)?
8. Does any value rely on a tooltip alone?
9. Does any group under 5 people show a value?
10. Alt text, tab order and contrast: done?

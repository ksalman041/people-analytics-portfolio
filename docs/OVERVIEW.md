# Portfolio overview: what each demo is, and how to talk about it

*About 15 minutes to read. Everything uses **Vltava Market Group**, a fictional ~240-person market-infrastructure group
(Frankfurt, Prague, Luxembourg, London). People are synthetic; Eurostat and ECB figures are real.*

---

## D1 · Refresh, don't rebuild (automation and data quality)
**What it shows:** a monthly HR report that used to be rebuilt by hand now refreshes itself: 25 monthly HRIS exports
in a folder, cleaned by documented rules, feeding one model.

**How it works**
- 25 CSV exports shaped like SAP SuccessFactors *Job Information* reports (Sep 2024 – Sep 2026, ~240 rows each).
- Power Query reads the whole folder, so a new month = drop the file in, press Refresh.
- 8 data-quality rules (duplicates, missing manager, future-dated records, wrong currency…). Each has a severity and a documented action.
- 19 errors were planted on purpose with an answer key; the rules find all 19 and nothing else.

**What to say**
1. "Adding October is one file and one click. The pages, titles included, move to October."
2. "Nothing is fixed silently: every exception is listed on the Data Quality page with what was done about it."
3. "Names are removed in the first step. No KPI needs them (GDPR data minimisation)."

---

## D2 · Board Pack in Power BI
**What it shows:** a four-page executive report: Board Summary, Movement & Attrition, Diversity & Pay, Data Quality.

**How it works**
- Star schema (snapshot + movements facts, date / division / entity dimensions), 91 DAX measures.
- **Chart titles are measures**: "Operations loses more than 1 in 5 people a year" is computed, so it can't go stale.
- Pay-gap page benchmarks each entity against **real Eurostat** financial-sector figures; like-for-like gaps are tested against the EU Pay Transparency Directive's 5% trigger.
- Row-level security role (*HRBP - Operations*) and a rule that hides any figure based on fewer than 5 people.

**What to say**
1. "Turnover is 14.0%, up 2.7 points on last year, driven by Operations, where 7 in 10 leavers quit in their first year. That points to onboarding, not pay."
2. "The raw gender pay gap is 19.6% but only 3.2% like-for-like: mostly fewer women in senior grades. Luxembourg is the outlier at double its sector benchmark."
3. "Every number is tested: an independent Python calculation matches Power BI on 240 out of 240 values."

---

## Visualization style guide
**What it shows:** the rules behind every page, written down so any analyst can build a page that fits (`docs/viz_style_guide.md`).

**How it works**
- Combines a tested charting method, **IBCS** reporting rules (common in German finance) and Microsoft's accessibility guidance.
- One accent colour, everything else grey; titles state the message; no two-axis charts, gauges or 3D.
- Palette **measured** for colour blindness (not eyeballed); text contrast ≥ 4.5:1; alt text on every chart.

**What to say**
1. "The posting asks to *establish best practices for data visualization*. This is what that looks like as a document."
2. "Colour has one job per chart. If everything is coloured, nothing stands out."
3. "I check palettes with a colour-vision simulator: about 1 in 12 men can't tell some reds and greens apart."

---

## D3 · Reorg in a box
**What it shows:** how a quarterly reorganisation is prepared and checked before go-live. Example: Market Data moves into
Technology, and two Technology departments merge (1 July 2026).

**How it works**
- HRBPs fill in an **Excel mapping template** (drop-downs, XLOOKUP/COUNTIF checks) that flags problems as they type.
- `reorg_validate.py` re-runs the 6 blocking checks and adds design checks: spans of control and management layers.
- The first submission fails on all 6 planted issues; the corrected one passes, and the July HRIS export matches it for **97 of 97** people.

**What to say**
1. "The first mapping would have dropped 15 people out of reporting: one unit simply wasn't in the file."
2. "The merge quietly adds a management layer for IT Infrastructure (5 → 6). That's a design question for the business, not a data error, so it's reported separately."
3. "Before and after headcount must reconcile, and the check fails if it doesn't."

---

## D4 · Ticket #4711 and the KPI catalog
**What it shows:** a real-world support ticket. An HRBP counts 50 people in Operations; the dashboard says 47.

**How it works**
- DuckDB SQL reproduces both numbers, anti-joins the two lists in both directions, and classifies every difference.
- Three causes: a contractor (not headcount), a transfer effective 1 Oct (after the cut-off), a hire starting 15 Oct (future-dated). **47 + 3 = 50.**
- The fix is a definition, not a number: `docs/kpi_catalog.md` defines every KPI once and links it to its Power BI measure.

**What to say**
1. "Both numbers were right; they answered different questions. My job was to show exactly how they connect."
2. "Reproduce both numbers first, then anti-join both ways, classify every difference, make it add up."
3. "Most 'wrong number' tickets are definition differences: cut-off dates, contractors, future-dated records."

---

## How it's all tested
| Check | Result |
|---|---|
| Data-quality rules vs planted errors | 19 of 19 found, no false alarms |
| Headcount bridge (opening + hires − leavers ± transfers = closing) | closes every month, every division |
| Power BI measures vs independent pandas calculation | 240 of 240 values match |
| Reorg mapping v1 vs answer key · v2 vs HRIS | 6 of 6 issues · 97 of 97 people |
| Ticket reconciliation | 47 + 3 = 50, nothing unexplained |
| Excel template, calculated by Excel | all checks fire, 0 formula errors |

---

## 5-minute demo script
| Time | Show | Say |
|---|---|---|
| 0:00 | Board Summary | "A monthly people report for a fictional market operator. One page tells the Board what changed: turnover is up, Operations is the hotspot, growth is all in Prague." |
| 0:45 | Hover a chart title | "Titles are measures, so they always describe the data on screen." |
| 1:15 | Movement & Attrition | "The bridge from 229 to 239 people. Seven in ten Operations leavers quit in year one, and first-year turnover is 5× the rate after that. That's an onboarding problem." |
| 2:00 | Diversity & Pay | "Raw gap 19.6%, like-for-like 3.2%. Luxembourg is double its Eurostat sector benchmark, and one group in Frankfurt is above the 5% Directive trigger." |
| 2:45 | Data Quality | "19 issues across 25 files, each with an action. Then the demo: drop the October file, Refresh, and every page moves to October." |
| 3:30 | Reorg memo | "Before a reorg goes live I validate the mapping. The first version would have lost 15 people; the merge adds a management layer." |
| 4:15 | Ticket case | "50 vs 47: a contractor, a transfer after cut-off, a future hire. Both numbers right, different questions." |
| 4:45 | Style guide | "And the rules behind all of it, written down so the team can reuse them." |

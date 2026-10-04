# People KPI catalog

*Vltava Market Group People Analytics · v1.0 · October 2026 · synthetic data*

One definition per KPI, used everywhere: the Power BI report, the board memo, ad-hoc answers. Each entry names the
exact DAX measure (`_Measures` table in `powerbi/Board_Pack.pbip`) and the independent check in `src/reference_kpis.py`.

## General rules (apply to every KPI)
| Rule | Definition |
|---|---|
| **As-of date** | Every stock figure is measured at **month-end** (the export's file month). Records effective after that date are excluded (rule DQ04). |
| **Population** | **Employees** = status *Active* and class *Permanent* or *Fixed-Term*. **External** contractors are never headcount. |
| **Rolling 12 months (R12)** | The 12 months up to and including the selected month. Needs 12 full months of movements; earlier months show blank. |
| **Comparison** | "vs last year" = the same month 12 months earlier. Changes in rates are shown in **percentage points (pp)**. |
| **Confidentiality** | Rates, averages, pay and diversity figures are **hidden when based on fewer than 5 people** (shown as "—"). |
| **Pay** | Full-time-equivalent base salary (annual salary ÷ FTE), converted to EUR at the **ECB monthly average rate**; the latest published rate is used when the month isn't published yet. |
| **Refresh** | Monthly, after the HRIS month-end export lands in `data/exports/`. Owner: People Analytics. Data owner: HR Services (HRIS). |

---

## Workforce
### Headcount
| | |
|---|---|
| **Definition** | Number of employees on the last day of the month. |
| **Formula** | count of people with status Active, class ≠ External, effective date ≤ month-end |
| **DAX** | `[Headcount]` · last year: `[Headcount PY]` |
| **Grain** | Person × month-end (`Snapshot`) |
| **Caveats** | A part-timer counts as 1 (see FTE). Lists pulled from the HRIS on another day, or including contractors / future-dated records, will differ: see Ticket #4711. |

### FTE
| | |
|---|---|
| **Definition** | Contracted capacity in full-time equivalents on the last day of the month. |
| **Formula** | sum of FTE over headcount; FTE outside 0–1 is treated as missing (DQ08) |
| **DAX** | `[FTE]` |

## Movement
### Hires · Leavers (12 months)
| | |
|---|---|
| **Definition** | Employees who joined / left during the last 12 months. |
| **Formula** | Found by comparing consecutive month-end snapshots: in this month and not the last = hire; the reverse = leaver. |
| **DAX** | `[Hires R12]`, `[Leavers R12]` |
| **Caveats** | Someone who joins and leaves within the same month is not counted (never in a month-end snapshot). Internal transfers are not hires or leavers. |

### Turnover rate (rolling 12 months)
| | |
|---|---|
| **Definition** | Share of the workforce that left over the last 12 months. |
| **Formula** | leavers in the last 12 months ÷ **average** of the 12 month-end headcounts |
| **DAX** | `[Turnover R12 %]` · last year: `[Turnover R12 % PY]` |
| **Why the average** | Dividing by the closing headcount makes a growing team look better and a shrinking team look worse. |
| **Caveats** | Hidden when the average headcount is under 5. Small teams swing a lot: read with the leaver count. |

### Voluntary turnover rate
| | |
|---|---|
| **Definition** | As turnover, counting only resignations. |
| **Formula** | voluntary leavers (R12) ÷ average headcount (R12) |
| **DAX** | `[Voluntary Turnover R12 %]` |
| **Mapping** | Leaver category comes from `data/reference/termination_reasons.csv`: resignations = voluntary; dismissal, redundancy, end of fixed term = involuntary; retirement separate. |

### Early leavers
| | |
|---|---|
| **Definition** | Share of leavers who left within 12 months of joining. |
| **Formula** | leavers (R12) with tenure at exit < 12 months ÷ all leavers (R12) |
| **DAX** | `[Early Leavers R12 %]` |
| **Caveats** | Hidden when there are fewer than 5 leavers. A high value points to hiring or onboarding, not pay. |

### Headcount bridge
| | |
|---|---|
| **Definition** | How headcount moved from a year ago to today. |
| **Formula** | opening + hires − leavers + transfers in − transfers out = closing (always closes; tested) |
| **DAX** | `[Bridge Value]` by `BridgeSteps[Step]` |

## Diversity and pay
### Women · Women in leadership
| | |
|---|---|
| **Definition** | Share of women among employees; among leadership (grades G6–G7). |
| **Formula** | women ÷ headcount (all declared and undeclared genders in the denominator) |
| **DAX** | `[Women %]`, `[Women in Leadership %]` |
| **Caveats** | Leadership is 18 people, so one appointment moves it by about 5–6 pp. |

### Gender pay gap, raw (mean and median)
| | |
|---|---|
| **Definition** | How much less women earn than men on average, as a share of men's pay (EU Pay Transparency Directive definition). |
| **Formula** | (men's mean FTE salary − women's mean FTE salary) ÷ men's mean; median version uses medians |
| **DAX** | `[Pay Gap Mean %]`, `[Pay Gap Median %]` |
| **Caveats** | Reflects *who is in which roles* as much as pay. Needs ≥ 5 women and ≥ 5 men. Pooling countries mixes cost-of-living differences: read by legal entity. |

### Gender pay gap, like-for-like
| | |
|---|---|
| **Definition** | The gap between women and men in comparable roles. |
| **Formula** | mean gap inside each *legal entity × pay grade* group, weighted by group size; groups with < 5 women or < 5 men are left out |
| **DAX** | `[Pay Gap Like-for-like %]` (company), `[Like-for-like Cell]` (per group) |
| **Threshold** | A gap of **5% or more** in a group of comparable workers that objective criteria can't explain triggers a *joint pay assessment* under the Directive. |

### Sector benchmark
| | |
|---|---|
| **Definition** | Raw gender pay gap in each entity's country, financial & insurance sector. |
| **Source** | Eurostat `earn_gr_gpgr2`, latest year (2024, provisional), fetched by `src/fetch_external.py`. |
| **DAX** | `[Sector Benchmark %]` |
| **Caveats** | National sector figure (all employers, Structure of Earnings Survey method); a direction-finder, not a like-for-like comparison. No figure for the UK. |

## Data quality
### Rule exceptions · Rows excluded
| | |
|---|---|
| **Definition** | Data-quality rule hits across all monthly files; rows dropped before reporting. |
| **Rules** | DQ01 duplicate · DQ02 missing manager · DQ03 manager not found · DQ04 future-dated · DQ05 non-standard location · DQ06 non-ISO dates · DQ07 currency mismatch · DQ08 FTE out of range |
| **DAX** | `[Rule Exceptions]`, `[Rows Excluded]` |
| **Action** | Every rule has a documented action (`DQ_Rules[Action Taken]`): removed, excluded, standardised or flagged to HR Services. |

## How the definitions are tested
- `src/reference_kpis.py` re-computes every KPI in pandas from the raw exports.
- `src/check_powerbi_numbers.ps1` + `src/compare_powerbi.py` read the same KPIs out of Power BI: **240 of 240 values match**
  (8 KPIs × company, 5 divisions and 4 legal entities × 3 month-ends).

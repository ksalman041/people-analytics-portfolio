# Ticket #4711: "My Operations list says 50, the dashboard says 47"

*Vltava Market Group People Analytics · synthetic data · investigation: `sql/ticket_4711.sql`, run with `python src/run_ticket.py`*

## The ticket
> **From:** HR Business Partner, Operations · **Opened:** Fri 2 Oct 2026, 09:12
> I pulled my team list from SuccessFactors this morning and count **50** people in Operations. The People
> dashboard shows **47** for September. Leadership meets on Monday and I need to know which number is right.

## Answer in one line
**Both numbers are correct; they answer different questions.** The dashboard counts *employees on 30 September*;
the HRBP's list counts *everyone linked to Operations in the HRIS on 2 October*, including a contractor and two
records that only take effect in October. **47 + 1 + 1 + 1 = 50.**

## How it was investigated

**1. Reproduce both numbers first.** Never debug a number you can't reproduce.

| Dashboard, Operations, 30 Sep 2026 | HRBP list, pulled 2 Oct 2026 |
|---|---|
| 47 | 50 |

The dashboard rule in SQL is exactly the Power BI definition: *active, not external, effective on or before the cut-off*.
```sql
SELECT DISTINCT "Person ID External" AS person_id, "Division" AS division, "Department" AS department
FROM read_csv('data/exports/2026-09.csv', all_varchar = true)
WHERE "Employee Status" = 'Active'
  AND "Employee Class" <> 'External'
  AND CAST("Event Date" AS DATE) <= DATE '2026-09-30';
```

**2. Find the people on one list but not the other (anti-join, both directions).**
```sql
SELECT h.* FROM hrbp h
WHERE NOT EXISTS (SELECT 1 FROM sep_headcount s
                  WHERE s.person_id = h."Person ID External" AND s.division = 'Operations');
```
| Person | Department | Class | Latest event | Effective |
|---|---|---|---|---|
| 100013 | Client Services | Permanent | Transfer | 2026-10-01 |
| 100226 | Settlement Operations | **External** | Hire | 2024-03-25 |
| 100311 | Settlement Operations | Permanent | Hire | **2026-10-15** |

The other direction (in the dashboard but not on the list) is empty, so the difference is exactly these three people.

**3. Look at what the September export says about each of them.** Person 100013 appears **twice** in the export:
the current record (Markets, Trading Services) and a pre-entered transfer to Operations dated 1 October. That
second row is a *future-dated record*; data-quality rule **DQ04** flags it and the dashboard leaves it out.

**4. Classify every difference and close the gap.**

| | People |
|---|---|
| Dashboard, Operations, 30 Sep 2026 | **47** |
| + Scope: external contractor (not an employee, never in headcount) | 1 |
| + Cut-off: transfer into Operations effective 1 Oct, after 30 Sep | 1 |
| + Future-dated: hire starting 15 Oct, after the list was pulled | 1 |
| **= HRBP list, pulled 2 Oct 2026** | **50** |

`run_ticket.py` fails if any difference is unexplained or the lines don't add up, so the reconciliation is tested, not eyeballed.

## Root causes
| Cause | Why the dashboard excludes it | Where it is defined |
|---|---|---|
| Contractor counted | Headcount = employees; contractors are tracked separately | KPI catalog → Headcount |
| Different cut-off date | Monthly reporting is "as of month-end"; 1 Oct belongs to October | KPI catalog → general rules |
| Future-dated hire | A record is only true from its effective date | DQ04, KPI catalog → Headcount |

## Reply sent to the HRBP
> Hi, both numbers are right, they just count different things:
> - **47** is the official headcount for **30 September**: employees only, as of month-end. Use this one on Monday.
> - Your **50** adds one external contractor in Settlement Operations, one person transferring in from Trading
>   Services on **1 October**, and one new joiner starting on **15 October**.
>
> The October dashboard (after the next refresh) will show 49 + any other October changes: the transfer and the
> new joiner will be in, the contractor still won't. For lists that match the dashboard, use the saved report
> "Headcount – official (month-end)" in SuccessFactors.

## What we changed so it doesn't happen again
1. **The as-of date is in every page subtitle** ("September 2026"), so nobody compares a month-end figure with a list pulled days later.
2. **One definition, written down:** `docs/kpi_catalog.md` → Headcount, shared with the HRBP community.
3. **Future-dated records are visible:** the Data Quality page lists DQ04 hits, so pre-entered changes don't surprise anyone.
4. **A saved SuccessFactors report** with the dashboard's filters, so self-service lists match by construction.

*Time to resolution: same morning. The useful habit: reproduce both numbers, anti-join both ways, classify every difference, make the reconciliation add up.*

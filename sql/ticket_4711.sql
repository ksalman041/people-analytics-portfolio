-- Ticket #4711 (opened 2 Oct 2026 by the HR Business Partner for Operations)
-- "My Operations list has 50 people. The People dashboard says 47 for September. Which one is right?"
--
-- DuckDB reads the CSV files directly; run everything with:  python src/run_ticket.py
-- Each block starts with "-- name:" so the runner can show its result.

-- name: setup
-- The September export exactly as the HRIS delivered it (everything as text, like Power Query sees it),
-- and the dashboard's headcount definition: active, not external, effective on or before 30 Sep 2026.
CREATE OR REPLACE VIEW sep_raw AS
SELECT * FROM read_csv('data/exports/2026-09.csv', all_varchar = true, header = true);

CREATE OR REPLACE VIEW sep_headcount AS
SELECT DISTINCT
    "Person ID External" AS person_id,
    "Division"           AS division,
    "Department"         AS department
FROM sep_raw
WHERE "Employee Status" = 'Active'
  AND "Employee Class" <> 'External'
  AND CAST("Event Date" AS DATE) <= DATE '2026-09-30';

CREATE OR REPLACE VIEW hrbp AS
SELECT * FROM read_csv('data/ticket/hrbp_operations_list_2026-10-02.csv', all_varchar = true, header = true);

-- name: 1. Reproduce both numbers
SELECT
    (SELECT count(*) FROM sep_headcount WHERE division = 'Operations') AS dashboard_sep_2026,
    (SELECT count(*) FROM hrbp)                                         AS hrbp_list_2_oct;

-- name: 2. On the HRBP list but not in the dashboard (anti-join)
SELECT h."Person ID External" AS person_id, h."Department", h."Employee Class", h."Event", h."Event Date"
FROM hrbp h
WHERE NOT EXISTS (
    SELECT 1 FROM sep_headcount s
    WHERE s.person_id = h."Person ID External" AND s.division = 'Operations')
ORDER BY person_id;

-- name: 3. In the dashboard but not on the HRBP list (the other direction)
SELECT s.person_id, s.department
FROM sep_headcount s
WHERE s.division = 'Operations'
  AND s.person_id NOT IN (SELECT "Person ID External" FROM hrbp);

-- name: 4. Why: what the September export says about each difference
SELECT r."Person ID External" AS person_id, r."Division", r."Department", r."Employee Class",
       r."Event", r."Event Date", r."Employee Status"
FROM sep_raw r
WHERE r."Person ID External" IN (
    SELECT h."Person ID External" FROM hrbp h
    WHERE NOT EXISTS (SELECT 1 FROM sep_headcount s
                      WHERE s.person_id = h."Person ID External" AND s.division = 'Operations'))
ORDER BY person_id, r."Event Date";

-- name: 5. Reconciliation: classify every difference and close the gap
WITH differences AS (
    SELECT h.*
    FROM hrbp h
    WHERE NOT EXISTS (SELECT 1 FROM sep_headcount s
                      WHERE s.person_id = h."Person ID External" AND s.division = 'Operations')
),
classified AS (
    SELECT
        "Person ID External" AS person_id,
        CASE
            WHEN "Employee Class" = 'External'
                THEN 'Scope: external contractor - not an employee, never in headcount'
            WHEN "Event" = 'Hire' AND CAST("Event Date" AS DATE) > DATE '2026-10-02'
                THEN 'Future-dated: hire starts ' || "Event Date" || ', after the list was pulled'
            WHEN CAST("Event Date" AS DATE) > DATE '2026-09-30'
                THEN 'Cut-off: ' || lower("Event") || ' into Operations effective ' || "Event Date" || ', after 30 Sep'
            ELSE 'UNEXPLAINED'
        END AS reason
    FROM differences
)
SELECT 'Dashboard, Operations, 30 Sep 2026' AS line, (SELECT count(*) FROM sep_headcount WHERE division = 'Operations') AS people
UNION ALL
SELECT '+ ' || reason, count(*) FROM classified GROUP BY reason
UNION ALL
SELECT '= HRBP list, pulled 2 Oct 2026', (SELECT count(*) FROM hrbp);

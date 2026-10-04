# Data governance and confidentiality

*How this portfolio handles people data, and how the same choices would apply to a real HR reporting team.*

| Principle | What it means here |
|---|---|
| **Synthetic data only** | Every person is generated (`src/make_exports.py`). Only Eurostat and ECB figures are real, and they are public. |
| **Data minimisation** (GDPR Art. 5) | Names are dropped in the first Power Query step and never reach the model. Analysis uses pseudonymous person IDs. |
| **Minimum group size: 5** | Rates, averages, pay and diversity figures are hidden for groups under 5 people, so no individual can be singled out. |
| **Least privilege** | Row-level security: the *HRBP - Operations* role sees Operations only. Real deployments map each HRBP to their division. |
| **Documented data quality** | Eight rules run on every refresh; each has a severity and a documented action. Nothing is fixed silently. |
| **One definition per KPI** | `docs/kpi_catalog.md` is the reference for the report, memos and ad-hoc answers. |
| **Tested numbers** | Power BI results are compared with an independent pandas implementation (240/240 match); the headcount bridge and reorg headcount must reconcile. |
| **No individual risk scores** | No "flight risk" predictions about named people. The EU AI Act treats AI used for employment decisions as high-risk, and aggregate drivers (e.g. early leavers by division) answer the business question. |
| **Change control** | The report is generated from code (`src/make_powerbi.py`) and versioned in Git; every change is reviewable. |

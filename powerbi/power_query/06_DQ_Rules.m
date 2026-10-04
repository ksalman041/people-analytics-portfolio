// DQ_Rules - the rule catalogue: what each rule checks, how serious it is, what we do about it.
// A dimension for the Data Quality page. Writing the action down is the governance part:
// every exception has an owner and an outcome, nothing is silently "fixed".
let
    Rules = #table(
        type table [#"Rule ID" = text, #"Rule" = text, #"Severity" = text, #"Action Taken" = text],
        {
            {"DQ01", "Duplicate row", "Medium", "Extra copy removed"},
            {"DQ02", "Missing manager", "Medium", "Kept; flagged to HR Services"},
            {"DQ03", "Manager not found", "Medium", "Kept; flagged to HR Services"},
            {"DQ04", "Future-dated record", "High", "Excluded until effective"},
            {"DQ05", "Non-standard location", "Low", "Standardised"},
            {"DQ06", "Non-ISO dates (file)", "Low", "Parsed as dd.MM.yyyy"},
            {"DQ07", "Currency mismatch", "High", "Excluded from pay metrics"},
            {"DQ08", "FTE out of range", "High", "Excluded from FTE and pay metrics"}
        }
    ),
    AddLabel = Table.AddColumn(Rules, "Rule Label", each [Rule ID] & " " & [Rule], type text),
    // Sort key so tables list High before Medium before Low
    AddOrder = Table.AddColumn(AddLabel, "Severity Order", each
        if [Severity] = "High" then 1 else if [Severity] = "Medium" then 2 else 3, Int64.Type)
in
    AddOrder

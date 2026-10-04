// DimDate - one row per month-end. Every fact table joins to it, so one Month slicer
// filters headcount, movements and data-quality exceptions at the same time.
// Mark it as a date table: Table tools > Mark as date table > Month End.
let
    Start = List.Min(Snapshot[As Of]),
    End = List.Max(Snapshot[As Of]),
    Months = List.Generate(() => Start, each _ <= End, each Date.EndOfMonth(Date.AddMonths(_, 1))),
    AsTable = Table.FromList(Months, Splitter.SplitByNothing(), {"Month End"}),
    Typed = Table.TransformColumnTypes(AsTable, {{"Month End", type date}}),
    AddMonth = Table.AddColumn(Typed, "Month", each Date.ToText([Month End], [Format = "MMM yyyy", Culture = "en-US"]), type text),
    AddYear = Table.AddColumn(AddMonth, "Year", each Date.Year([Month End]), Int64.Type),
    AddQuarter = Table.AddColumn(AddYear, "Quarter", each
        "Q" & Text.From(Date.QuarterOfYear([Month End])) & " " & Text.From(Date.Year([Month End])), type text),
    AddQuarterSort = Table.AddColumn(AddQuarter, "Quarter Sort", each
        Date.Year([Month End]) * 10 + Date.QuarterOfYear([Month End]), Int64.Type),
    // Month Index (1, 2, 3 ...) makes "the 12 months up to this one" easy in DAX
    AddIndex = Table.AddIndexColumn(AddQuarterSort, "Month Index", 1, 1, Int64.Type)
in
    AddIndex

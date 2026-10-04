// Exports_Raw - every monthly export in the folder, stacked into one table, untouched.
// This is the automation: drop next month's file into data\exports, press Refresh, done.
// Everything stays as text here on purpose - the data-quality rules need to see the raw values.
// Staging only: uncheck "Enable load".
let
    ExportColumns = {
        "Person ID External", "First Name", "Last Name", "Gender", "Employee Status",
        "Employee Class", "Hire Date", "Event", "Event Reason", "Event Date",
        "Regret Termination", "Division", "Department", "Cost Center", "Legal Entity",
        "Location", "Job Title", "Pay Grade", "FTE", "Manager ID", "Annual Salary", "Currency"
    },
    Source = Folder.Files(ProjectFolder & "\data\exports"),
    // Only month files named like 2025-07.csv (11 characters)
    MonthFiles = Table.SelectRows(Source, each [Extension] = ".csv" and Text.Length([Name]) = 11),
    // The file name says which month-end the snapshot describes
    AddAsOf = Table.AddColumn(MonthFiles, "As Of", each Date.EndOfMonth(#date(
        Number.FromText(Text.Start([Name], 4)), Number.FromText(Text.Middle([Name], 5, 2)), 1)), type date),
    // Encoding 65001 = UTF-8, so Czech names like "Čermáková" survive
    AddData = Table.AddColumn(AddAsOf, "Data", each Table.PromoteHeaders(
        Csv.Document([Content], [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
        [PromoteAllScalars = true])),
    KeepCols = Table.SelectColumns(AddData, {"Name", "As Of", "Data"}),
    Expanded = Table.ExpandTableColumn(KeepCols, "Data", ExportColumns),
    Renamed = Table.RenameColumns(Expanded, {{"Name", "File"}}),
    Sorted = Table.Sort(Renamed, {{"File", Order.Ascending}}),
    WithRowId = Table.AddIndexColumn(Sorted, "Row ID", 1, 1, Int64.Type)
in
    WithRowId

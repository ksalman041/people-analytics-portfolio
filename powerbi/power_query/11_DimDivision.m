// DimDivision - one row per division. Row-level security sits on this table, so an HR
// Business Partner who may only see "Operations" sees only Operations in every fact table.
let
    Source = Table.Distinct(Table.SelectColumns(Snapshot, {"Division"})),
    Sorted = Table.Sort(Source, {{"Division", Order.Ascending}})
in
    Sorted

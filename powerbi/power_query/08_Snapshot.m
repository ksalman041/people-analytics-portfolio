// Snapshot - the clean fact table: one row per person per month-end.
// Every cleaning decision is a named step, so anyone can click through Applied Steps
// and see exactly what happened to the data. Expected: 5,855 rows; 248 headcount in Sep 2026.
let
    Raw = Exports_Raw,

    // 1. Remove exact duplicate rows (rule DQ01)
    DataCols = List.RemoveItems(Table.ColumnNames(Raw), {"Row ID"}),
    Deduped = Table.Distinct(Table.SelectColumns(Raw, DataCols)),

    // 2. Data minimisation (GDPR): no KPI needs names, so they never enter the model
    NoNames = Table.RemoveColumns(Deduped, {"First Name", "Last Name"}),

    // 3. Trim stray spaces everywhere and standardise location labels (DQ05)
    TextCols = List.RemoveItems(Table.ColumnNames(NoNames), {"As Of"}),
    Trimmed = Table.TransformColumns(NoNames, List.Transform(TextCols, each {_, Text.Trim, type text})),
    Located = Table.ReplaceValue(Trimmed, "Praha", "Prague", Replacer.ReplaceValue, {"Location"}),

    // 4. Parse dates in either format (DQ06), then drop records that are not effective yet (DQ04)
    Dated = Table.TransformColumns(Located, {
        {"Hire Date", fnParseDate, type date}, {"Event Date", fnParseDate, type date}
    }),
    Effective = Table.SelectRows(Dated, each [Event Date] <= [As Of]),

    // 5. Numbers - always parse with "en-US" so "0.8" works on a Czech or German PC.
    //    An FTE outside 0-1 is unusable (DQ08): blank it so it can't distort FTE or pay.
    Numbers = Table.TransformColumns(Effective, {
        {"FTE", each let v = if _ = "" then null else Number.FromText(_, "en-US")
                     in if v <> null and v > 0 and v <= 1 then v else null, type nullable number},
        {"Annual Salary", each if _ = "" then null else Number.FromText(_, "en-US"), type nullable number}
    }),

    // 6. Flags the measures rely on
    AddHC = Table.AddColumn(Numbers, "Is Headcount", each
        [Employee Status] = "Active" and [Employee Class] <> "External", type logical),
    AddGrade = Table.AddColumn(AddHC, "Grade", each
        if [Pay Grade] = "" then null else Number.FromText(Text.AfterDelimiter([Pay Grade], "G")), Int64.Type),
    AddLeader = Table.AddColumn(AddGrade, "Is Leadership", each [Grade] <> null and [Grade] >= 6, type logical),
    AddTenure = Table.AddColumn(AddLeader, "Tenure Months", each
        Number.Round(Duration.Days([As Of] - [Hire Date]) / 30.4375, 1), type number),
    AddBand = Table.AddColumn(AddTenure, "Tenure Band", each
        if [Tenure Months] < 12 then "< 1 year" else if [Tenure Months] < 24 then "1–2 years"
        else if [Tenure Months] < 60 then "2–5 years" else "5+ years", type text),

    // 7. Full-time-equivalent salary in EUR, for pay-gap reporting:
    //    look up the entity's own currency and the ECB rate for that month
    WithEntity = Table.NestedJoin(AddBand, {"Legal Entity"}, LegalEntities, {"Legal Entity"}, "Entity", JoinKind.LeftOuter),
    WithEntityCcy = Table.ExpandTableColumn(WithEntity, "Entity", {"Currency"}, {"Entity Currency"}),
    AddMonthKey = Table.AddColumn(WithEntityCcy, "Month Key", each
        Date.ToText([As Of], [Format = "yyyy-MM", Culture = "en-US"]), type text),
    WithFx = Table.NestedJoin(AddMonthKey, {"Month Key", "Currency"}, FX, {"Month", "Currency"}, "Fx", JoinKind.LeftOuter),
    WithRate = Table.ExpandTableColumn(WithFx, "Fx", {"Units per EUR"}),
    // The ECB publishes a month's average only after the month ends, so the newest export
    // may have no rate yet: fall back to the latest rate we have for that currency.
    LatestFx = Table.Group(FX, {"Currency"}, {{"Latest Rate", each
        List.Last(Table.Sort(_, {{"Month", Order.Ascending}})[Units per EUR]), type number}}),
    WithLatest = Table.NestedJoin(WithRate, {"Currency"}, LatestFx, {"Currency"}, "Latest", JoinKind.LeftOuter),
    LatestCol = Table.ExpandTableColumn(WithLatest, "Latest", {"Latest Rate"}),
    AddRate = Table.AddColumn(LatestCol, "Rate Used", each
        if [Units per EUR] <> null then [Units per EUR] else [Latest Rate], type nullable number),
    // Pay is usable only for internal staff with a valid FTE and the right currency (DQ07)
    AddPayValid = Table.AddColumn(AddRate, "Pay Valid", each
        [Is Headcount] and [Annual Salary] <> null and [FTE] <> null and [Currency] = [Entity Currency], type logical),
    AddEur = Table.AddColumn(AddPayValid, "Salary FTE EUR", each
        if [Pay Valid] then [Annual Salary] / [FTE] / [Rate Used] else null, type nullable number),

    Final = Table.RemoveColumns(AddEur, {"Units per EUR", "Latest Rate", "Rate Used", "Entity Currency", "Month Key"})
in
    Final

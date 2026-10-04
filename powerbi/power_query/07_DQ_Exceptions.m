// DQ_Exceptions - every data-quality rule, run against the raw exports.
// One output row per problem found: which file, which person, which rule.
// Loaded into the model for the Data Quality page. Expected result: 19 rows,
// exactly matching data\reference\planted_issues.csv.
let
    Raw = Exports_Raw,
    Cols = {"File", "As Of", "Person ID External"},

    // DQ01 - duplicate rows: group identical rows inside a file; every copy after the first is a hit
    DataCols = List.RemoveItems(Table.ColumnNames(Raw), {"Row ID"}),
    Groups = Table.Group(Raw, DataCols, {{"Copies", each Table.RowCount(_), Int64.Type}}),
    Dupes = Table.SelectRows(Groups, each [Copies] > 1),
    OneRowPerExtraCopy = Table.ExpandListColumn(Table.AddColumn(Dupes, "Extra", each List.Numbers(1, [Copies] - 1)), "Extra"),
    DQ01 = Table.SelectColumns(OneRowPerExtraCopy, Cols),

    // DQ02 - missing manager (the CEO is the only person allowed to have none)
    DQ02 = Table.SelectColumns(
        Table.SelectRows(Raw, each [Manager ID] = "" and [Job Title] <> "Chief Executive Officer"), Cols),

    // DQ03 - manager ID that does not exist in the same file.
    // A left anti join keeps the rows on the left that have NO match on the right.
    PeopleInFile = Table.Distinct(Table.SelectColumns(Raw, {"File", "Person ID External"})),
    WithManager = Table.SelectRows(Raw, each [Manager ID] <> ""),
    NoMatch = Table.NestedJoin(WithManager, {"File", "Manager ID"}, PeopleInFile, {"File", "Person ID External"},
        "Match", JoinKind.LeftAnti),
    DQ03 = Table.SelectColumns(NoMatch, Cols),

    // DQ04 - record not effective yet on the file's as-of date (entered early in the HRIS)
    DQ04 = Table.SelectColumns(Table.SelectRows(Raw, each fnParseDate([Event Date]) > [As Of]), Cols),

    // DQ05 - location label that is not the standard spelling
    StandardLocation = (t as text) as text => let x = Text.Trim(t) in if x = "Praha" then "Prague" else x,
    DQ05 = Table.SelectColumns(Table.SelectRows(Raw, each [Location] <> StandardLocation([Location])), Cols),

    // DQ06 - files whose dates are not ISO (yyyy-MM-dd). One hit per file, not per row.
    IsoFlags = Table.AddColumn(Raw, "Is ISO", each
        (try Date.FromText([Event Date], [Format = "yyyy-MM-dd", Culture = "en-US"]) otherwise null) <> null, type logical),
    NonIsoFiles = Table.Distinct(Table.SelectColumns(Table.SelectRows(IsoFlags, each not [Is ISO]), {"File", "As Of"})),
    DQ06 = Table.AddColumn(NonIsoFiles, "Person ID External", each "", type text),

    // DQ07 - salary currency that does not match the legal entity's currency
    WithEntity = Table.NestedJoin(Raw, {"Legal Entity"}, LegalEntities, {"Legal Entity"}, "Entity", JoinKind.LeftOuter),
    WithEntityCcy = Table.ExpandTableColumn(WithEntity, "Entity", {"Currency"}, {"Entity Currency"}),
    DQ07 = Table.SelectColumns(
        Table.SelectRows(WithEntityCcy, each [Currency] <> "" and [Currency] <> [Entity Currency]), Cols),

    // DQ08 - FTE outside 0 (exclusive) to 1 (inclusive); blank or non-numeric also fails
    DQ08 = Table.SelectColumns(
        Table.SelectRows(Raw, each
            let fte = try Number.FromText([FTE], "en-US") otherwise null
            in fte = null or fte <= 0 or fte > 1),
        Cols),

    Tag = (t as table, id as text) as table => Table.AddColumn(t, "Rule ID", each id, type text),
    All = Table.Combine({
        Tag(DQ01, "DQ01"), Tag(DQ02, "DQ02"), Tag(DQ03, "DQ03"), Tag(DQ04, "DQ04"),
        Tag(DQ05, "DQ05"), Tag(DQ06, "DQ06"), Tag(DQ07, "DQ07"), Tag(DQ08, "DQ08")
    }),
    WithRule = Table.NestedJoin(All, {"Rule ID"}, DQ_Rules, {"Rule ID"}, "RuleInfo", JoinKind.LeftOuter),
    Expanded = Table.ExpandTableColumn(WithRule, "RuleInfo", {"Rule", "Rule Label", "Severity", "Severity Order", "Action Taken"}),
    Typed = Table.TransformColumnTypes(Expanded, {
        {"File", type text}, {"As Of", type date}, {"Person ID External", type text}, {"Rule", type text},
        {"Rule Label", type text}, {"Severity", type text}, {"Severity Order", Int64.Type}, {"Action Taken", type text}
    })
in
    Typed

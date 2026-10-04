// Movements - hires, leavers and transfers, found by comparing each month with the month before.
//   in this month, not last month  -> Hire
//   in last month, not this month  -> Leaver
//   in both, different department  -> Transfer Out (old) + Transfer In (new)
// Because every movement comes from the snapshots themselves, the headcount bridge
// (opening + hires - leavers + transfers in - transfers out = closing) always closes.
// Expected: 335 rows = 92 Hire, 61 Leaver, 91 Transfer In, 91 Transfer Out.
let
    HC = Table.SelectColumns(Table.SelectRows(Snapshot, each [Is Headcount]),
        {"Person ID External", "As Of", "Division", "Department", "Legal Entity", "Gender", "Grade"}),
    FirstMonth = List.Min(HC[As Of]),
    LastMonth = List.Max(HC[As Of]),

    // Shift every snapshot forward one month, so "last month" lines up with "this month"
    Prev = Table.TransformColumns(HC, {{"As Of", each Date.EndOfMonth(Date.AddMonths(_, 1)), type date}}),
    Joined = Table.NestedJoin(HC, {"Person ID External", "As Of"}, Prev, {"Person ID External", "As Of"},
        "Prev", JoinKind.FullOuter),
    Expanded = Table.ExpandTableColumn(Joined, "Prev",
        {"Person ID External", "As Of", "Division", "Department", "Legal Entity", "Gender", "Grade"},
        {"P Person", "P As Of", "P Division", "P Department", "P Legal Entity", "P Gender", "P Grade"}),

    // Each joined row becomes zero, one or two movement records
    FromThisMonth = (r as record, kind as text) as record => [Movement = kind, Person = r[Person ID External], Month = r[As Of],
        Division = r[Division], Department = r[Department], Entity = r[Legal Entity], Gender = r[Gender], Grade = r[Grade]],
    FromLastMonth = (r as record, kind as text, month as date) as record => [Movement = kind, Person = r[P Person], Month = month,
        Division = r[P Division], Department = r[P Department], Entity = r[P Legal Entity], Gender = r[P Gender], Grade = r[P Grade]],
    Classified = Table.AddColumn(Expanded, "Records", each
        if [Person ID External] = null then {FromLastMonth(_, "Leaver", [P As Of])}
        else if [P Person] = null then {FromThisMonth(_, "Hire")}
        else if [Department] <> [P Department] then {FromLastMonth(_, "Transfer Out", [As Of]), FromThisMonth(_, "Transfer In")}
        else {}),
    OnlyRecords = Table.SelectColumns(Classified, {"Records"}),
    OneRowEach = Table.ExpandListColumn(OnlyRecords, "Records"),
    NonEmpty = Table.SelectRows(OneRowEach, each [Records] <> null),
    AsColumns = Table.ExpandRecordColumn(NonEmpty, "Records",
        {"Movement", "Person", "Month", "Division", "Department", "Entity", "Gender", "Grade"},
        {"Movement", "Person ID External", "Month", "Division", "Department", "Legal Entity", "Gender", "Grade"}),

    // The first month has no "month before", and leavers shifted past the last month don't exist yet
    InRange = Table.SelectRows(AsColumns, each [Month] > FirstMonth and [Month] <= LastMonth),

    // Leaver details come from that month's termination row
    Terminations = Table.SelectColumns(Table.SelectRows(Snapshot, each [Employee Status] = "Terminated"),
        {"Person ID External", "As Of", "Event Reason", "Regret Termination", "Hire Date", "Event Date"}),
    WithExit = Table.NestedJoin(InRange, {"Person ID External", "Month"}, Terminations, {"Person ID External", "As Of"},
        "Exit", JoinKind.LeftOuter),
    ExitCols = Table.ExpandTableColumn(WithExit, "Exit", {"Event Reason", "Regret Termination", "Hire Date", "Event Date"}),
    WithReason = Table.NestedJoin(ExitCols, {"Event Reason"}, TerminationReasons, {"Event Reason"}, "Reason", JoinKind.LeftOuter),
    ReasonCols = Table.ExpandTableColumn(WithReason, "Reason", {"Leaver Category", "Is Voluntary", "Reason Short"}),
    AddTenure = Table.AddColumn(ReasonCols, "Tenure Months At Exit", each
        if [Event Date] = null then null else Number.Round(Duration.Days([Event Date] - [Hire Date]) / 30.4375, 1),
        type nullable number),
    AddBand = Table.AddColumn(AddTenure, "Tenure Band", each
        if [Tenure Months At Exit] = null then null else if [Tenure Months At Exit] < 12 then "< 1 year"
        else if [Tenure Months At Exit] < 24 then "1–2 years" else if [Tenure Months At Exit] < 60 then "2–5 years"
        else "5+ years", type nullable text),
    AddEarly = Table.AddColumn(AddBand, "Is Early Leaver", each
        [Movement] = "Leaver" and [Tenure Months At Exit] <> null and [Tenure Months At Exit] < 12, type logical),
    AddRegretted = Table.AddColumn(AddEarly, "Is Regretted", each [Regret Termination] = "Yes", type logical),
    // +1 / -1 so a single SUM gives the net change in any slice (used by the bridge)
    AddSign = Table.AddColumn(AddRegretted, "Bridge Sign", each
        if [Movement] = "Leaver" or [Movement] = "Transfer Out" then -1 else 1, Int64.Type),

    Final = Table.TransformColumnTypes(Table.RemoveColumns(AddSign, {"Regret Termination", "Hire Date", "Event Date"}), {
        {"Movement", type text}, {"Person ID External", type text}, {"Month", type date}, {"Division", type text},
        {"Department", type text}, {"Legal Entity", type text}, {"Gender", type text}, {"Grade", Int64.Type},
        {"Event Reason", type text}, {"Leaver Category", type text}, {"Is Voluntary", type logical}, {"Reason Short", type text}
    })
in
    Final

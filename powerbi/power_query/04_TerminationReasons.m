// TerminationReasons - lookup: Event Reason -> Voluntary / Involuntary / Retirement.
// Keeping this mapping in a table (not in an IF formula) means HR can change it without
// touching the logic. Staging only: uncheck "Enable load".
let
    Source = Csv.Document(
        File.Contents(ProjectFolder & "\data\reference\termination_reasons.csv"),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed = Table.TransformColumnTypes(Promoted, {
        {"Event Reason", type text}, {"Leaver Category", type text}, {"Is Voluntary", type text}, {"Reason Short", type text}
    }),
    AsLogical = Table.TransformColumns(Typed, {{"Is Voluntary", each _ = "Yes", type logical}})
in
    AsLogical

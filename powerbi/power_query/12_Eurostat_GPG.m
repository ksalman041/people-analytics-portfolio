// Eurostat_GPG - real benchmark: unadjusted gender pay gap (%) by country and activity,
// Eurostat dataset earn_gr_gpgr2. Flag: p = provisional, d = definition differs, b = break in series.
let
    Source = Csv.Document(
        File.Contents(ProjectFolder & "\data\external\eurostat_gender_pay_gap.csv"),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed = Table.TransformColumnTypes(Promoted, {
        {"Geo", type text}, {"Activity", type text}, {"Year", Int64.Type}, {"Pay Gap %", type number}, {"Flag", type text}
    }, "en-US")
in
    Typed

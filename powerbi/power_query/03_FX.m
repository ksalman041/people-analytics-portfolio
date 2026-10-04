// FX - ECB monthly average rates (real data): how many CZK / GBP / EUR one euro buys.
// Staging only: right-click > uncheck "Enable load"; Snapshot merges it in.
let
    Source = Csv.Document(
        File.Contents(ProjectFolder & "\data\external\fx_rates_monthly.csv"),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    // The culture argument "en-US" makes "24.2965" parse correctly on a Czech or German PC,
    // where the decimal separator is a comma.
    Typed = Table.TransformColumnTypes(Promoted, {
        {"Month", type text}, {"Currency", type text}, {"Units per EUR", type number}
    }, "en-US")
in
    Typed

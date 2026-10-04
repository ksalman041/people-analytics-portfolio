// LegalEntities - lookup: legal entity -> country, location, currency. Loaded as a dimension.
let
    Source = Csv.Document(
        File.Contents(ProjectFolder & "\data\reference\legal_entities.csv"),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed = Table.TransformColumnTypes(Promoted, {
        {"Legal Entity", type text}, {"Entity Code", type text}, {"Country", type text},
        {"Location", type text}, {"Currency", type text}
    })
in
    Typed

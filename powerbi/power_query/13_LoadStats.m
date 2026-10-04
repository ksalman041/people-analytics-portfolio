// LoadStats - rows per monthly file, for the Data Quality page. No personal data.
let
    Grouped = Table.Group(Exports_Raw, {"File", "As Of"}, {{"Rows", each Table.RowCount(_), Int64.Type}}),
    Typed = Table.TransformColumnTypes(Grouped, {{"File", type text}, {"As Of", type date}})
in
    Typed

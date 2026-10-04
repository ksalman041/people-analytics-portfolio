// DimTenureBand - length-of-service bands; filters both Snapshot and Movements.
#table(
    type table [#"Tenure Band" = text, #"Band Order" = Int64.Type],
    {{"< 1 year", 1}, {"1–2 years", 2}, {"2–5 years", 3}, {"5+ years", 4}}
)

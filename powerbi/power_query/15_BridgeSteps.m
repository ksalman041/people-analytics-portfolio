// BridgeSteps - the categories of the headcount bridge (waterfall). The waterfall adds the
// closing total itself: opening + hires - leavers + net transfers.
#table(
    type table [#"Step" = text, #"Step Order" = Int64.Type],
    {{"Opening", 1}, {"Hires", 2}, {"Voluntary leavers", 3}, {"Involuntary leavers", 4}, {"Retirements", 5}, {"Net transfers", 6}}
)

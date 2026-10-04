// fnParseDate - turns "2025-11-30" (ISO) or "30.11.2025" (German export) into a date.
// Blank text stays blank. One function, reused by every query that reads dates, so
// the rule for "what counts as a valid date" is written down exactly once.
(value as nullable text) as nullable date =>
let
    t = if value = null then "" else Text.Trim(value),
    iso = try Date.FromText(t, [Format = "yyyy-MM-dd", Culture = "en-US"]) otherwise null,
    german = try Date.FromText(t, [Format = "dd.MM.yyyy", Culture = "de-DE"]) otherwise null,
    result = if t = "" then null else if iso <> null then iso else german
in
    result

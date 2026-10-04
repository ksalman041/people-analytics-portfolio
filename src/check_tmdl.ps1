# check_tmdl.ps1 - parse the semantic model with Power BI Desktop's own TMDL library.
# Fails with the file and line of the first syntax error; otherwise lists what it found.
# Run: powershell -ExecutionPolicy Bypass -File src\check_tmdl.ps1
param([string]$Folder = "$PSScriptRoot\..\powerbi\Board_Pack.SemanticModel\definition")

$bin = "C:\Program Files\Microsoft Power BI Desktop\bin"
Add-Type -Path "$bin\Microsoft.PowerBI.Tabular.dll"
try {
    $db = [Microsoft.AnalysisServices.Tabular.TmdlSerializer]::DeserializeDatabaseFromFolder((Resolve-Path $Folder).Path)
    $m = $db.Model
    "OK: {0} tables, {1} relationships, {2} roles, {3} expressions" -f $m.Tables.Count, $m.Relationships.Count, $m.Roles.Count, $m.Expressions.Count
    foreach ($t in $m.Tables) { "  {0,-14} {1,2} columns {2,3} measures" -f $t.Name, $t.Columns.Count, $t.Measures.Count }
} catch {
    "TMDL ERROR: " + $_.Exception.GetType().Name
    $e = $_.Exception
    while ($e) { "  " + $e.Message; $e = $e.InnerException }
    exit 1
}

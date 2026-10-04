# check_powerbi_numbers.ps1 - query the measures inside the open Power BI Desktop file and save them,
# so src/compare_powerbi.py can compare them with data/reference/reference_kpis.csv.
# Needs Board_Pack.pbip open in Power BI Desktop (it hosts a local Analysis Services engine).
# Run: powershell -ExecutionPolicy Bypass -File src\check_powerbi_numbers.ps1
param([string]$Out = "$PSScriptRoot\..\data\reference\powerbi_kpis.csv")

$bin = "C:\Program Files\Microsoft Power BI Desktop\bin"
Add-Type -Path "$bin\Microsoft.PowerBI.AdomdClient.dll"
$ws = "$env:LOCALAPPDATA\Microsoft\Power BI Desktop\AnalysisServicesWorkspaces"
$portFile = Get-ChildItem $ws -Recurse -Filter msmdsrv.port.txt -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $portFile) { "No running Power BI model found - open Board_Pack.pbip first."; exit 1 }
$port = (Get-Content $portFile.FullName -Encoding Unicode).Trim()
$conn = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection("Data Source=localhost:$port")
$conn.Open()

$kpis = [ordered]@{
  "Headcount" = "[Headcount]"; "Turnover R12 %" = "[Turnover R12 %] * 100"; "Voluntary Turnover R12 %" = "[Voluntary Turnover R12 %] * 100";
  "Early Leavers R12 %" = "[Early Leavers R12 %] * 100"; "Women in Leadership %" = "[Women in Leadership %] * 100";
  "Pay Gap Mean %" = "[Pay Gap Mean %] * 100"; "Pay Gap Median %" = "[Pay Gap Median %] * 100"; "Pay Gap Adjusted %" = "[Pay Gap Like-for-like %] * 100"
}
$cols = ($kpis.GetEnumerator() | ForEach-Object { '"{0}", {1}' -f $_.Key, $_.Value }) -join ", "
$rows = @()
foreach ($month in @("2025-09-30", "2026-03-31", "2026-09-30")) {
  $d = [datetime]::Parse($month)
  $filter = "TREATAS ( { DATE ( $($d.Year), $($d.Month), $($d.Day) ) }, DimDate[Month End] )"
  $queries = @{
    "Company" = "EVALUATE ROW ( `"Scope`", `"Company`", $cols )"
    "Division" = "EVALUATE SUMMARIZECOLUMNS ( DimDivision[Division], $filter, $cols )"
    "Entity" = "EVALUATE SUMMARIZECOLUMNS ( LegalEntities[Legal Entity], $filter, $cols )"
  }
  $queries["Company"] = "EVALUATE CALCULATETABLE ( ROW ( `"Scope`", `"Company`", $cols ), $filter )"
  foreach ($q in $queries.Values) {
    $cmd = $conn.CreateCommand(); $cmd.CommandText = $q
    $rd = $cmd.ExecuteReader()
    while ($rd.Read()) {
      $scope = [string]$rd.GetValue(0)
      for ($i = 1; $i -lt $rd.FieldCount; $i++) {
        $name = ($rd.GetName($i) -replace '^\[|\]$', '')
        $v = if ($rd.IsDBNull($i)) { "" } else { [string]::Format([cultureinfo]::InvariantCulture, "{0}", $rd.GetValue($i)) }
        $rows += [pscustomobject]@{ Month = $month.Substring(0, 7); Scope = $scope; KPI = $name; Value = $v }
      }
    }
    $rd.Close()
  }
}
$conn.Close()
$rows | Export-Csv -Path $Out -NoTypeInformation -Encoding UTF8
"Saved {0} values from Power BI to {1}" -f $rows.Count, (Resolve-Path $Out)

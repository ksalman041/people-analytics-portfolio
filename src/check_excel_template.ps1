# check_excel_template.ps1 - let Excel itself calculate the reorg template and read back the checks.
# Opens the file invisibly and read-only, never saves it.
# Run: powershell -ExecutionPolicy Bypass -File src\check_excel_template.ps1
param([string]$Path = "$PSScriptRoot\..\excel\reorg_mapping_template.xlsx")

$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false; $xl.DisplayAlerts = $false
try {
    $wb = $xl.Workbooks.Open((Resolve-Path $Path).Path, 0, $true)
    $xl.CalculateFull()
    $m = $wb.Worksheets.Item("Mapping")
    "Mapping (rows with data):"
    for ($r = 5; $r -le 16; $r++) {
        $unit = $m.Cells.Item($r, 1).Text
        if ($unit -eq "") { continue }
        $vals = (2, 9, 10, 11, 12, 13) | ForEach-Object { $m.Cells.Item($r, $_).Text }
        "  {0,-22} CC={1,-8} | target: {2,-16} | cc: {3,-14} | head: {4,-12} | date: {5,-26} | {6}" -f $unit, $vals[0], $vals[1], $vals[2], $vals[3], $vals[4], $vals[5]
    }
    $c = $wb.Worksheets.Item("Coverage")
    "Coverage:"
    for ($r = 5; $r -le 8; $r++) { "  {0,-22} {1,4}  {2}" -f $c.Cells.Item($r, 1).Text, $c.Cells.Item($r, 3).Text, $c.Cells.Item($r, 4).Text }
    for ($r = 10; $r -le 12; $r++) { "  {0,-22} {1}" -f $c.Cells.Item($r, 1).Text, $c.Cells.Item($r, 2).Text }
    $errors = 0
    foreach ($ws in $wb.Worksheets) {
        $used = $ws.UsedRange
        foreach ($cell in $used.Cells) { if ($cell.Text -like "#*") { $errors++; "  ERROR in $($ws.Name)!$($cell.Address()): $($cell.Text)" } }
    }
    "Formula errors (#NAME?, #VALUE! ...): $errors"
    $wb.Close($false)
} finally {
    $xl.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($xl) | Out-Null
}

# merge-hex.ps1 - Combine a chipKIT bootloader .hex with a compiled sketch .hex
# into one file that MPLAB IPE can flash in a single shot.
#
# Usage:
#   .\merge-hex.ps1 -Bootloader "UDB32_MX2_DIP.hex" -App "DefaultBoard.ino.hex" -Out "combined.hex"

param(
    [Parameter(Mandatory=$true)][string]$Bootloader,
    [Parameter(Mandatory=$true)][string]$App,
    [Parameter(Mandatory=$true)][string]$Out
)

function Get-Records($path) {
    if (-not (Test-Path $path)) { throw "File not found: $path" }
    # Keep every record except End-Of-File (type 01). We add exactly one back at the end.
    Get-Content $path | ForEach-Object { $_.Trim() } |
        Where-Object { $_.Length -ge 11 -and $_[0] -eq ':' -and $_.Substring(7,2) -ne '01' }
}

function Get-Ranges($records) {
    $upper = 0
    $seen = @{}
    foreach ($l in $records) {
        $tt = $l.Substring(7,2)
        if ($tt -eq '04') { $upper = [Convert]::ToUInt32($l.Substring(9,4),16) }
        elseif ($tt -eq '00') {
            $addr = ($upper -shl 16) -bor [Convert]::ToUInt32($l.Substring(3,4),16)
            $len  = [Convert]::ToUInt32($l.Substring(1,2),16)
            $key  = '0x{0:X4}0000' -f $upper
            if (-not $seen.ContainsKey($key)) { $seen[$key] = @($addr, ($addr+$len-1)) }
            else {
                $r = $seen[$key]
                if ($addr -lt $r[0]) { $r[0] = $addr }
                if (($addr+$len-1) -gt $r[1]) { $r[1] = $addr+$len-1 }
                $seen[$key] = $r
            }
        }
    }
    return $seen
}

$blRecs  = @(Get-Records $Bootloader)
$appRecs = @(Get-Records $App)

if ($blRecs.Count  -eq 0) { throw "No usable records in bootloader file." }
if ($appRecs.Count -eq 0) { throw "No usable records in app file." }

$blRange  = Get-Ranges $blRecs
$appRange = Get-Ranges $appRecs

Write-Host "Bootloader regions:" -ForegroundColor Cyan
foreach ($k in ($blRange.Keys | Sort-Object)) {
    Write-Host ("  {0}: 0x{1:X8} .. 0x{2:X8}" -f $k, $blRange[$k][0], $blRange[$k][1])
}
Write-Host "Application regions:" -ForegroundColor Cyan
foreach ($k in ($appRange.Keys | Sort-Object)) {
    Write-Host ("  {0}: 0x{1:X8} .. 0x{2:X8}" -f $k, $appRange[$k][0], $appRange[$k][1])
}

# Overlap check - if these collide, one will silently overwrite the other.
$overlap = $false
foreach ($k in $blRange.Keys) {
    if ($appRange.ContainsKey($k)) {
        $b = $blRange[$k]; $a = $appRange[$k]
        if ($b[0] -le $a[1] -and $a[0] -le $b[1]) {
            Write-Host ("  !! OVERLAP in {0}: bootloader 0x{1:X8}-0x{2:X8} vs app 0x{3:X8}-0x{4:X8}" -f $k,$b[0],$b[1],$a[0],$a[1]) -ForegroundColor Red
            $overlap = $true
        }
    }
}
if ($overlap) { throw "Address overlap detected - refusing to write a broken image." }

# The app's records must not inherit the bootloader's segment. Force a fresh
# extended-linear-address record if the app file doesn't open with one.
$prefix = @()
if ($appRecs[0].Substring(7,2) -ne '04') {
    Write-Host "  (app has no leading type-04 record; inserting :020000040000FA)" -ForegroundColor Yellow
    $prefix = @(':020000040000FA')
}

$all = @($blRecs) + $prefix + @($appRecs) + @(':00000001FF')
Set-Content -Path $Out -Value $all -Encoding ascii

Write-Host ""
Write-Host ("Wrote {0} ({1} records, exactly 1 EOF at the end)." -f $Out, $all.Count) -ForegroundColor Green

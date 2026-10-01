# listen-cyton.ps1 - Dumb serial listener. Opens a COM port, prints everything
# that arrives, and tees it to a log file. Receive-only; never transmits.
#
#   .\listen-cyton.ps1 -Port COM14 -Seconds 40

param(
    [string]$Port    = "COM14",
    [int]$Baud       = 115200,
    [int]$Seconds    = 40,
    [string]$LogFile = "$PSScriptRoot\cyton-serial-log.txt"
)

$sp = New-Object System.IO.Ports.SerialPort $Port, $Baud, 'None', 8, 'One'
$sp.ReadTimeout  = 250
$sp.DtrEnable    = $true
$sp.RtsEnable    = $true

try { $sp.Open() }
catch {
    Write-Host "COULD NOT OPEN $Port" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Almost always this means another program is holding the port." -ForegroundColor Yellow
    Write-Host "Close every Arduino IDE window, then try again." -ForegroundColor Yellow
    exit 1
}

Write-Host "Listening on $Port at $Baud for $Seconds seconds." -ForegroundColor Green
Write-Host "POWER ON THE CYTON NOW." -ForegroundColor Cyan
Write-Host "----------------------------------------------------" -ForegroundColor DarkGray

$deadline = (Get-Date).AddSeconds($Seconds)
$buf      = New-Object System.Text.StringBuilder
$total    = 0

while ((Get-Date) -lt $deadline) {
    try {
        $chunk = $sp.ReadExisting()
        if ($chunk.Length -gt 0) {
            $total += $chunk.Length
            [void]$buf.Append($chunk)
            Write-Host $chunk -NoNewline
        }
        Start-Sleep -Milliseconds 50
    }
    catch [TimeoutException] { }
    catch { break }
}

$sp.Close()
$text = $buf.ToString()

Write-Host ""
Write-Host "----------------------------------------------------" -ForegroundColor DarkGray
Write-Host ("Received $total bytes.") -ForegroundColor Green

if ($total -gt 0) {
    Set-Content -Path $LogFile -Value $text -Encoding utf8
    Write-Host "Saved to $LogFile" -ForegroundColor Green
    Write-Host ""
    # Pull out the one number that matters.
    $m = [regex]::Match($text, 'On Board ADS1299 Device ID:\s*0x([0-9A-Fa-f]+)')
    if ($m.Success) {
        $id = $m.Groups[1].Value.ToUpper()
        if ($id -eq '3E') {
            Write-Host ">>> ADS1299 Device ID = 0x$id  -- CORRECT. The EEG chip is alive. <<<" -ForegroundColor Green
        } else {
            Write-Host ">>> ADS1299 Device ID = 0x$id  -- expected 0x3E. <<<" -ForegroundColor Yellow
        }
    }
    # Show non-printable bytes as hex if the text looks like garbage (wrong baud).
    $printable = ($text.ToCharArray() | Where-Object { [int]$_ -ge 32 -and [int]$_ -lt 127 }).Count
    if ($total -gt 8 -and ($printable / $total) -lt 0.6) {
        Write-Host ""
        Write-Host "Output looks like garbage - probably a baud rate mismatch." -ForegroundColor Yellow
        Write-Host "Raw hex of first 64 bytes:" -ForegroundColor Yellow
        $bytes = [System.Text.Encoding]::GetEncoding(28591).GetBytes($text)
        ($bytes | Select-Object -First 64 | ForEach-Object { '{0:X2}' -f $_ }) -join ' '
    }
} else {
    Write-Host ""
    Write-Host "Nothing received. Check, in this order:" -ForegroundColor Yellow
    Write-Host "  1. Was the Cyton powered on during the listening window?"
    Write-Host "  2. Is Cyton J4 pin 4 (D11) wired to the adapter's RX hole?"
    Write-Host "  3. Is Cyton J3 pin 4 (AGND) wired to the adapter's GND hole?"
    Write-Host "  4. Are ALL five PICkit wires unplugged?"
    Write-Host "  5. Loopback test: jumper the adapter's own TX to its own RX and rerun."
}

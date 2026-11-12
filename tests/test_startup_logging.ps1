$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot
$temp = Join-Path $env:TEMP ('MailOffer log test ' + [guid]::NewGuid())
try {
    New-Item -ItemType Directory -Path (Join-Path $temp 'tools') | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $temp 'logs') | Out-Null
    Copy-Item (Join-Path $root 'tools/startup_logging.ps1') (Join-Path $temp 'tools')
    $powershell = (Get-Process -Id $PID).Path
    foreach ($code in @(0, 1)) {
        [IO.File]::WriteAllText((Join-Path $temp 'tools/ensure_python.ps1'), "Write-Output 'Unicode: " + [char]0x00E5 + "'`r`nexit $code", [Text.Encoding]::UTF8)
        & $powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $temp 'tools/startup_logging.ps1')
        if ($LASTEXITCODE -ne $code) { throw 'Lost startup exit status' }
    }
    $fso = New-Object -ComObject Scripting.FileSystemObject
    $stream = $fso.OpenTextFile((Join-Path $temp 'logs/startup.log'), 1, $false, -1)
    try { $text = $stream.ReadAll() } finally { $stream.Close() }
    if (-not $text.Contains('Unicode: ' + [char]0x00E5) -or $text -notmatch '\| ERROR \|.*exit code=1') { throw 'Startup text/encoding or error severity damaged' }
    if (@(Get-ChildItem (Join-Path $temp 'logs') -Filter '*.log').Count -ne 1) { throw 'Extra startup logs' }
} catch {
    Write-Host ('::error::' + ($_ | Out-String).Replace("`r", '%0D').Replace("`n", '%0A'))
    exit 1
} finally {
    Remove-Item -LiteralPath $temp -Recurse -Force
}
exit 0

# Match VBS UTF-16 output; never mix console/OEM bytes into the same log.
$ErrorActionPreference = 'Stop'
$path = Join-Path (Split-Path $PSScriptRoot) 'logs/startup.log'
$code = 1
try {
    ('{0} | INFO | Python startup check' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')) |
        Out-File -LiteralPath $path -Append -Encoding Unicode
    & (Join-Path $PSScriptRoot 'ensure_python.ps1') 2>&1 |
        Out-File -LiteralPath $path -Append -Encoding Unicode
    $code = $LASTEXITCODE
} catch {
    ($_ | Out-String) | Out-File -LiteralPath $path -Append -Encoding Unicode
    $code = 1
}
$level = if ($code -eq 0) { 'INFO' } else { 'ERROR' }
('{0} | {1} | Python startup check ended; exit code={2}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $level, $code) |
    Out-File -LiteralPath $path -Append -Encoding Unicode
exit $code

$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot
. (Join-Path $root 'tools/python_runtime_checks.ps1')
$temporary = Join-Path $env:TEMP ('MailOffer runtime tests ' + [guid]::NewGuid())
New-Item -ItemType Directory -Path $temporary | Out-Null
try {
    # Exercise actual native stderr under ErrorActionPreference=Stop.
    $realPython = (Get-Command python.exe -CommandType Application | Select-Object -First 1).Source
    $badScript = Join-Path $temporary 'broken probe.py'
    [IO.File]::WriteAllText($badScript, "import sys`nsys.stderr.write('expected probe failure')`nsys.exit(7)`n")
    $bad = Invoke-PythonCheck $realPython $badScript
    if ($bad.Code -ne 7 -or $bad.Text -notmatch 'expected probe failure') { throw 'Native stderr must not terminate fallback' }

    $runtimes = @()
    foreach ($version in @('3.14','3.13','3.15')) {
        $folder = Join-Path $temporary $version
        New-Item -ItemType Directory -Path $folder | Out-Null
        [IO.File]::WriteAllText((Join-Path $folder 'pythonw.exe'), '')
        $runtimes += [pscustomobject]@{Version=[version]$version; Path=(Join-Path $folder 'python.exe')}
    }
    $order = @(Get-PreferredRuntimes $runtimes)
    if ($order[0].Version -ne [version]'3.15' -or $order[1].Version -ne [version]'3.14') { throw 'Wrong runtime order' }
    function Invoke-PythonCheck($Exe, $Script) {
        $version = Split-Path (Split-Path $Exe) -Leaf
        $kind = Split-Path $Script -Leaf
        $script:calls.Add($version + ':' + $kind)
        $fail = ($version -eq '3.15' -and $kind -eq $script:failureKind) -or $script:failAll
        return [pscustomobject]@{Code=[int]$fail; Text='simulated check'}
    }
    foreach ($failureKind in @('', 'update_python_packages.py', 'probe_app_python.py')) {
        $script:failureKind = $failureKind
        $script:failAll = $false
        $script:calls = New-Object 'System.Collections.Generic.List[string]'
        $choice = Select-WorkingRuntime $runtimes (Join-Path $root 'tools') $true
        $expected = if ($failureKind) { [version]'3.14' } else { [version]'3.15' }
        if ($choice.Version -ne $expected) { throw "Wrong fallback for $failureKind" }
        if ($calls[0] -ne '3.15:update_python_packages.py') { throw 'Must start with 3.15' }
        if (-not $failureKind -and ($calls -match '^3.14:')) { throw 'Do not touch fallback when first candidate works' }
    }
    $script:calls.Clear()
    $script:failureKind = 'probe_app_python.py'
    $choice = Select-WorkingRuntime $runtimes (Join-Path $root 'tools') $false
    if ($choice.Version -ne [version]'3.14' -or ($calls -match 'update_python_packages')) { throw 'Offline fallback must not update packages' }
    $script:failAll = $true
    if ($null -ne (Select-WorkingRuntime $runtimes (Join-Path $root 'tools') $false)) { throw 'Must reject failed runtimes' }
    $script:failAll = $false
    Remove-Item -LiteralPath (Join-Path (Split-Path $order[0].Path) 'pythonw.exe')
    $choice = Select-WorkingRuntime $runtimes (Join-Path $root 'tools') $false
    if ($choice.Version -ne [version]'3.14') { throw 'Missing pythonw must fall back' }

    # Exactly the encoding and FSO reader used by startup, including spaces.
    $runtimeFile = Join-Path $temporary 'python-runtime.txt'
    [IO.File]::WriteAllText($runtimeFile, (Join-Path $temporary 'pythonw.exe'), [Text.Encoding]::Unicode)
    $fso = New-Object -ComObject Scripting.FileSystemObject
    $stream = $fso.OpenTextFile($runtimeFile, 1, $false, -1)
    try { $text = $stream.ReadAll().Trim() } finally { $stream.Close() }
    if ($text -ne (Join-Path $temporary 'pythonw.exe')) { throw 'Runtime encoding is not readable by VBS' }
    Write-Host 'Runtime preference, failures, offline fallback and VBS encoding passed.'
} catch {
    $detail = ($_ | Out-String) + $_.ScriptStackTrace
    Write-Host ('::error::' + $detail.Replace('%', '%25').Replace("`r", '%0D').Replace("`n", '%0A'))
    exit 1
} finally {
    Remove-Item -LiteralPath $temporary -Recurse -Force
}

exit 0

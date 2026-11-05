# Windows PowerShell 5.1. Never install a second Python when one is detected.
param([switch]$SkipPythonUpgrade)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'weekly_python.ps1')
$appRoot = Split-Path $PSScriptRoot
$statePath = Join-Path $appRoot 'logs/python-maintenance.json'
$runtimePath = Join-Path $appRoot 'logs/python-runtime.txt'
$startupLock = $null
try {
    if (-not $SkipPythonUpgrade) {
        $logDirectory = Join-Path (Split-Path $PSScriptRoot) 'logs'
        New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null
        $startupLock = [IO.File]::Open((Join-Path $logDirectory 'python-startup.lock'), [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
    }
    if (-not $SkipPythonUpgrade) {
        Register-PythonMaintenance $appRoot
        if (-not (Test-PythonMaintenanceDue $statePath)) {
            if (Test-Path $runtimePath) {
                $existingRuntime = [IO.File]::ReadAllText($runtimePath).Trim()
                if (Test-Path -LiteralPath $existingRuntime -PathType Leaf) {
                    Write-Host 'Veckokontrollen ar redan klar. Ingen uppdateringskontroll vid denna start.'
                    exit 0
                }
            }
        }
    }
    $candidates = @()
    $detected = $false
    foreach ($root in @('HKCU:\Software\Python\PythonCore',
                        'HKLM:\Software\Python\PythonCore',
                        'HKLM:\Software\WOW6432Node\Python\PythonCore')) {
        if (Test-Path $root) {
            foreach ($key in Get-ChildItem $root) {
                $installKey = Join-Path $key.PSPath 'InstallPath'
                if (Test-Path $installKey) {
                    $location = (Get-Item $installKey).GetValue('')
                    if ($location) {
                        $exe = Join-Path $location 'python.exe'
                        if (Test-Path $exe) { $detected = $true; $candidates += $exe }
                    }
                }
            }
        }
    }
    foreach ($name in @('python.exe', 'python3.exe')) {
        foreach ($command in @(Get-Command $name -CommandType Application -ErrorAction SilentlyContinue)) {
            # Windows Store aliases are not installed interpreters.
            if ($command.Source -notmatch '\\Microsoft\\WindowsApps\\') {
                $detected = $true
                $candidates += $command.Source
            }
        }
    }
    # Standard locations also cover installs not registered in PATH/launcher.
    foreach ($parent in @((Join-Path $env:LOCALAPPDATA 'Programs\Python'), $env:ProgramFiles, ${env:ProgramFiles(x86)})) {
        if ($parent -and (Test-Path $parent)) {
            foreach ($folder in @(Get-ChildItem -LiteralPath $parent -Directory -Filter 'Python*')) {
                $exe = Join-Path $folder.FullName 'python.exe'
                if (Test-Path $exe) { $detected = $true; $candidates += $exe }
            }
        }
    }
    if (Get-Command Get-AppxPackage -ErrorAction SilentlyContinue) {
        foreach ($package in @(Get-AppxPackage -Name 'PythonSoftwareFoundation.Python.*')) {
            # Store-installed Python must also prevent a parallel installation.
            $detected = $true
            $exe = Join-Path $package.InstallLocation 'python.exe'
            if (Test-Path $exe) { $candidates += $exe }
        }
    }
    $launcher = Get-Command py.exe -CommandType Application -ErrorAction SilentlyContinue
    if ($launcher) {
        foreach ($line in @(& $launcher.Source -0p 2>$null)) {
            if ("$line" -match '([A-Za-z]:\\.+\\python(?:w)?\.exe)\s*$') {
                $exe = $Matches[1] -replace 'pythonw\.exe$', 'python.exe'
                if (Test-Path $exe) { $detected = $true; $candidates += $exe }
            }
        }
    }
    $versions = @()
    $runtimes = @()
    foreach ($exe in @($candidates | Select-Object -Unique)) {
        $output = & $exe -I -c 'import sys; print("%d.%d" % sys.version_info[:2] if sys.prefix == sys.base_prefix else "virtual")' 2>$null
        if ($LASTEXITCODE -eq 0 -and "$output" -match '^(\d+)\.(\d+)$') {
            $versions += "$output"
            if ([version]"$output" -ge [version]"3.10") {
                $runtimes += [pscustomobject]@{Version=[version]"$output"; Path=$exe}
            }
        }
    }
    if ($detected) {
        # Crucial: this branch NEVER falls back to a fresh installation.
        if (-not $versions.Count) { throw 'Python finns men kunde inte kontrolleras. Ingen ny installation gjordes.' }
        $runtime = $runtimes | Sort-Object Version -Descending | Select-Object -First 1
        if (-not $runtime) { throw 'Ingen gemensam Python 3.10+ hittades. Ingen separat miljo skapas.' }
        $version = $runtime.Version.ToString()
        if (-not $SkipPythonUpgrade) {
            $winget = Get-Command winget.exe -CommandType Application -ErrorAction SilentlyContinue
            if (-not $winget) { throw 'Winget saknas. Uppdatera befintlig Python manuellt; ingen ny installation gjordes.' }
            $package = 'Python.Python.' + $version
            Write-Host "Kontrollerar uppdatering av befintlig Python $version."
            & $winget.Source upgrade --exact --id $package --source winget --silent --accept-package-agreements --accept-source-agreements --disable-interactivity
            if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne -1978335189 -and $LASTEXITCODE -ne 2316632107) {
                throw "Befintlig Python kunde inte uppdateras (kod $LASTEXITCODE). Ingen ny installation gjordes."
            }
        }
        # Run with exactly the interpreter the GUI will use, before importing Qt.
        & $runtime.Path (Join-Path $PSScriptRoot 'update_python_packages.py')
        if ($LASTEXITCODE -ne 0) { throw 'Kontroll/uppdatering av Python-tillagg misslyckades. Se logs/python-startup.log.' }
        $pythonw = Join-Path (Split-Path $runtime.Path) 'pythonw.exe'
        if (-not (Test-Path $pythonw)) { throw 'Gemensam pythonw.exe saknas.' }
        $logs = Join-Path (Split-Path $PSScriptRoot) 'logs'
        New-Item -ItemType Directory -Force -Path $logs | Out-Null
        [IO.File]::WriteAllText((Join-Path $logs 'python-runtime.txt'), $pythonw, [Text.Encoding]::Unicode)

        $state = @{slot=(Get-PythonMaintenanceSlot).ToString('s'); completed=(Get-Date).ToString('s')} | ConvertTo-Json
        $temporaryState = $statePath + '.tmp'
        [IO.File]::WriteAllText($temporaryState, $state)
        Move-Item -LiteralPath $temporaryState -Destination $statePath -Force
        exit 0
    }

    # No installed interpreter found: install the latest stable Windows release.
    Write-Host 'Python saknas. Hamtar senaste stabila Python fran python.org.'
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $html = (Invoke-WebRequest -UseBasicParsing 'https://www.python.org/downloads/windows/').Content
    $match = [regex]::Match($html, 'Latest Python 3 Release\s*-\s*Python\s+(3\.\d+\.\d+)')
    if (-not $match.Success) { throw 'Kunde inte faststalla senaste stabila Python. Ingen installation gjordes.' }
    $version = $match.Groups[1].Value
    $suffix = if ($env:PROCESSOR_ARCHITECTURE -eq 'ARM64' -or $env:PROCESSOR_ARCHITEW6432 -eq 'ARM64') { 'arm64' } elseif ([Environment]::Is64BitOperatingSystem) { 'amd64' } else { '' }
    $filename = 'python-' + $version + $(if ($suffix) { '-' + $suffix }) + '.exe'
    $temporary = Join-Path ([IO.Path]::GetTempPath()) ('mailoffer-python-' + [guid]::NewGuid())
    New-Item -ItemType Directory -Path $temporary | Out-Null
    try {
        $installer = Join-Path $temporary $filename
        Invoke-WebRequest -UseBasicParsing -Uri "https://www.python.org/ftp/python/$version/$filename" -OutFile $installer
        $signature = Get-AuthenticodeSignature $installer
        if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'O=Python Software Foundation(?:,|$)') {
            throw 'Python-installationens signatur kunde inte verifieras.'
        }
        $process = Start-Process -FilePath $installer -ArgumentList '/quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 Include_launcher=1 Include_test=0' -Wait -PassThru
        if ($process.ExitCode -notin @(0, 3010)) { throw "Python-installationen misslyckades (kod $($process.ExitCode))." }
    } finally {
        Remove-Item -LiteralPath $temporary -Recurse -Force
    }
    & $PSCommandPath -SkipPythonUpgrade
    exit $LASTEXITCODE
} catch {
    Write-Host ("Python-kontrollen misslyckades: " + $_.Exception.Message)
    exit 1
} finally {
    if ($startupLock) { $startupLock.Dispose() }
}

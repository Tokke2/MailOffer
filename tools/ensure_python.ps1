# Windows PowerShell 5.1: use existing shared Python; update app packages only.
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'weekly_python.ps1')
. (Join-Path $PSScriptRoot 'python_runtime_checks.ps1')
$appRoot = Split-Path $PSScriptRoot
$statePath = Join-Path $appRoot 'logs/python-maintenance.json'
$runtimePath = Join-Path $appRoot 'logs/python-runtime.txt'
$startupLock = $null
try {
    $logDirectory = Join-Path $appRoot 'logs'
    New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null
    $startupLock = [IO.File]::Open((Join-Path $logDirectory 'python-startup.lock'), [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
    Register-PythonMaintenance $appRoot
    $maintenanceDue = Test-PythonMaintenanceDue $statePath
    if (-not $maintenanceDue -and (Test-Path $runtimePath)) {
        $existingRuntime = [IO.File]::ReadAllText($runtimePath).Trim().Trim([char]0xFEFF)
        $cachedExe = $existingRuntime -replace 'pythonw\.exe$', 'python.exe'
        if ((Test-Path -LiteralPath $existingRuntime -PathType Leaf) -and (Test-Path -LiteralPath $cachedExe -PathType Leaf)) {
            $check = Invoke-PythonCheck $cachedExe (Join-Path $PSScriptRoot 'probe_app_python.py')
            if ($check.Code -eq 0) {
                # Always normalize encoding, including manually edited UTF-8 paths.
                [IO.File]::WriteAllText($runtimePath, $existingRuntime, [Text.Encoding]::Unicode)
                Write-Host 'Veckans tillaggskontroll ar redan klar. Systemets Python andras inte.'
                exit 0
            }
            Write-Host ('Sparad Python klarade inte starttestet: ' + $check.Text)
        }
    }
    $candidates = @()
    $detected = $false
    if (Test-Path $runtimePath) {
        $known = [IO.File]::ReadAllText($runtimePath).Trim() -replace 'pythonw\.exe$', 'python.exe'
        if (Test-Path -LiteralPath $known -PathType Leaf) { $candidates += $known; $detected = $true }
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
    # Get-Command can return several launchers. Never invoke an array of paths.
    foreach ($launcher in @(Get-Command py.exe -CommandType Application -ErrorAction SilentlyContinue)) {
        $previousPreference = $ErrorActionPreference
        try {
            $ErrorActionPreference = 'Continue'
            $launcherLines = @(& $launcher.Source -0p 2>$null)
        } catch { $launcherLines = @() }
        finally { $ErrorActionPreference = $previousPreference }
        foreach ($line in $launcherLines) {
            if ("$line" -match '([A-Za-z]:\\.+\\python(?:w)?\.exe)\s*$') {
                $exe = $Matches[1] -replace 'pythonw\.exe$', 'python.exe'
                if (Test-Path $exe) { $detected = $true; $candidates += $exe }
            }
        }
    }
    $versions = @()
    $runtimes = @()
    foreach ($exe in @($candidates | Select-Object -Unique)) {
        $probe = Invoke-PythonCheck $exe (Join-Path $PSScriptRoot 'probe_system_python.py')
        $output = $probe.Text.Trim()
        if ($probe.Code -eq 0 -and "$output" -match '^(\d+)\.(\d+)$') {
            $versions += "$output"
            if ([version]"$output" -ge [version]"3.10") {
                $runtimes += [pscustomobject]@{Version=[version]"$output"; Path=$exe}
            }
        }
    }
    if ($detected) {
        # Crucial: this branch NEVER falls back to a fresh installation.
        if (-not $versions.Count) { throw 'Python finns men kunde inte kontrolleras. Ingen ny installation gjordes.' }
        $runtime = Select-WorkingRuntime $runtimes $PSScriptRoot $maintenanceDue
        if (-not $runtime) { throw 'Ingen befintlig system-Python klarade tillaggs-/starttestet. Se ovan. Ingen Python installerades eller uppgraderades.' }
        $pythonw = Join-Path (Split-Path $runtime.Path) 'pythonw.exe'
        $logs = Join-Path (Split-Path $PSScriptRoot) 'logs'
        New-Item -ItemType Directory -Force -Path $logs | Out-Null
        [IO.File]::WriteAllText((Join-Path $logs 'python-runtime.txt'), $pythonw, [Text.Encoding]::Unicode)

        if ($maintenanceDue) {
            $state = @{slot=(Get-PythonMaintenanceSlot).ToString('s'); completed=(Get-Date).ToString('s')} | ConvertTo-Json
            $temporaryState = $statePath + '.tmp'
            [IO.File]::WriteAllText($temporaryState, $state)
            Move-Item -LiteralPath $temporaryState -Destination $statePath -Force
        }
        exit 0
    }

    # No installed interpreter found: stop; Python is managed by the user/IT.
    throw 'Systemets Python saknas eller kunde inte hittas. Installera/valj Python 3.10+ manuellt eller kontakta IT. Appen installerar eller uppgraderar inte Python.'
} catch {
    Write-Host ("Python-kontrollen misslyckades: " + $_.Exception.Message)
    exit 1
} finally {
    if ($startupLock) { $startupLock.Dispose() }
}

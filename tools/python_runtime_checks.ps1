# Native stderr must not terminate discovery under Windows PowerShell 5.1.
function Invoke-PythonCheck($Exe, $Script) {
    $ErrorActionPreference = 'Continue'
    try {
        $lines = @(& $Exe -I $Script 2>&1)
        $code = $LASTEXITCODE
        return [pscustomobject]@{Code=$code; Text=($lines | ForEach-Object { "$_" }) -join "`n"}
    } catch {
        return [pscustomobject]@{Code=1; Text=$_.Exception.Message}
    }
}

function Get-PreferredRuntimes($Runtimes) {
    # Explicit preference: installed 3.15, then installed 3.14; older versions last.
    $Runtimes | Sort-Object @{Expression={
        if ($_.Version -eq [version]'3.15') { 0 }
        elseif ($_.Version -eq [version]'3.14') { 1 }
        else { 2 }
    }}, @{Expression={$_.Version}; Descending=$true}
}

function Select-WorkingRuntime($Runtimes, $Tools, [bool]$MaintenanceDue) {
    foreach ($runtime in @(Get-PreferredRuntimes $Runtimes)) {
        $pythonw = Join-Path (Split-Path $runtime.Path) 'pythonw.exe'
        if (-not (Test-Path -LiteralPath $pythonw -PathType Leaf)) {
            Write-Host ('Hoppar over Python ' + $runtime.Version + ': pythonw.exe saknas.')
            continue
        }
        Write-Host ('Provar systemets Python ' + $runtime.Version + ': ' + $runtime.Path)
        if ($MaintenanceDue) {
            $update = Invoke-PythonCheck $runtime.Path (Join-Path $Tools 'update_python_packages.py')
            if ($update.Text) { Write-Host $update.Text }
            if ($update.Code -ne 0) {
                Write-Host ('Tillaggskontroll misslyckades for Python ' + $runtime.Version + '; provar nasta befintliga version.')
                continue
            }
        }
        $check = Invoke-PythonCheck $runtime.Path (Join-Path $Tools 'probe_app_python.py')
        if ($check.Code -eq 0) { return $runtime }
        Write-Host ('Starttest misslyckades for Python ' + $runtime.Version + ': ' + $check.Text)
    }
    return $null
}

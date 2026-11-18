# Discovery and startup scans must never allocate a console of their own.
function Invoke-HiddenNative($Exe, [string]$Arguments) {
    $process = New-Object System.Diagnostics.Process
    $info = New-Object System.Diagnostics.ProcessStartInfo
    $info.FileName = $Exe
    $info.Arguments = $Arguments
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $info.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
    $info.RedirectStandardInput = $true
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    $process.StartInfo = $info
    try {
        if (-not $process.Start()) { throw 'Could not start background check' }
        $process.StandardInput.Close()
        # Drain both streams concurrently: pip/import errors must not deadlock.
        $output = $process.StandardOutput.ReadToEndAsync()
        $errors = $process.StandardError.ReadToEndAsync()
        if (-not $process.WaitForExit(1200000)) {
            $process.Kill()
            $process.WaitForExit()
            return [pscustomobject]@{Code=1; Text='Background check timed out'}
        }
        return [pscustomobject]@{Code=$process.ExitCode; Text=($output.Result + "`n" + $errors.Result).Trim()}
    } catch {
        return [pscustomobject]@{Code=1; Text=$_.Exception.Message}
    } finally {
        $process.Dispose()
    }
}

function Invoke-PythonCheck($Exe, $Script) {
    # Windows file names cannot contain quotes; quote the script path for spaces.
    return Invoke-HiddenNative $Exe ('-I "' + $Script + '"')
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

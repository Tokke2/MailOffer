# Calendar scheduling in the computer's local timezone; no network operations.
function Get-PythonMaintenanceSlot([datetime]$Now = (Get-Date)) {
    $days = (([int]$Now.DayOfWeek + 6) % 7)
    $slot = $Now.Date.AddDays(-$days).AddHours(8)
    if ($Now -lt $slot) { $slot = $slot.AddDays(-7) }
    return $slot
}

function Test-PythonMaintenanceDue($StatePath, [datetime]$Now = (Get-Date)) {
    try {
        $state = Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json
        $last = [datetime]::Parse($state.slot, [Globalization.CultureInfo]::InvariantCulture)
        return $last -lt (Get-PythonMaintenanceSlot $Now)
    } catch { return $true }
}

function Register-PythonMaintenance($AppRoot) {
    try {
        $sha = [Security.Cryptography.SHA256]::Create()
        try { $hash = [BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($AppRoot.ToLowerInvariant()))).Replace('-', '').Substring(0, 12) }
        finally { $sha.Dispose() }
        $name = 'MailOffer-Python-Weekly-' + $hash
        $script = Join-Path $AppRoot 'tools\weekly_python.vbs'
        $arguments = '//B //Nologo "' + $script + '"'
        $existing = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
        if ($existing -and $existing.Actions.Arguments -eq $arguments) { return }
        $action = New-ScheduledTaskAction -Execute (Join-Path $env:WINDIR 'System32\wscript.exe') -Argument $arguments -WorkingDirectory $AppRoot
        $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At '08:00'
        $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew
        $user = [Security.Principal.WindowsIdentity]::GetCurrent().Name
        $principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
        Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
    } catch {
        Write-Host ('VARNING: Veckoschemat kunde inte registreras. Kontroll sker vid forsta appstart efter mandag 08:00. ' + $_.Exception.Message)
    }
}

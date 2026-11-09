# Exercise the real discovery block without installing Python or packages.
$ErrorActionPreference = 'Stop'
$tokens = $null
$errors = $null
$root = Split-Path $PSScriptRoot
$ast = [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $root 'tools/ensure_python.ps1'), [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw 'Invalid startup script syntax' }
$block = $ast.Find({ param($node)
    $node -is [System.Management.Automation.Language.ForEachStatementAst] -and
    $node.Variable.VariablePath.UserPath -eq 'launcher'
}, $true)
if (-not $block) { throw 'Missing per-launcher loop' }
$probe = [scriptblock]::Create($block.Extent.Text)
$temporary = Join-Path $env:TEMP ('MailOffer launchers ' + [guid]::NewGuid())
New-Item -ItemType Directory -Path $temporary | Out-Null
try {
    $all = @()
    foreach ($number in 1..3) {
        $folder = Join-Path $temporary "Python location $number"
        New-Item -ItemType Directory -Path $folder | Out-Null
        $runtime = Join-Path $folder 'python.exe'
        [IO.File]::WriteAllText($runtime, '')
        $launcher = Join-Path $folder 'fake py.ps1'
        [IO.File]::WriteAllText($launcher, "param([string]`$option)`r`nif (`$option -ne '-0p') { throw 'Wrong arguments' }`r`nWrite-Output ' -V:3.14 * $runtime'")
        $all += [pscustomobject]@{Source=$launcher}
    }
    function Get-Command {
        param($Name, $CommandType, $ErrorAction)
        if ($Name -ne 'py.exe') { throw 'Unexpected command lookup' }
        $script:fakeLaunchers
    }
    foreach ($count in 0..3) {
        $script:fakeLaunchers = @($all | Select-Object -First $count)
        $candidates = @()
        $detected = $false
        . $probe
        if ($candidates.Count -ne $count) { throw "Expected $count candidates, got $($candidates.Count)" }
        if ($detected -ne ($count -gt 0)) { throw 'Wrong detection state' }
        foreach ($candidate in $candidates) {
            if (-not (Test-Path -LiteralPath $candidate)) { throw 'Paths were joined or damaged' }
        }
    }
    Write-Host 'Separate launcher discovery: zero, one, two and three launchers passed.'
} finally {
    Remove-Item -LiteralPath $temporary -Recurse -Force
}

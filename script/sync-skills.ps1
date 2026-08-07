#Requires -Version 5.1
[CmdletBinding()]
param(
    [switch]$Check
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$pythonArgs = @('sync-skills', '--root', $root)
if ($Check) { $pythonArgs += '--check' }
Push-Location -LiteralPath $root
try {
    & python -m harness @pythonArgs
    $code = $LASTEXITCODE
}
finally {
    Pop-Location
}
exit $code

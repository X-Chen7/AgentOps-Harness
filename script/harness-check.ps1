#Requires -Version 5.1
param(
    [switch]$Strict
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$pythonArgs = @('check', '--root', $root)
if ($Strict) { $pythonArgs += '--strict' }
Push-Location -LiteralPath $root
try {
    & python -m harness @pythonArgs
    $code = $LASTEXITCODE
}
finally {
    Pop-Location
}
exit $code

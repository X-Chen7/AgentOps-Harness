#Requires -Version 5.1
param(
    [switch]$Backend,
    [switch]$Compile
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot

Write-Host "[check] harness check (python)"
$pythonArgs = @('check', '--root', $root)
if ($Backend) { $pythonArgs += '--backend' }
if ($Compile) { $pythonArgs += '--compile' }
Push-Location -LiteralPath $root
try {
    & python -m harness @pythonArgs
    $code = $LASTEXITCODE
}
finally {
    Pop-Location
}
exit $code

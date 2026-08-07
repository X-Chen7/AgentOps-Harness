#Requires -Version 5.1
param(
    [switch]$PushGate
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$pythonArgs = @('sync', '--root', $root)
if ($PushGate) { $pythonArgs += '--push-gate' }
Push-Location -LiteralPath $root
try {
    & python -m harness @pythonArgs
    $code = $LASTEXITCODE
}
finally {
    Pop-Location
}
exit $code

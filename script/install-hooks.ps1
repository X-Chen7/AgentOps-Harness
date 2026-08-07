#Requires -Version 5.1
param(
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$pythonArgs = @('install-hooks', '--root', $root)
if ($Force) { $pythonArgs += '--force' }
Push-Location -LiteralPath $root
try {
    & python -m harness @pythonArgs
    $code = $LASTEXITCODE
}
finally {
    Pop-Location
}
exit $code

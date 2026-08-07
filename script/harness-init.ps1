#Requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Target,

    [Parameter(Position = 1)]
    [string]$ProjectName = ''
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$pythonArgs = @('init', '--root', $root, '--target', $Target)
if ($ProjectName) { $pythonArgs += @('--project-name', $ProjectName) }
Push-Location -LiteralPath $root
try {
    & python -m harness @pythonArgs
    $code = $LASTEXITCODE
}
finally {
    Pop-Location
}
exit $code

#Requires -Version 5.1
<#
.SYNOPSIS
    Git/PR automation for .harness features (Python CLI wrapper).
.DESCRIPTION
    Commands: commit / push / pr
.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File script\harness-git.ps1 commit -Feature F-001
#>
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('commit', 'push', 'pr')]
    [string]$Command = 'commit',
    [string]$Feature = '',
    [string]$Message = ''
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
if (-not $Feature) {
    throw "Feature id is required (-Feature F-001)"
}
$pythonArgs = @($Command, '--root', $root, '--feature', $Feature)
if ($Message) { $pythonArgs += @('--message', $Message) }
Push-Location -LiteralPath $root
try {
    & python -m harness @pythonArgs
    $code = $LASTEXITCODE
}
finally {
    Pop-Location
}
exit $code

#Requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Target,

    [Parameter(Position = 1)]
    [string]$ProjectName = ''
)

$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$templatePath = Join-Path $repoRoot 'harness-template\AGENTS.md.template'

if (-not (Test-Path -LiteralPath $templatePath)) {
    Write-Error "Template not found: $templatePath"
    exit 1
}

$target = [System.IO.Path]::GetFullPath($Target)
$agentsPath = Join-Path $target 'AGENTS.md'

if (Test-Path -LiteralPath $agentsPath) {
    Write-Output "SKIP: AGENTS.md already exists at $target"
    exit 0
}

if (-not (Test-Path -LiteralPath $target)) {
    New-Item -ItemType Directory -Path $target -Force | Out-Null
}

if (-not $ProjectName) {
    $ProjectName = Split-Path -Leaf $target
    if (-not $ProjectName) {
        $ProjectName = 'UnnamedProject'
    }
}

$harnessDir = Join-Path $target '.harness'
$dirs = @(
    'rules',
    'skills',
    'changes\active',
    'changes\completed',
    'wiki',
    'templates',
    'agents'
)

foreach ($dir in $dirs) {
    New-Item -ItemType Directory -Path (Join-Path $harnessDir $dir) -Force | Out-Null
}

$content = Get-Content -LiteralPath $templatePath -Raw -Encoding UTF8
$content = $content.Replace('{{PROJECT_NAME}}', $ProjectName)
$content = $content.Replace('{{PROJECT_DESC}}', 'TODO: Describe project in one or two sentences.')
$content = $content.Replace('{{ENABLED_MODULES}}', 'TODO: List enabled modules.')

Set-Content -LiteralPath $agentsPath -Value $content -Encoding UTF8

Write-Output "OK: initialized harness at $harnessDir"
exit 0

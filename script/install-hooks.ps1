#Requires -Version 5.1
param(
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "[install-hooks] git is not available"
    exit 1
}
$previousEap = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
& git rev-parse --is-inside-work-tree 2>&1 | Out-Null
$isGitRepo = ($LASTEXITCODE -eq 0)
$ErrorActionPreference = $previousEap
if (-not $isGitRepo) {
    Write-Host "[install-hooks] not a git repository; skip hook installation"
    exit 0
}

$gitDir = (& git rev-parse --git-dir).Trim()
if (-not [System.IO.Path]::IsPathRooted($gitDir)) {
    $gitDir = Join-Path $root $gitDir
}
$hook = Join-Path $gitDir 'hooks\pre-push'
$content = @(
    '#!/bin/sh',
    '# Harness changes git sync gate (installed by script/install-hooks.ps1)',
    'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "script/sync-changes.ps1" -PushGate',
    ''
) -join "`n"

if ((Test-Path -LiteralPath $hook) -and -not $Force) {
    Write-Host "[install-hooks] pre-push hook already exists; use -Force to overwrite: $hook"
    exit 0
}

[System.IO.File]::WriteAllText($hook, $content, (New-Object System.Text.UTF8Encoding($false)))
Write-Host "[install-hooks] installed pre-push hook: $hook"
exit 0

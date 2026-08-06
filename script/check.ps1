#Requires -Version 5.1
param(
    [switch]$Backend,
    [switch]$Compile
)

$ErrorActionPreference = 'Stop'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$failures = @()
$mvn = Get-Command mvn -ErrorAction SilentlyContinue
$root = Split-Path -Parent $scriptDir
$mvnProject = Test-Path -LiteralPath (Join-Path $root 'pom.xml')

Write-Host "[check] harness-check.ps1"
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $scriptDir 'harness-check.ps1')
if ($LASTEXITCODE -ne 0) {
    $failures += 'harness-check'
}

if ($Backend) {
    if ($null -eq $mvn -or -not $mvnProject) {
        Write-Host "[check] no Maven project found; skipping backend verification"
    }
    else {
        $mvnCommands = @(
            @('-pl', 'app-module-user', '-am', 'test'),
            @('-pl', 'app-module-infra', '-am', 'test'),
            @('-pl', 'app-server', '-am', 'package', '-DskipTests')
        )
        foreach ($command in $mvnCommands) {
            $label = 'mvn ' + ($command -join ' ')
            Write-Host "[check] $label"
            & 'mvn' @command
            if ($LASTEXITCODE -ne 0) {
                $failures += $label
            }
        }
    }
}
elseif ($Compile) {
    if ($null -eq $mvn -or -not $mvnProject) {
        Write-Host "[check] no Maven project found; skipping compile gate"
    }
    else {
        $compileCommand = @('-pl', 'app-server', '-am', 'compile', '-DskipTests')
        $label = 'mvn ' + ($compileCommand -join ' ')
        Write-Host "[check] $label"
        & 'mvn' @compileCommand
        if ($LASTEXITCODE -ne 0) {
            $failures += $label
        }
    }
}
else {
    Write-Host "[check] backend checks skipped; run with -Backend to include Maven verification"
}

if ($failures.Count -gt 0) {
    Write-Host "[check] failed:"
    foreach ($failure in $failures) {
        Write-Host "  - $failure"
    }
    exit 1
}

Write-Host "[check] ok"
exit 0

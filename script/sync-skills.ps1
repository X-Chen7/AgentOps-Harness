[CmdletBinding()]
param(
    [switch]$Check
)

$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
$Source = Join-Path $Root '.harness\skills'
$Target = Join-Path $Root '.codex\skills'

function Get-RelativePath {
    param(
        [string]$Path,
        [string]$Base
    )

    if ($Path.StartsWith($Base, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $Path.Substring($Base.Length).TrimStart('\')
    }
    return $Path
}

function Copy-Tree {
    param(
        [string]$SourcePath,
        [string]$TargetPath
    )

    if (-not (Test-Path -LiteralPath $TargetPath -PathType Container)) {
        New-Item -ItemType Directory -Path $TargetPath -Force | Out-Null
    }

    Get-ChildItem -LiteralPath $SourcePath -Force | ForEach-Object {
        $Destination = Join-Path $TargetPath $_.Name
        if ($_.PSIsContainer) {
            Copy-Tree -SourcePath $_.FullName -TargetPath $Destination
        } else {
            Copy-Item -LiteralPath $_.FullName -Destination $Destination -Force
        }
    }
}

function Get-FileMap {
    param(
        [string]$BasePath
    )

    $Map = @{}
    if (Test-Path -LiteralPath $BasePath -PathType Container) {
        Get-ChildItem -LiteralPath $BasePath -Recurse -File -Force | ForEach-Object {
            $Relative = Get-RelativePath -Path $_.FullName -Base $BasePath
            $Map[$Relative] = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
        }
    }
    return $Map
}

if (-not (Test-Path -LiteralPath $Source -PathType Container)) {
    Write-Output "FAILED: source not found: $Source"
    exit 2
}

if (-not $Check) {
    Copy-Tree -SourcePath $Source -TargetPath $Target
    $SkillCount = (Get-ChildItem -LiteralPath $Source -Directory).Count
    Write-Output "Synced $SkillCount skills to $Target"
    exit 0
}

$SourceMap = Get-FileMap -BasePath $Source
$TargetMap = Get-FileMap -BasePath $Target
$DifferenceCount = 0

foreach ($Relative in ($SourceMap.Keys | Sort-Object)) {
    if (-not $TargetMap.ContainsKey($Relative)) {
        Write-Output "MISSING: $Relative"
        $DifferenceCount++
    } elseif ($SourceMap[$Relative] -ne $TargetMap[$Relative]) {
        Write-Output "DIFF: $Relative"
        $DifferenceCount++
    }
}

foreach ($Relative in ($TargetMap.Keys | Sort-Object)) {
    if (-not $SourceMap.ContainsKey($Relative)) {
        Write-Output "EXTRA: $Relative"
        $DifferenceCount++
    }
}

if ($DifferenceCount -gt 0) {
    Write-Output "FAILED: $DifferenceCount difference(s)"
    exit 1
}

Write-Output "OK: files match"
exit 0

#Requires -Version 5.1
<#
.SYNOPSIS
    Git/PR automation for .harness features.
.DESCRIPTION
    Commands:
      commit - create/switch feature branch, stage, commit, update feature-list
      push   - run checks, push branch, update feature-list
      pr     - create a PR with gh, update feature-list
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

$ErrorActionPreference = 'Continue'
$root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$harness = Join-Path $root '.harness'
$featureListPath = Join-Path $harness 'changes\active\feature-list.json'
$stateRoot = Join-Path $harness 'state'

function Write-Step([string]$message) {
    Write-Host "[harness-git] $message"
}

function Get-Timestamp {
    return (Get-Date -Format 'yyyy-MM-ddTHH:mm:sszzz')
}

function Read-JsonFile([string]$path) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Missing file: $path"
    }
    try {
        return (Get-Content -Raw -Encoding UTF8 $path | ConvertFrom-Json)
    }
    catch {
        throw "Invalid JSON in $path : $($_.Exception.Message)"
    }
}

function Save-JsonFile([object]$object, [string]$path) {
    $json = $object | ConvertTo-Json -Depth 20
    $json = [regex]::Replace($json, '\\u([0-9a-fA-F]{4})', {
        param($match)
        $code = [Convert]::ToInt32($match.Groups[1].Value, 16)
        return [string][char]$code
    })
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($path, $json, $utf8)
}

function Get-FeatureById([object]$features, [string]$featureId) {
    foreach ($feature in $features.features) {
        if ($feature.id -eq $featureId) {
            return $feature
        }
    }
    return $null
}

function Assert-GitRepo {
    $previousEap = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    & git rev-parse --is-inside-work-tree 2>&1 | Out-Null
    $isRepo = ($LASTEXITCODE -eq 0)
    $ErrorActionPreference = $previousEap
    if (-not $isRepo) {
        throw "Not a git repository; run git init first"
    }
}

function Get-FeatureBranchName($feature) {
    if ($feature.branch -and (-not $feature.branch.StartsWith([char]0x672A))) {
        return [string]$feature.branch
    }
    return ('feature/' + $feature.id)
}

function Add-GitHistoryEntry($feature, [string]$status, [string]$note) {
    if ($null -eq $feature.history) {
        $feature.history = @()
    }
    $entry = @{
        status = $status
        at = (Get-Date -Format 'yyyy-MM-dd')
        by = 'harness-git'
        note = $note
    }
    $feature.history = @($feature.history) + @($entry)
}

function Invoke-GitCommit($features, $feature) {
    Assert-GitRepo
    $branch = Get-FeatureBranchName $feature
    $current = (& git rev-parse --abbrev-ref HEAD).Trim()
    if ($current -ne $branch) {
        $previousEap = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        & git rev-parse --verify --quiet "refs/heads/$branch" *> $null
        $branchExists = ($LASTEXITCODE -eq 0)
        $ErrorActionPreference = $previousEap
        if ($branchExists) {
            & git checkout $branch 2>&1 | Out-Null
        }
        else {
            & git checkout -b $branch 2>&1 | Out-Null
        }
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to switch to branch $branch"
        }
    }
    & git add -A 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "git add failed"
    }
    $pending = @(& git status --porcelain)
    if ($pending.Count -eq 0) {
        Write-Step "no changes to commit for $($feature.id)"
        return
    }
    if (-not $Message) {
        $Message = "feat($($feature.id)): $($feature.title) Ref: $($feature.id)"
    }
    & git commit -m $Message 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "git commit failed"
    }
    $commit = (& git rev-parse HEAD).Trim()
    $feature.status = 'committed'
    $feature.branch = $branch
    $feature.commit = $commit
    $feature.push_status = 'none'
    Add-GitHistoryEntry $feature 'committed' "committed on $branch"
    $features.updated_at = (Get-Date -Format 'yyyy-MM-dd')
    Save-JsonFile $features $featureListPath
    Write-Step "committed $($feature.id) on $branch at $commit"
}

function Invoke-GitPush($features, $feature) {
    Assert-GitRepo
    $remotes = @(& git remote)
    if ($remotes.Count -eq 0) {
        Write-Step "no git remote configured; add origin first"
        exit 1
    }
    if ($feature.status -ne 'committed' -or -not $feature.commit) {
        Write-Step "feature $($feature.id) is not committed yet; run commit first"
        exit 1
    }
    $branch = Get-FeatureBranchName $feature
    $current = (& git rev-parse --abbrev-ref HEAD).Trim()
    if ($current -ne $branch) {
        & git checkout $branch 2>&1 | Out-Null
    }
    Write-Step "running script/check.ps1 before push"
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root 'script\check.ps1')
    if ($LASTEXITCODE -ne 0) {
        Write-Step "check failed; push aborted"
        exit 1
    }
    Write-Step "running sync-changes.ps1 -PushGate"
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root 'script\sync-changes.ps1') -PushGate
    if ($LASTEXITCODE -ne 0) {
        Write-Step "push gate failed; push aborted"
        exit 1
    }
    & git push -u origin $branch 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "git push failed"
    }
    $feature.status = 'pushed'
    $feature.push_status = 'pushed'
    $feature.remote_branch = $branch
    Add-GitHistoryEntry $feature 'pushed' "pushed to origin/$branch"
    $features.updated_at = (Get-Date -Format 'yyyy-MM-dd')
    Save-JsonFile $features $featureListPath
    Write-Step "pushed $($feature.id) to origin/$branch"
}

function Invoke-GitPr($features, $feature) {
    Assert-GitRepo
    if ($feature.push_status -ne 'pushed') {
        Write-Step "feature $($feature.id) is not pushed yet; run push first"
        exit 1
    }
    $branch = Get-FeatureBranchName $feature
    $title = "feat($($feature.id)): $($feature.title)"
    $body = @(
        "## Related",
        "- Feature ID: $($feature.id)",
        "- Branch: $branch",
        "- Commit: $($feature.commit)",
        "",
        "## Summary",
        "- See commit $($feature.commit)",
        "",
        "## Verification",
        "- script/check.ps1 passed before push"
    ) -join "`n"
    $gh = Get-Command gh -ErrorAction SilentlyContinue
    if ($null -eq $gh) {
        $reportDir = Join-Path $stateRoot 'reports'
        New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
        $path = Join-Path $reportDir "pr-$($feature.id).md"
        $utf8 = New-Object System.Text.UTF8Encoding($false)
        [System.IO.File]::WriteAllText($path, $body, $utf8)
        Write-Step "gh CLI not found; PR description written to $path"
        exit 1
    }
    $out = & gh pr create --base main --head $branch --title $title --body $body 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Step "gh pr create failed: $out"
        exit 1
    }
    $url = ($out | Select-Object -Last 1).Trim()
    $feature.pr_url = $url
    Add-GitHistoryEntry $feature 'pushed' "PR created: $url"
    $features.updated_at = (Get-Date -Format 'yyyy-MM-dd')
    Save-JsonFile $features $featureListPath
    Write-Step "PR created: $url"
}

if (-not $Feature) {
    throw "Feature id is required (-Feature F-001)"
}

$features = Read-JsonFile $featureListPath
$featureObj = Get-FeatureById $features $Feature
if ($null -eq $featureObj) {
    throw "Feature not found: $Feature"
}

switch ($Command) {
    'commit' {
        Invoke-GitCommit $features $featureObj
        exit 0
    }
    'push' {
        Invoke-GitPush $features $featureObj
        exit 0
    }
    'pr' {
        Invoke-GitPr $features $featureObj
        exit 0
    }
}

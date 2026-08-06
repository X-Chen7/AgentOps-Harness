#Requires -Version 5.1
param(
    [switch]$PushGate
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$harness = Join-Path $root '.harness'
$featureList = Join-Path $harness 'changes\active\feature-list.json'
$progress = Join-Path $harness 'PROGRESS.md'
$errors = @()
$warnings = @()

function Add-Error([string]$message) {
    $script:errors += $message
}

function Add-Warning([string]$message) {
    $script:warnings += $message
}

# 1. Git repository detection.
$gitRepo = $false
if (Get-Command git -ErrorAction SilentlyContinue) {
    $previousEap = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    & git rev-parse --is-inside-work-tree 2>&1 | Out-Null
    $gitRepo = ($LASTEXITCODE -eq 0)
    $ErrorActionPreference = $previousEap
}

# 2. Feature-list validation (always runs).
$features = $null
if (-not (Test-Path -LiteralPath $featureList)) {
    Add-Error "Missing $featureList"
}
else {
    try {
        $features = Get-Content -Raw -Encoding UTF8 $featureList | ConvertFrom-Json
    }
    catch {
        Add-Error "feature-list.json is not valid JSON: $($_.Exception.Message)"
    }
}

if ($features) {
    $validStatuses = @('todo', 'in_progress', 'ready_for_review', 'committed', 'pushed', 'merged', 'blocked', 'done')
    $validPushStatuses = @('none', 'local', 'pushed', 'merged')
    foreach ($feature in $features.features) {
        if ($validStatuses -notcontains $feature.status) {
            Add-Error "Invalid feature status: $($feature.id) -> $($feature.status)"
        }
        if ($feature.push_status -and ($validPushStatuses -notcontains $feature.push_status)) {
            Add-Error "Invalid push_status: $($feature.id) -> $($feature.push_status)"
        }
        if (@('committed', 'pushed', 'merged') -contains $feature.status -and -not $feature.commit) {
            Add-Error "Feature $($feature.id) status $($feature.status) requires commit"
        }
        if ($feature.history) {
            foreach ($entry in $feature.history) {
                if (-not $entry.status -or -not $entry.at -or -not $entry.by) {
                    Add-Error "Feature $($feature.id) history entry requires status/at/by"
                }
            }
        }
    }
    $inProgress = @($features.features | Where-Object { $_.status -eq 'in_progress' }).Count
    if ($inProgress -gt $features.wip_limit) {
        Add-Error "WIP exceeded: $inProgress in_progress, wip_limit=$($features.wip_limit)"
    }
}

# 3. PROGRESS and active-plan consistency (always runs).
if (-not (Test-Path -LiteralPath $progress)) {
    Add-Error "Missing $progress"
}
elseif ($features -and $features.updated_at) {
    $progressText = Get-Content -Raw -Encoding UTF8 $progress
    if ($progressText -notmatch [regex]::Escape($features.updated_at)) {
        $message = "PROGRESS.md does not contain feature-list updated_at $($features.updated_at)"
        if ($PushGate) { Add-Error $message } else { Add-Warning $message }
    }
}

$activeDir = Join-Path $harness 'changes\active'
if (Test-Path -LiteralPath $activeDir) {
    foreach ($file in (Get-ChildItem -LiteralPath $activeDir -File -Filter '*.md')) {
        if ($file.Name -eq 'README.md') {
            continue
        }
        $content = Get-Content -Raw -Encoding UTF8 $file.FullName
        if ([regex]::IsMatch($content, '\u72B6\u6001\uff1a\s*completed|\u72B6\u6001\uff1a\s*\u5DF2\u5B8C\u6210')) {
            Add-Error "Completed plan still in active: $($file.Name)"
        }
    }
}

# 4. Git-specific checks (skipped when not a repository).
if (-not $gitRepo) {
    Write-Host "[sync-changes] not a git repository; git-specific checks skipped"
}
else {
    $previousEap = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $diffCheck = & git diff --check 2>&1
    if ($LASTEXITCODE -ne 0) {
        Add-Error "git diff --check failed: $diffCheck"
    }
    $porcelain = @(& git status --porcelain)
    if ($porcelain.Count -gt 0) {
        $message = "$($porcelain.Count) uncommitted path(s) present before push"
        if ($PushGate) { Add-Error $message } else { Add-Warning $message }
    }
    if ($features) {
        foreach ($feature in $features.features) {
            if ($feature.commit) {
                & git rev-parse --verify "$($feature.commit)^{commit}" 2>$null | Out-Null
                if ($LASTEXITCODE -ne 0) {
                    Add-Error "Feature $($feature.id) references unknown commit: $($feature.commit)"
                }
            }
            if ($feature.branch -and $feature.branch -notmatch '\u672A') {
                & git rev-parse --verify "refs/heads/$($feature.branch)" 2>$null | Out-Null
                if ($LASTEXITCODE -ne 0) {
                    Add-Warning "Feature $($feature.id) branch not found locally: $($feature.branch)"
                }
            }
        }
    }
    $ErrorActionPreference = $previousEap
}

# 5. Summary.
$featureSummary = ''
if ($features) {
    $featureSummary = @($features.features | ForEach-Object { "$($_.id)=$($_.status)" }) -join ', '
}
Write-Host "[sync-changes] features: $featureSummary"
Write-Host "[sync-changes] $($errors.Count) error(s), $($warnings.Count) warning(s)"
foreach ($warning in $warnings) {
    Write-Warning $warning
}
if ($errors.Count -gt 0) {
    foreach ($errorMessage in $errors) {
        Write-Error $errorMessage
    }
    exit 1
}
exit 0

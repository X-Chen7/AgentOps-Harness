#Requires -Version 5.1
<#
.SYNOPSIS
    Executable pipeline runner for .harness.
.DESCRIPTION
    Commands:
      run     - run or resume the pipeline for a feature
      stage   - run a single pipeline stage by id
      status  - print the current pipeline state
      report  - generate a pipeline report
      reset   - remove pipeline state for a feature
.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File script\harness-cli.ps1 run -Feature F-001 -DryRun
.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File script\harness-cli.ps1 run -Feature F-001 -Resume
#>
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('ui', 'run', 'status', 'report', 'reset', 'stage', 'commit', 'push', 'pr')]
    [string]$Command = 'ui',
    [string]$Feature = '',
    [string]$Stage = '',
    [switch]$Resume,
    [switch]$DryRun,
    [int]$TimeoutSeconds = 900,
    [string]$ReasoningEffort = '',
    [string]$Scope = '',
    [string]$Message = ''
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$harness = Join-Path $root '.harness'
$pipelineConfig = Join-Path $harness 'pipelines\default.json'
$featureListPath = Join-Path $harness 'changes\active\feature-list.json'
$stateRoot = Join-Path $harness 'state'
$executorScript = Join-Path $PSScriptRoot 'lib\codex-executor.ps1'

function Write-Step([string]$message) {
    Write-Host "[harness-cli] $message"
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

function Get-StatePath([string]$featureId) {
    $safeId = $featureId -replace '[^A-Za-z0-9_-]', '-'
    return (Join-Path $stateRoot ("pipeline-" + $safeId + ".json"))
}

function New-PipelineState([string]$featureId, $config) {
    $stages = @{}
    foreach ($stage in $config.stages) {
        $stages[$stage.id] = @{
            status = 'pending'
            started_at = ''
            finished_at = ''
            exit_code = $null
            gate_exit_code = $null
            artifacts = @()
            gate_log = ''
        }
    }
    return @{
        feature_id = $featureId
        pipeline = $config.pipeline
        status = 'not_started'
        current_stage = ''
        started_at = ''
        finished_at = ''
        stages = $stages
        history = @()
    }
}

function Load-PipelineState([string]$featureId) {
    $statePath = Get-StatePath $featureId
    if (-not (Test-Path -LiteralPath $statePath)) {
        return $null
    }
    return (Read-JsonFile $statePath)
}

function Save-PipelineState($state) {
    $statePath = Get-StatePath $state.feature_id
    Save-JsonFile $state $statePath
}

function Get-GateText($gate) {
    $parts = @($gate.file) + @($gate.args)
    return ($parts -join ' ')
}

function Expand-Template([string]$templatePath, [hashtable]$values) {
    $text = Get-Content -Raw -Encoding UTF8 $templatePath
    foreach ($key in $values.Keys) {
        $pattern = '\{\{' + [regex]::Escape($key) + '\}\}'
        $text = $text -replace $pattern, ([string]$values[$key])
    }
    return $text
}

function Write-Utf8File([string]$path, [string]$content) {
    $parent = Split-Path -Parent $path
    if (-not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($path, $content, $utf8)
}

function Invoke-CodexExecutor([string]$promptFile, [string]$logFile, [string]$lastMessageFile, [string]$reasoningEffort, [string]$sandbox) {
    if (-not (Test-Path -LiteralPath $executorScript)) {
        throw "Missing executor: $executorScript"
    }
    $executorArgs = @('-PromptFile', $promptFile, '-Root', $root, '-LogFile', $logFile, '-LastMessageFile', $lastMessageFile, '-TimeoutSeconds', $TimeoutSeconds, '-Sandbox', $sandbox)
    if ($reasoningEffort) {
        $executorArgs += @('-ReasoningEffort', $reasoningEffort)
    }
    & powershell -NoProfile -ExecutionPolicy Bypass -File $executorScript @executorArgs
    return $LASTEXITCODE
}

function Invoke-Gate($gate) {
    $gateFile = Join-Path $root $gate.file
    if (-not (Test-Path -LiteralPath $gateFile)) {
        throw "Missing gate file: $gateFile"
    }
    $gateArgs = @($gate.args)
    $gateOutput = & powershell -NoProfile -ExecutionPolicy Bypass -File $gateFile @gateArgs 2>&1
    foreach ($line in $gateOutput) {
        Write-Host $line
    }
    return $LASTEXITCODE
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
    return ('feature/F-' + $feature.id)
}

function Add-GitHistoryEntry($feature, [string]$status, [string]$note) {
    if ($null -eq $feature.history) {
        $feature.history = @()
    }
    $entry = @{
        status = $status
        at = (Get-Date -Format 'yyyy-MM-dd')
        by = 'harness-cli'
        note = $note
    }
    $feature.history = @($feature.history) + @($entry)
}

function Invoke-GitCommit($features, $feature) {
    Assert-GitRepo
    $branch = Get-FeatureBranchName $feature
    $current = (& git rev-parse --abbrev-ref HEAD).Trim()
    if ($current -ne $branch) {
        & git rev-parse --verify "refs/heads/$branch" 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
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
    Add-GitHistoryEntry $feature 'committed' "committed by harness-cli on $branch"
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
    Add-GitHistoryEntry $feature 'pushed' "pushed by harness-cli to origin/$branch"
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
        Write-Utf8File $path $body
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
    Add-GitHistoryEntry $feature 'pushed' "PR created by harness-cli: $url"
    $features.updated_at = (Get-Date -Format 'yyyy-MM-dd')
    Save-JsonFile $features $featureListPath
    Write-Step "PR created: $url"
}

function Update-FeatureStatus($features, $feature, [string]$status, [string]$pipelineStatus, [string]$note) {
    $feature.status = $status
    if ($null -eq $feature.history) {
        $feature.history = @()
    }
    $entry = @{
        status = $status
        at = (Get-Date -Format 'yyyy-MM-dd')
        by = 'harness-cli'
        note = $note
    }
    $feature.history = @($feature.history) + @($entry)
    if ($null -eq $feature.pipeline) {
        $feature.pipeline = @{}
    }
    $feature.pipeline.status = $pipelineStatus
    $feature.pipeline.last_run = (Get-Timestamp)
    $features.updated_at = (Get-Date -Format 'yyyy-MM-dd')
    Save-JsonFile $features $featureListPath
}

function Get-PipelineStages($config) {
    $all = @($config.stages)
    if ($Command -eq 'stage') {
        if (-not $Stage) {
            throw "Stage id is required for the stage command"
        }
        $selected = @($all | Where-Object { $_.id -eq $Stage })
        if ($selected.Count -eq 0) {
            throw "Unknown stage: $Stage"
        }
        return $selected
    }
    return $all
}

function Show-Status($config, $feature) {
    $state = Load-PipelineState $feature.id
    if ($null -eq $state) {
        Write-Step "feature $($feature.id) pipeline status: not_started"
        return
    }
    Write-Step "feature $($feature.id) pipeline status: $($state.status)"
    Write-Step "current_stage: $($state.current_stage)"
    foreach ($stage in $config.stages) {
        $stageState = $state.stages.$($stage.id)
        if ($null -ne $stageState) {
            Write-Step "  $($stage.id): $($stageState.status)"
        }
    }
}

function New-PipelineReport($config, $feature, $state) {
    $templatePath = Join-Path $harness 'templates\pipeline-report.md.template'
    if (-not (Test-Path -LiteralPath $templatePath)) {
        throw "Missing report template: $templatePath"
    }
    $stageLines = @()
    foreach ($stage in $config.stages) {
        $stageState = $state.stages.$($stage.id)
        if ($null -ne $stageState) {
            $stageLines += "- $($stage.id): $($stageState.status)"
        }
    }
    $values = @{
        feature_id = $feature.id
        pipeline = $state.pipeline
        pipeline_status = $state.status
        started_at = $state.started_at
        finished_at = $state.finished_at
        stage_table = ($stageLines -join "`n")
        summary = "Pipeline status: $($state.status). Review the stage logs under .harness/state/logs before merging."
    }
    return (Expand-Template $templatePath $values)
}

function Invoke-Stage($config, $features, $feature, $state, $stage) {
    $stageId = $stage.id
    $startedAt = Get-Timestamp
    $state.status = 'running'
    $state.current_stage = $stageId
    $state.started_at = $startedAt
    $state.stages.$stageId.status = 'running'
    $state.stages.$stageId.started_at = $startedAt
    Save-PipelineState $state

    $taskCardPath = Join-Path (Join-Path $stateRoot 'tasks') "$($feature.id)-$stageId.md"
    $logPath = Join-Path (Join-Path $stateRoot 'logs') "$($feature.id)-$stageId.log"
    $lastMessagePath = Join-Path (Join-Path $stateRoot 'logs') "$($feature.id)-$stageId-last-message.md"

    $templatePath = Join-Path $root $stage.prompt_template
    if (-not (Test-Path -LiteralPath $templatePath)) {
        throw "Missing prompt template: $templatePath"
    }
    $values = @{
        feature_id = $feature.id
        feature_title = $feature.title
        feature_status = $feature.status
        feature_plan = $feature.plan
        stage_label = $stage.label
        stage_goal = $stage.goal
        output_required = ($stage.output_required -join ', ')
        gate_command = (Get-GateText $stage.gate)
        scope = (if ($Scope) { $Scope } else { 'all' })
        rules_index = '.harness/rules/'
        skills_index = '.harness/skills/'
        wiki_index = '.harness/wiki/'
    }
    $card = Expand-Template $templatePath $values
    Write-Utf8File $taskCardPath $card

    $stageTimeout = if ($stage.timeout_seconds) { [int]$stage.timeout_seconds } else { $TimeoutSeconds }
    $stageEffort = if ($stage.reasoning_effort) { [string]$stage.reasoning_effort } else { $ReasoningEffort }
    $stageSandbox = if ($stage.sandbox) { [string]$stage.sandbox } else { 'workspace-write' }
    $effortText = if ($stageEffort) { ", reasoning_effort=$stageEffort" } else { '' }
    $scopeText = if ($Scope) { ", scope=$Scope" } else { '' }
    Write-Step "stage $stageId started (executor=codex, timeout=${stageTimeout}s, sandbox=$stageSandbox$effortText$scopeText)"
    Write-Step "stage $stageId log: $logPath"
    $execExit = Invoke-CodexExecutor $taskCardPath $logPath $lastMessagePath $stageEffort $stageSandbox
    $state.stages.$stageId.exit_code = $execExit
    $state.stages.$stageId.gate_log = $logPath
    Save-PipelineState $state

    if ($execExit -ne 0) {
        $state.stages.$stageId.status = 'failed'
        $state.status = 'blocked'
        $state.finished_at = (Get-Timestamp)
        Save-PipelineState $state
        Update-FeatureStatus $features $feature 'blocked' 'blocked' "pipeline stage $stageId failed with executor exit code $execExit"
        Write-Step "stage $stageId failed (executor exit code $execExit)"
        exit 1
    }

    Write-Step "stage $stageId executor ok, running gate: $(Get-GateText $stage.gate)"
    $gateExit = Invoke-Gate $stage.gate
    $state.stages.$stageId.gate_exit_code = $gateExit
    Save-PipelineState $state

    if ($gateExit -ne 0) {
        $state.stages.$stageId.status = 'failed'
        $state.status = 'blocked'
        $state.finished_at = (Get-Timestamp)
        Save-PipelineState $state
        Update-FeatureStatus $features $feature 'blocked' 'blocked' "pipeline stage $stageId gate failed with exit code $gateExit"
        Write-Step "stage $stageId gate failed (exit code $gateExit)"
        exit 1
    }

    $state.stages.$stageId.status = 'passed'
    $state.stages.$stageId.finished_at = (Get-Timestamp)
    $state.stages.$stageId.artifacts = @($taskCardPath, $logPath)
    Save-PipelineState $state
    Write-Step "stage $stageId passed"
}

function Invoke-CliChild([string]$childCommand, [string]$featureId, [string[]]$extraArgs) {
    if (-not $featureId) {
        Write-Step "select a feature first (option 1)"
        return
    }
    $childArgs = @($childCommand, '-Feature', $featureId) + $extraArgs
    & powershell -NoProfile -ExecutionPolicy Bypass -File $PSCommandPath @childArgs
    Write-Step ("child exit code: " + $LASTEXITCODE)
}

function Show-InteractiveMenu {
    $config = Read-JsonFile $pipelineConfig
    $selected = $null
    while ($true) {
        $features = Read-JsonFile $featureListPath
        Write-Host ""
        Write-Host "harness-cli interactive menu"
        Write-Host "--------------------------------"
        Write-Host "1) Select feature"
        Write-Host "2) Dry-run pipeline"
        Write-Host "3) Run pipeline"
        Write-Host "4) Resume pipeline"
        Write-Host "5) Show status"
        Write-Host "6) Generate report"
        Write-Host "7) Reset pipeline state"
        Write-Host "0) Exit"
        $choice = Read-Host "Choice"
        switch ($choice) {
            '1' {
                $index = 0
                foreach ($feature in $features.features) {
                    $index++
                    Write-Host ("  {0}) {1} [{2}]" -f $index, $feature.id, $feature.status)
                }
                $number = Read-Host "Feature number"
                $parsed = 0
                $featureArray = @($features.features)
                if ([int]::TryParse($number, [ref]$parsed) -and $parsed -ge 1 -and $parsed -le $featureArray.Count) {
                    $selected = $featureArray[$parsed - 1]
                    Write-Step ("selected " + $selected.id)
                }
                else {
                    Write-Step "invalid feature number"
                }
            }
            '2' { Invoke-CliChild 'run' $selected.id @('-DryRun') }
            '3' { Invoke-CliChild 'run' $selected.id @() }
            '4' { Invoke-CliChild 'run' $selected.id @('-Resume') }
            '5' { Invoke-CliChild 'status' $selected.id @() }
            '6' { Invoke-CliChild 'report' $selected.id @() }
            '7' { Invoke-CliChild 'reset' $selected.id @() }
            '0' {
                Write-Step "exit"
                return
            }
            default { Write-Step "unknown choice" }
        }
    }
}

if ($Command -eq 'ui') {
    Show-InteractiveMenu
    exit 0
}

if (-not $Feature) {
    throw "Feature id is required (-Feature F-001)"
}

$config = Read-JsonFile $pipelineConfig
$features = Read-JsonFile $featureListPath
$featureObj = Get-FeatureById $features $Feature
if ($null -eq $featureObj) {
    throw "Feature not found: $Feature"
}

switch ($Command) {
    'status' {
        Show-Status $config $featureObj
        exit 0
    }
    'report' {
        $state = Load-PipelineState $Feature
        if ($null -eq $state) {
            Write-Step "feature $Feature has no pipeline state; run the pipeline first"
            exit 1
        }
        $report = New-PipelineReport $config $featureObj $state
        $reportPath = Join-Path (Join-Path $stateRoot 'reports') "pipeline-$Feature.md"
        Write-Utf8File $reportPath $report
        Write-Step "report written: $reportPath"
        exit 0
    }
    'reset' {
        $statePath = Get-StatePath $Feature
        if (Test-Path -LiteralPath $statePath) {
            Remove-Item -LiteralPath $statePath -Force
            Write-Step "pipeline state reset for $Feature"
        }
        else {
            Write-Step "no pipeline state for $Feature"
        }
        exit 0
    }
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

$stagesToRun = Get-PipelineStages $config

if ($DryRun) {
    Write-Step "dry-run feature: $Feature"
    foreach ($stageItem in $stagesToRun) {
        $stageSandbox = if ($stageItem.sandbox) { [string]$stageItem.sandbox } else { 'workspace-write' }
        $scopeText = if ($Scope) { ", scope=$Scope" } else { '' }
        Write-Step "  stage $($stageItem.id): executor=codex, sandbox=$stageSandbox$scopeText, gate=$(Get-GateText $stageItem.gate)"
    }
    exit 0
}

$state = Load-PipelineState $Feature
if ($null -eq $state) {
    $state = New-PipelineState $Feature $config
}
elseif (-not $Resume -and $Command -eq 'run') {
    throw "Pipeline state exists for $Feature; use -Resume or reset first"
}

Update-FeatureStatus $features $featureObj 'in_progress' 'running' 'pipeline started by harness-cli'

foreach ($stageItem in $stagesToRun) {
    $stageState = $state.stages.$($stageItem.id)
    if ($null -ne $stageState -and $stageState.status -eq 'passed' -and $Command -ne 'stage') {
        continue
    }
    Invoke-Stage $config $features $featureObj $state $stageItem
}

if ($Command -eq 'stage') {
    Write-Step "stage run finished; pipeline remains $($state.status)"
    exit 0
}

$state.status = 'done'
$state.finished_at = (Get-Timestamp)
Save-PipelineState $state
Update-FeatureStatus $features $featureObj 'ready_for_review' 'done' 'pipeline completed by harness-cli'

$report = New-PipelineReport $config $featureObj $state
$reportPath = Join-Path (Join-Path $stateRoot 'reports') "pipeline-$Feature.md"
Write-Utf8File $reportPath $report

Write-Step "pipeline done for $Feature"
Write-Step "report: $reportPath"
exit 0

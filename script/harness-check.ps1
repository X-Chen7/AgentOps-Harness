#Requires -Version 5.1
param(
    [switch]$Strict
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$harness = Join-Path $root '.harness'
$errors = @()
$warnings = @()

function Add-Error([string]$message) {
    $script:errors += $message
}

function Add-Warning([string]$message) {
    $script:warnings += $message
}

# 1. AGENTS.md must route to existing harness files and include the frontend skill.
$agents = Join-Path $root 'AGENTS.md'
if (-not (Test-Path -LiteralPath $agents)) {
    Add-Error "AGENTS.md is missing"
}
else {
    $agentsText = Get-Content -Raw -Encoding UTF8 $agents
    $scannedText = $agentsText
    $importMatches = [regex]::Matches($agentsText, '(?m)^@\s*([^\r\n]+)')
    foreach ($importMatch in $importMatches) {
        $importRel = $importMatch.Groups[1].Value.Trim()
        $importPath = Join-Path $root $importRel
        if (-not (Test-Path -LiteralPath $importPath)) {
            Add-Error "Broken AGENTS import: $importRel"
        }
        else {
            $scannedText += "`n" + (Get-Content -Raw -Encoding UTF8 $importPath)
        }
    }
    $paths = [regex]::Matches($scannedText, '\.harness/[^\s`\)\]\|\}]+') |
        ForEach-Object { $_.Value.TrimEnd('.', ',', ';', ')', ']', '}') }
    foreach ($path in ($paths | Select-Object -Unique)) {
        $candidate = Join-Path $root ($path -replace '^\./', '')
        if (-not (Test-Path -LiteralPath $candidate)) {
            Add-Error "Broken AGENTS path: $path"
        }
    }
    if ($scannedText -notmatch 'frontend-backend-integration') {
        Add-Error "AGENTS.md does not route frontend-backend-integration"
    }
}

# 2. Live harness directories must not contain V1 spec drafts.
$liveSpecs = Get-ChildItem -LiteralPath $harness -Recurse -File -Filter '*-spec.md' |
    Where-Object { $_.FullName -notmatch '\\archive\\' -and $_.FullName -notmatch '\\\.zread\\' }
foreach ($file in $liveSpecs) {
    Add-Error "Live spec draft found: $($file.FullName)"
}

# 3. Skills must be flat and every skill must have SKILL.md.
if (Test-Path -LiteralPath (Join-Path $harness 'skills\skills')) {
    Add-Error "Nested skills/skills directory still exists"
}
$skillRoot = Join-Path $harness 'skills'
if (Test-Path -LiteralPath $skillRoot) {
    foreach ($dir in (Get-ChildItem -LiteralPath $skillRoot -Directory)) {
        if (-not (Test-Path -LiteralPath (Join-Path $dir.FullName 'SKILL.md'))) {
            Add-Error "Skill directory has no SKILL.md: $($dir.Name)"
        }
    }
}

# 4. Active plans must not be marked completed.
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

# 5. zread output must not live inside .harness.
if (Test-Path -LiteralPath (Join-Path $harness '.zread')) {
    Add-Error ".harness/.zread should be moved to docs/zread/harness"
}

# 6. AGENTS should stay a lean entry file.
$agentsLines = (Get-Content -Encoding UTF8 $agents).Count
if ($agentsLines -gt 120) {
    Add-Warning "AGENTS.md has $agentsLines lines; keep near 100"
}

# 7. State artifacts must exist and feature status must respect WIP=1.
$progress = Join-Path $harness 'PROGRESS.md'
if (-not (Test-Path -LiteralPath $progress)) {
    Add-Error "Missing .harness/PROGRESS.md"
}
$featureList = Join-Path $harness 'changes\active\feature-list.json'
if (-not (Test-Path -LiteralPath $featureList)) {
    Add-Error "Missing changes/active/feature-list.json"
}
else {
    try {
        $features = Get-Content -Raw -Encoding UTF8 $featureList | ConvertFrom-Json
        $validStatuses = @('todo', 'in_progress', 'ready_for_review', 'committed', 'pushed', 'merged', 'blocked', 'done')
        foreach ($feature in $features.features) {
            if ($validStatuses -notcontains $feature.status) {
                Add-Error "Invalid feature status: $($feature.id) -> $($feature.status)"
            }
            if ($feature.plan) {
                $planPath = Join-Path $root ($feature.plan -replace '^\./', '')
                if (-not (Test-Path -LiteralPath $planPath)) {
                    Add-Error "Broken feature plan link: $($feature.plan)"
                }
            }
        }
        $inProgress = @($features.features | Where-Object { $_.status -eq 'in_progress' }).Count
        if ($inProgress -gt $features.wip_limit) {
            Add-Error "WIP exceeded: $inProgress in_progress, wip_limit=$($features.wip_limit)"
        }
        $validPushStatuses = @('none', 'local', 'pushed', 'merged')
        foreach ($feature in $features.features) {
            if ($feature.push_status -and ($validPushStatuses -notcontains $feature.push_status)) {
                Add-Error "Invalid push_status: $($feature.id) -> $($feature.push_status)"
            }
            if ($feature.status -in @('committed', 'pushed', 'merged') -and -not $feature.commit) {
                Add-Error "Feature $($feature.id) status $($feature.status) requires commit"
            }
            if ($null -eq $feature.owner -or $feature.owner -eq '') {
                Add-Warning "Feature $($feature.id) has no owner"
            }
            if ($feature.history) {
                foreach ($entry in $feature.history) {
                    if (-not $entry.status -or -not $entry.at -or -not $entry.by) {
                        Add-Error "Feature $($feature.id) history entry requires status/at/by"
                    }
                    if ($entry.status -and ($validStatuses -notcontains $entry.status)) {
                        Add-Error "Invalid history status: $($feature.id) -> $($entry.status)"
                    }
                }
            }
        }
    }
    catch {
        Add-Error "feature-list.json is not valid JSON: $($_.Exception.Message)"
    }
}

# 7.1 Git repository checks.
$gitRepo = $false
if (Get-Command git -ErrorAction SilentlyContinue) {
    $previousEap = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    & git rev-parse --is-inside-work-tree 2>&1 | Out-Null
    $gitRepo = ($LASTEXITCODE -eq 0)
    $ErrorActionPreference = $previousEap
}
if ($gitRepo) {
    $previousEap = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $diffCheck = & git diff --check 2>&1
    if ($LASTEXITCODE -ne 0) {
        Add-Error "git diff --check failed: $diffCheck"
    }
    $porcelain = @(& git status --porcelain)
    if ($porcelain.Count -gt 0) {
        Add-Warning "$($porcelain.Count) uncommitted path(s) present (git status)"
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
        if ($features.git_sync -and -not $features.git_sync.enabled) {
            Add-Warning "git repo detected but git_sync.enabled is false"
        }
    }
    $ErrorActionPreference = $previousEap
}
elseif ($features -and $features.git_sync -and $features.git_sync.enabled) {
    Add-Warning "git_sync.enabled is true but not a git repository"
}
else {
    Write-Host "Git sync checks skipped: not a git repository"
}

# 7.2 PROGRESS and feature-list consistency.
if ((Test-Path -LiteralPath $progress) -and (Test-Path -LiteralPath $featureList) -and $features) {
    $progressText = Get-Content -Raw -Encoding UTF8 $progress
    if ($features.updated_at -and $progressText -notmatch [regex]::Escape($features.updated_at)) {
        Add-Warning "PROGRESS.md does not contain feature-list updated_at $($features.updated_at)"
    }
    $inProgressIds = @($features.features | Where-Object { $_.status -eq 'in_progress' } | ForEach-Object { $_.id })
    foreach ($id in $inProgressIds) {
        if ($progressText -notmatch [regex]::Escape($id)) {
            Add-Warning "PROGRESS.md does not mention in_progress feature $id"
        }
    }
}

# 8. Unified check, contracts, and templates must exist.
$checkScript = Join-Path $root 'script\check.ps1'
if (-not (Test-Path -LiteralPath $checkScript)) {
    Add-Error "Missing script/check.ps1"
}
$gitWorkflow = Join-Path $harness 'rules\git-workflow.md'
if (-not (Test-Path -LiteralPath $gitWorkflow)) {
    Add-Error "Missing rules/git-workflow.md"
}
$syncChanges = Join-Path $root 'script\sync-changes.ps1'
if (-not (Test-Path -LiteralPath $syncChanges)) {
    Add-Error "Missing script/sync-changes.ps1"
}
$installHooks = Join-Path $root 'script\install-hooks.ps1'
if (-not (Test-Path -LiteralPath $installHooks)) {
    Add-Error "Missing script/install-hooks.ps1"
}
$initContract = Join-Path $harness 'init-contract.md'
if (-not (Test-Path -LiteralPath $initContract)) {
    Add-Error "Missing .harness/init-contract.md"
}
$toolAccess = Join-Path $harness 'rules\tool-access.md'
if (-not (Test-Path -LiteralPath $toolAccess)) {
    Add-Error "Missing rules/tool-access.md"
}
$requiredTemplates = @(
    'PROGRESS.md.template',
    'feature-list.json.template',
    'init-contract.md.template',
    'session-handoff.md.template',
    'commit-message.md.template',
    'pr-description.md.template',
    'pipeline-task-card.md.template',
    'pipeline-report.md.template',
    'pipeline-handoff.md.template'
)
foreach ($template in $requiredTemplates) {
    if (-not (Test-Path -LiteralPath (Join-Path $harness "templates\$template"))) {
        Add-Error "Missing template: $template"
    }
}

# 8.1 Codex-native harness artifacts.
$codexDir = Join-Path $root '.codex'
if (-not (Test-Path -LiteralPath (Join-Path $codexDir 'config.toml'))) {
    Add-Error "Missing .codex/config.toml"
}
if (-not (Test-Path -LiteralPath (Join-Path $codexDir 'README.md'))) {
    Add-Error "Missing .codex/README.md"
}
$sourceSkills = Join-Path $harness 'skills'
$codexSkills = Join-Path $codexDir 'skills'
if (Test-Path -LiteralPath $sourceSkills) {
    foreach ($dir in (Get-ChildItem -LiteralPath $sourceSkills -Directory)) {
        $targetSkill = Join-Path $codexSkills ($dir.Name + '\SKILL.md')
        if (-not (Test-Path -LiteralPath $targetSkill)) {
            Add-Error "Codex skill not synced: $($dir.Name)"
        }
        else {
            $sourceHash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $dir.FullName 'SKILL.md')).Hash
            $targetHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $targetSkill).Hash
            if ($sourceHash -ne $targetHash) {
                Add-Error "Codex skill out of sync: $($dir.Name)"
            }
        }
    }
}
$codexArtifacts = @(
    (Join-Path $root 'harness-template\AGENTS.md.template'),
    (Join-Path $root 'harness-template\README.md'),
    (Join-Path $root 'script\harness-init.ps1'),
    (Join-Path $root 'script\sync-skills.ps1'),
    (Join-Path $root 'benchmark\README.md')
)
foreach ($file in $codexArtifacts) {
    if (-not (Test-Path -LiteralPath $file)) {
        Add-Error "Missing Codex harness artifact: $file"
    }
}

# 8.2 Desktop multi-agent pipeline validation.
$validPipelineStatuses = @('not_started', 'running', 'blocked', 'done')
$validStageStatuses = @('queued', 'running', 'passed', 'failed', 'skipped')

$desktopPipeline = Join-Path $harness 'pipelines\desktop-pipeline.json'
$pipelineHandoffTemplate = Join-Path $harness 'templates\pipeline-handoff.md.template'
$pipelineHandoffExample = Join-Path $harness 'templates\pipeline-handoff.example.md'
$pipelineStateExample = Join-Path $harness 'templates\pipeline-state.example.json'
foreach ($artifact in @($desktopPipeline, $pipelineHandoffTemplate, $pipelineHandoffExample, $pipelineStateExample)) {
    if (-not (Test-Path -LiteralPath $artifact)) {
        Add-Error "Missing desktop pipeline artifact: $artifact"
    }
}

if (Test-Path -LiteralPath $pipelineHandoffTemplate) {
    $handoffText = Get-Content -Raw -Encoding UTF8 $pipelineHandoffTemplate
    foreach ($placeholder in @('{{feature_id}}', '{{stage}}', '{{conclusion}}', '{{next_stage_contract}}')) {
        if (-not $handoffText.Contains($placeholder)) {
            Add-Error "pipeline-handoff.md.template missing placeholder: $placeholder"
        }
    }
}

$pipelineConfig = $null
if (Test-Path -LiteralPath $desktopPipeline) {
    try {
        $pipelineConfig = Get-Content -Raw -Encoding UTF8 $desktopPipeline | ConvertFrom-Json
        if ($pipelineConfig.schema_version -ne '1.0') {
            Add-Error "desktop-pipeline.json schema_version must be 1.0"
        }
        $stageIds = @()
        foreach ($stage in $pipelineConfig.stages) {
            if ($stageIds -contains $stage.id) {
                Add-Error "Duplicate pipeline stage id: $($stage.id)"
            }
            $stageIds += $stage.id
            if (-not $stage.role) {
                Add-Error "Pipeline stage $($stage.id) missing role"
            }
            else {
                $roleFile = Join-Path $harness "agents\pipeline\$($stage.role).md"
                if (-not (Test-Path -LiteralPath $roleFile)) {
                    Add-Error "Missing role contract for $($stage.id): $roleFile"
                }
            }
            if (-not $stage.gate) {
                Add-Error "Pipeline stage $($stage.id) missing gate"
            }
            else {
                $gateFile = ($stage.gate -split ' ')[0]
                $gatePath = Join-Path $root ($gateFile -replace '^\./', '')
                if (-not (Test-Path -LiteralPath $gatePath)) {
                    Add-Error "Pipeline stage $($stage.id) gate file missing: $gateFile"
                }
            }
            if ($stage.max_attempts -lt 1) {
                Add-Error "Pipeline stage $($stage.id) max_attempts must be >= 1"
            }
            foreach ($dep in $stage.depends_on) {
                if ($dep -eq $stage.id) {
                    Add-Error "Pipeline stage $($stage.id) depends on itself"
                }
                elseif (($pipelineConfig.stages | Where-Object { $_.id -eq $dep }).Count -eq 0) {
                    Add-Error "Pipeline stage $($stage.id) has unknown dependency: $dep"
                }
            }
        }
        if ($stageIds.Count -eq 0) {
            Add-Error "desktop-pipeline.json has no stages"
        }
        else {
            # Reject dependency cycles with a simple topological check.
            $resolved = @()
            $remaining = @($stageIds)
            while ($remaining.Count -gt 0) {
                $progress = $false
                foreach ($id in @($remaining)) {
                    $stage = $pipelineConfig.stages | Where-Object { $_.id -eq $id }
                    $depsOk = $true
                    foreach ($dep in $stage.depends_on) {
                        if ($resolved -notcontains $dep) {
                            $depsOk = $false
                            break
                        }
                    }
                    if ($depsOk) {
                        $resolved += $id
                        $remaining = @($remaining | Where-Object { $_ -ne $id })
                        $progress = $true
                    }
                }
                if (-not $progress) {
                    Add-Error "Pipeline stages contain a dependency cycle: $($remaining -join ', ')"
                    break
                }
            }
        }
    }
    catch {
        Add-Error "desktop-pipeline.json is not valid JSON: $($_.Exception.Message)"
    }
}

$configStageIds = @()
if ($pipelineConfig) {
    $configStageIds = @($pipelineConfig.stages | ForEach-Object { $_.id })
}

if (Test-Path -LiteralPath $pipelineStateExample) {
    try {
        $exampleState = Get-Content -Raw -Encoding UTF8 $pipelineStateExample | ConvertFrom-Json
        if ($exampleState.schema_version -ne '1.0') {
            Add-Error "pipeline-state.example.json schema_version must be 1.0"
        }
        if ($null -eq $exampleState.stages -or $exampleState.stages.Count -eq 0) {
            Add-Error "pipeline-state.example.json has no stages"
        }
        if ($null -eq $exampleState.journal) {
            Add-Error "pipeline-state.example.json missing journal"
        }
        if ($validPipelineStatuses -notcontains $exampleState.status) {
            Add-Error "pipeline-state.example.json has invalid status: $($exampleState.status)"
        }
        foreach ($stage in $exampleState.stages) {
            if ($validStageStatuses -notcontains $stage.status) {
                Add-Error "pipeline-state.example.json stage $($stage.id) has invalid status: $($stage.status)"
            }
        }
        foreach ($entry in $exampleState.journal) {
            if ($null -eq $entry.seq -or $null -eq $entry.at -or $null -eq $entry.type) {
                Add-Error "pipeline-state.example.json journal entry missing seq/at/type"
            }
        }
        if ($configStageIds.Count -gt 0) {
            $exampleStageIds = @($exampleState.stages | ForEach-Object { $_.id })
            foreach ($id in $configStageIds) {
                if ($exampleStageIds -notcontains $id) {
                    Add-Error "pipeline-state.example.json missing stage: $id"
                }
            }
            foreach ($id in $exampleStageIds) {
                if ($configStageIds -notcontains $id) {
                    Add-Error "pipeline-state.example.json has unknown stage: $id"
                }
            }
        }
    }
    catch {
        Add-Error "pipeline-state.example.json is not valid JSON: $($_.Exception.Message)"
    }
}

$stateDir = Join-Path $harness 'state'
if (Test-Path -LiteralPath $stateDir) {
    foreach ($stateFile in (Get-ChildItem -LiteralPath $stateDir -File -Filter 'pipeline-*.json')) {
        try {
            $state = Get-Content -Raw -Encoding UTF8 $stateFile.FullName | ConvertFrom-Json
            if ($state.schema_version -ne '1.0') {
                Add-Error "Pipeline state schema_version must be 1.0 in $($stateFile.Name)"
            }
            if ($validPipelineStatuses -notcontains $state.status) {
                Add-Error "Invalid pipeline state status in $($stateFile.Name): $($state.status)"
            }
            $stateStageIds = @($state.stages | ForEach-Object { $_.id })
            if ($state.current_stage -and ($stateStageIds -notcontains $state.current_stage)) {
                Add-Error "Pipeline state current_stage not found in $($stateFile.Name): $($state.current_stage)"
            }
            if ($configStageIds.Count -gt 0) {
                foreach ($id in $configStageIds) {
                    if ($stateStageIds -notcontains $id) {
                        Add-Error "Pipeline state missing stage $id in $($stateFile.Name)"
                    }
                }
                foreach ($id in $stateStageIds) {
                    if ($configStageIds -notcontains $id) {
                        Add-Error "Pipeline state has unknown stage $id in $($stateFile.Name)"
                    }
                }
            }
            foreach ($stage in $state.stages) {
                if ($validStageStatuses -notcontains $stage.status) {
                    Add-Error "Invalid stage status in $($stateFile.Name) for $($stage.id): $($stage.status)"
                }
            }
            if ($null -eq $state.journal) {
                Add-Error "Pipeline state missing journal in $($stateFile.Name)"
            }
            else {
                foreach ($entry in $state.journal) {
                    if ($null -eq $entry.seq -or $null -eq $entry.at -or $null -eq $entry.type) {
                        Add-Error "Journal entry missing fields in $($stateFile.Name)"
                    }
                }
            }
            $featureExists = $false
            if ($features) {
                foreach ($feature in $features.features) {
                    if ($feature.id -eq $state.feature_id) {
                        $featureExists = $true
                        break
                    }
                }
            }
            if (-not $featureExists) {
                Add-Error "Pipeline state references unknown feature: $($state.feature_id)"
            }
            if ($featureExists) {
                if ($state.status -eq 'done' -and $feature.pipeline.status -ne 'done') {
                    Add-Error "Pipeline state done but feature-list status is $($feature.pipeline.status) for $($state.feature_id)"
                }
                if ($state.status -eq 'blocked' -and $feature.pipeline.status -ne 'blocked') {
                    Add-Error "Pipeline state blocked but feature-list status is $($feature.pipeline.status) for $($state.feature_id)"
                }
            }
        }
        catch {
            Add-Error "Invalid pipeline state file $($stateFile.Name): $($_.Exception.Message)"
        }
    }
}

if ($features) {
    if ($features.schema_version -ne '1.2') {
        Add-Error "feature-list schema_version must be 1.2"
    }
    foreach ($feature in $features.features) {
        if ($null -eq $feature.pipeline) {
            Add-Error "Feature $($feature.id) missing pipeline block (schema 1.2)"
        }
        elseif ($validPipelineStatuses -notcontains $feature.pipeline.status) {
            Add-Error "Feature $($feature.id) has invalid pipeline.status: $($feature.pipeline.status)"
        }
    }
}

# 9. Tech-debt main list must not contain resolved rows; closed rows live in section 7.
$techDebt = Join-Path $harness 'changes\tech-debt-tracker.md'
if (Test-Path -LiteralPath $techDebt) {
    $inMainList = $false
    foreach ($line in (Get-Content -Encoding UTF8 $techDebt)) {
        if ($line -match '^## 5\.') {
            $inMainList = $true
        }
        elseif ($line -match '^## 6\.') {
            $inMainList = $false
        }
        elseif ($inMainList -and $line -match '^\| TD-\d+ .*\| resolved \|') {
            Add-Error "Resolved tech debt still in main list: $line"
        }
    }
}

# 10.1 Completed index must exist and links must resolve.
$completedIndex = Join-Path $harness 'changes\completed\INDEX.md'
if (-not (Test-Path -LiteralPath $completedIndex)) {
    Add-Error "Missing changes/completed/INDEX.md"
}
else {
    $indexText = Get-Content -Raw -Encoding UTF8 $completedIndex
    $indexLinks = [regex]::Matches($indexText, '\]\(([^\)]+\.md)\)')
    foreach ($match in $indexLinks) {
        $relative = $match.Groups[1].Value
        if ($relative.StartsWith('completed/')) {
            $relative = $relative.Substring('completed/'.Length)
        }
        $candidate = Join-Path (Split-Path $completedIndex) $relative
        if (-not (Test-Path -LiteralPath $candidate)) {
            Add-Error "Broken completed INDEX link: $($match.Groups[1].Value)"
        }
    }
}

# 11. Large hand-written docs are a warning so they can be split on demand.
$largeDocs = Get-ChildItem -LiteralPath (Join-Path $harness 'wiki'), (Join-Path $harness 'changes') -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Length -gt 40KB -and $_.Extension -ne '.html' }
foreach ($file in $largeDocs) {
    Add-Warning "Large doc ($([math]::Round($file.Length / 1KB, 1)) KB): $($file.FullName)"
}

# 12. zread editor state should not be kept.
$obsidian = Get-ChildItem -LiteralPath (Join-Path $root 'docs\zread'), (Join-Path $root '.zread') -Recurse -Directory -Filter '.obsidian' -ErrorAction SilentlyContinue
foreach ($dir in $obsidian) {
    Add-Warning "Obsidian editor state found: $($dir.FullName)"
}

Write-Host "Harness check: $($errors.Count) error(s), $($warnings.Count) warning(s)"
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

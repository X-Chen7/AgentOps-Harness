# Runs the Codex CLI once with a prompt file and captures its output.

param(
    [Parameter(Mandatory = $true)][string]$PromptFile,
    [Parameter(Mandatory = $true)][string]$Root,
    [Parameter(Mandatory = $true)][string]$LogFile,
    [Parameter(Mandatory = $true)][string]$LastMessageFile,
    [int]$TimeoutSeconds = 900,
    [string]$ReasoningEffort = '',
    [string]$Sandbox = 'workspace-write'
)

$ErrorActionPreference = 'Stop'

$codex = Get-Command codex -ErrorAction SilentlyContinue
if ($null -eq $codex) {
    [Console]::Error.WriteLine('codex CLI not found. Please install it and try again.')
    exit 1
}

$prompt = Get-Content -Raw -Encoding UTF8 -LiteralPath $PromptFile

$logDir = Split-Path -Parent $LogFile
if ($logDir) {
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
}

$messageDir = Split-Path -Parent $LastMessageFile
if ($messageDir) {
    New-Item -ItemType Directory -Force -Path $messageDir | Out-Null
}

[Console]::Error.WriteLine("[codex-executor] starting codex exec...")
$job = Start-Job -ScriptBlock {
    param($promptText, $root, $lastMessageFile, $logFile, $reasoningEffort, $sandbox)
    $codexArgs = @('exec', '--skip-git-repo-check', '-C', $root, '-o', $lastMessageFile, '--ephemeral', '--color', 'never', '-s', $sandbox)
    if ($reasoningEffort) {
        $codexArgs += @('-c', "model_reasoning_effort=$reasoningEffort")
    }
    $codexArgs += $promptText
    & codex @codexArgs 2>&1 | Tee-Object -FilePath $logFile
    "HARNESS_CODEX_EXIT=$LASTEXITCODE"
} -ArgumentList $prompt, $Root, $LastMessageFile, $LogFile, $ReasoningEffort, $Sandbox

$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
while (-not (Wait-Job $job -Timeout 15)) {
    $elapsed = [int]$stopwatch.Elapsed.TotalSeconds
    $logSize = 0
    if (Test-Path -LiteralPath $LogFile) {
        $logSize = (Get-Item -LiteralPath $LogFile).Length
    }
    [Console]::Error.WriteLine("[codex-executor] still running ${elapsed}s, log size $([math]::Round($logSize / 1KB, 1)) KB")
    if (Test-Path -LiteralPath $LogFile) {
        $lastLine = Get-Content -LiteralPath $LogFile -Tail 1 -ErrorAction SilentlyContinue
        if ($lastLine) {
            $lastActivity = ($lastLine | Out-String).Trim()
            if ($lastActivity.Length -gt 120) {
                $lastActivity = $lastActivity.Substring(0, 120)
            }
            [Console]::Error.WriteLine("[codex-executor] last: $lastActivity")
        }
    }
    if ($elapsed -ge $TimeoutSeconds) {
        break
    }
}
$stopwatch.Stop()

if ($job.State -ne 'Completed') {
    Stop-Job $job
    Remove-Job $job -Force
    [Console]::Error.WriteLine("[codex-executor] codex exec timed out after $($stopwatch.Elapsed.TotalSeconds.ToString('0')) seconds; see $LogFile")
    exit 124
}

$jobOutput = Receive-Job $job
Remove-Job $job -Force
$exitCode = -1
foreach ($line in @($jobOutput)) {
    if ($line -match '^HARNESS_CODEX_EXIT=(-?\d+)$') {
        $exitCode = [int]$Matches[1]
    }
}

[Console]::Error.WriteLine("[codex-executor] codex exec finished with exit code $exitCode after $($stopwatch.Elapsed.TotalSeconds.ToString('0')) seconds")

if (-not (Test-Path -LiteralPath $LastMessageFile -PathType Leaf)) {
    Write-Warning 'Last message file was not created.'
}

Add-Content -LiteralPath $LogFile -Encoding UTF8 -Value "[codex-executor] exit code: $exitCode"

exit $exitCode

# run_evaluation.ps1 - Research-layer Evaluation Orchestration
# P0-5: Execution Authenticity Gate + Artifact Integrity Gate -> e2e_metrics
#
# Flow:
#   1. execution_gate.py checks execution authenticity and artifact integrity
#   2. INVALID (exit 2) -> execution not authentic, skip capability scoring
#   3. PASS (exit 0)    -> run e2e_metrics for 8-dimension capability scoring
#   4. FAIL (exit 1)    -> warning but still score (with caution)
#
# Usage:
#   .\run_evaluation.ps1 -Project projects/p151-2024a
#   .\run_evaluation.ps1 -Project projects/p151-2024a -GtPath gt.json -ResponsePath response.json

param(
    [Parameter(Mandatory=$true)]
    [string]$Project,

    [string]$GtPath = "",
    [string]$ResponsePath = "",
    [string]$OutputDir = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
$GateScript = Join-Path $PSScriptRoot "execution_gate.py"
$MetricsRunner = Join-Path $PSScriptRoot "_metrics_runner.py"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

# Resolve project path
if (-not [System.IO.Path]::IsPathRooted($Project)) {
    $ProjectPath = Join-Path $RepoRoot $Project
} else {
    $ProjectPath = $Project
}
$ProjectName = Split-Path $ProjectPath -Leaf

if (-not (Test-Path $ProjectPath)) {
    Write-Error "Project directory not found: $ProjectPath"
    exit 1
}

# Output directory
if ($OutputDir) {
    if (-not [System.IO.Path]::IsPathRooted($OutputDir)) {
        $OutputDir = Join-Path $RepoRoot $OutputDir
    }
} else {
    $RunsDir = Join-Path $PSScriptRoot "runs"
    $OutputDir = Join-Path $RunsDir "$ProjectName`_$Timestamp"
}
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$GateReport = Join-Path $OutputDir "execution_gate.json"
$MetricsReport = Join-Path $OutputDir "e2e_metrics.json"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Evaluation Orchestration (P0-5)" -ForegroundColor Cyan
Write-Host " Project : $ProjectName" -ForegroundColor Cyan
Write-Host " Output  : $OutputDir" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ---------------------------------------------------------------
# Step 1: Execution Authenticity and Artifact Integrity Gate
# ---------------------------------------------------------------
Write-Host "[Step 1] Running Execution Gate..." -ForegroundColor Yellow

$GateStdout = Join-Path $OutputDir "gate_stdout.txt"

& py -3.12 $GateScript --project $ProjectPath --json $GateReport *> $GateStdout
$GateExit = $LASTEXITCODE

Write-Host "  Gate exit code: $GateExit"

# Parse gate report for overall verdict
$GateVerdict = "UNKNOWN"
if (Test-Path $GateReport) {
    try {
        $GateData = Get-Content $GateReport -Raw -Encoding UTF8 | ConvertFrom-Json
        $GateVerdict = $GateData.overall
    } catch {
        Write-Warning "Cannot parse gate report: $_"
    }
}
Write-Host "  Gate verdict : $GateVerdict"
Write-Host ""

# ---------------------------------------------------------------
# Step 2: Decide whether to run e2e_metrics based on gate result
# ---------------------------------------------------------------
if ($GateExit -eq 2 -or $GateVerdict -eq "INVALID") {
    Write-Host "========================================" -ForegroundColor Red
    Write-Host " EXECUTION INVALID - skip capability scoring" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Gate report: $GateReport"
    Write-Host ""
    Write-Host "Possible causes:" -ForegroundColor Yellow
    Write-Host "  - artifact payload is empty (template init, no real execution)"
    Write-Host "  - no files in code/output/artifacts directories"
    Write-Host "  - latency below threshold (< 1s)"
    Write-Host "  - model_provider/model_version is null"
    Write-Host ""

    $SkipReport = [ordered]@{
        project = $ProjectName
        evaluated_at = (Get-Date).ToString("o")
        gate_verdict = $GateVerdict
        gate_exit_code = $GateExit
        status = "SKIPPED_INVALID_EXECUTION"
        message = "Execution not authentic, skip capability scoring"
        gate_report = $GateReport
    }
    $SkipReport | ConvertTo-Json -Depth 10 | Set-Content -Path (Join-Path $OutputDir "evaluation_skipped.json") -Encoding UTF8

    exit 2
}

if ($GateExit -eq 1 -or $GateVerdict -eq "FAIL") {
    Write-Warning "Execution Gate returned FAIL (exit=1), still scoring but interpret with caution"
    Write-Host ""
}

# PASS or FAIL: run e2e_metrics
Write-Host "[Step 2] Running e2e_metrics (8-dimension capability scoring)..." -ForegroundColor Yellow

# Pass paths via environment variables to Python runner
$env:EVAL_PROJECT = $ProjectPath
$env:EVAL_REPO = $RepoRoot
$env:EVAL_GT = $GtPath
$env:EVAL_RESPONSE = $ResponsePath
$env:EVAL_OUTPUT = $MetricsReport

& py -3.12 $MetricsRunner
$MetricsExit = $LASTEXITCODE

Write-Host ""
if ($MetricsExit -eq 0) {
    Write-Host "========================================" -ForegroundColor Green
    Write-Host " EVALUATION COMPLETE" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  Gate report   : $GateReport"
    Write-Host "  Metrics JSON  : $MetricsReport"
    Write-Host "  Metrics MD    : $($MetricsReport -replace '\.json$', '.md')"
    Write-Host ""
} else {
    Write-Error "e2e_metrics failed (exit=$MetricsExit)"
    exit 1
}

exit 0

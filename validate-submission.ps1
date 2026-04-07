# validate-submission.ps1 — OpenEnv Submission Validator (Windows)
#
# Checks that your HF Space is live, Docker image builds, and openenv validate passes.
#
# Prerequisites:
#   - Docker Desktop for Windows
#   - Python 3.11+ with openenv-core: pip install openenv-core
#   - PowerShell 5.1+ (pre-installed on Windows)
#
# Run:
#   .\validate-submission.ps1 -PingUrl "https://your-space.hf.space" [-RepoDir ".\bom-normalizer"]
#
# Examples:
#   .\validate-submission.ps1 -PingUrl "https://tani-prog-bom-normalizer.hf.space"
#   .\validate-submission.ps1 -PingUrl "https://tani-prog-bom-normalizer.hf.space" -RepoDir ".\bom-normalizer"
#

param(
    [Parameter(Mandatory=$true)]
    [string]$PingUrl,
    
    [Parameter(Mandatory=$false)]
    [string]$RepoDir = "."
)

$ErrorActionPreference = "Stop"
$DOCKER_BUILD_TIMEOUT = 600

# Colors
function Write-Pass { param($msg) Write-Host "[PASSED]" -ForegroundColor Green -NoNewline; Write-Host " -- $msg" }
function Write-Fail { param($msg) Write-Host "[FAILED]" -ForegroundColor Red -NoNewline; Write-Host " -- $msg" }
function Write-Hint { param($msg) Write-Host "  Hint: " -ForegroundColor Yellow -NoNewline; Write-Host $msg }
function Write-Log  { param($msg) Write-Host "[$((Get-Date).ToString('HH:mm:ss'))]" -NoNewline; Write-Host " $msg" }

function Stop-Validation {
    param($step)
    Write-Host ""
    Write-Host "Validation stopped at $step." -ForegroundColor Red -BackgroundColor Black
    Write-Host "Fix the above before continuing." -ForegroundColor Red
    exit 1
}

# Validate inputs
if (-not (Test-Path $RepoDir)) {
    Write-Host "Error: directory '$RepoDir' not found" -ForegroundColor Red
    exit 1
}

$RepoDir = Resolve-Path $RepoDir
$PingUrl = $PingUrl.TrimEnd('/')

$PASS = 0

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  OpenEnv Submission Validator" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Log "Repo:     $RepoDir"
Write-Log "Ping URL: $PingUrl"
Write-Host ""

# Step 1: Ping HF Space
Write-Log "Step 1/3: Pinging HF Space ($PingUrl/reset?task_id=easy) ..."

try {
    $response = Invoke-WebRequest -Uri "$PingUrl/reset?task_id=easy" -Method POST `
        -ContentType "application/json" -Body '{}' `
        -TimeoutSec 30 -UseBasicParsing -ErrorAction Stop
    
    if ($response.StatusCode -eq 200) {
        Write-Pass "HF Space is live and responds to /reset"
        $PASS++
    } else {
        Write-Fail "HF Space /reset returned HTTP $($response.StatusCode) (expected 200)"
        Write-Hint "Make sure your Space is running and the URL is correct."
        Write-Hint "Try opening $PingUrl in your browser first."
        Stop-Validation "Step 1"
    }
} catch {
    Write-Fail "HF Space not reachable (connection failed or timed out)"
    Write-Hint "Check your network connection and that the Space is running."
    Write-Hint "Error: $($_.Exception.Message)"
    Stop-Validation "Step 1"
}

# Step 2: Docker Build
Write-Log "Step 2/3: Running docker build ..."

# Check if Docker is installed
try {
    $dockerVersion = docker --version 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Docker not found" }
} catch {
    Write-Fail "docker command not found"
    Write-Hint "Install Docker Desktop: https://docs.docker.com/desktop/install/windows-install/"
    Stop-Validation "Step 2"
}

# Find Dockerfile
$DockerfilePath = $null
if (Test-Path "$RepoDir\Dockerfile") {
    $DockerfilePath = $RepoDir
} elseif (Test-Path "$RepoDir\server\Dockerfile") {
    $DockerfilePath = "$RepoDir\server"
} else {
    Write-Fail "No Dockerfile found in repo root or server\ directory"
    Stop-Validation "Step 2"
}

Write-Log "  Found Dockerfile in $DockerfilePath"

# Build Docker image with timeout
$buildJob = Start-Job -ScriptBlock {
    param($path)
    docker build $path 2>&1
} -ArgumentList $DockerfilePath

$buildCompleted = Wait-Job $buildJob -Timeout $DOCKER_BUILD_TIMEOUT
$buildOutput = Receive-Job $buildJob

if ($buildCompleted -and $buildJob.State -eq "Completed") {
    Write-Pass "Docker build succeeded"
    $PASS++
} else {
    Write-Fail "Docker build failed (timeout=${DOCKER_BUILD_TIMEOUT}s)"
    if ($buildOutput) {
        $buildOutput | Select-Object -Last 20 | ForEach-Object { Write-Host $_ }
    }
    Stop-Job $buildJob -ErrorAction SilentlyContinue
    Remove-Job $buildJob -ErrorAction SilentlyContinue
    Stop-Validation "Step 2"
}

Remove-Job $buildJob -ErrorAction SilentlyContinue

# Step 3: OpenEnv Validate
Write-Log "Step 3/3: Running openenv validate ..."

# Check if openenv is installed
try {
    $openenvVersion = openenv --version 2>&1
    if ($LASTEXITCODE -ne 0) { throw "openenv not found" }
} catch {
    Write-Fail "openenv command not found"
    Write-Hint "Install it: pip install openenv-core"
    Stop-Validation "Step 3"
}

# Run openenv validate
Push-Location $RepoDir
try {
    $validateOutput = openenv validate 2>&1
    $validateExitCode = $LASTEXITCODE
    
    if ($validateExitCode -eq 0) {
        Write-Pass "openenv validate passed"
        $PASS++
        if ($validateOutput) {
            Write-Log "  $validateOutput"
        }
    } else {
        Write-Fail "openenv validate failed"
        if ($validateOutput) {
            $validateOutput | ForEach-Object { Write-Host $_ }
        }
        Stop-Validation "Step 3"
    }
} finally {
    Pop-Location
}

# Success!
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  All 3/3 checks passed!" -ForegroundColor Green
Write-Host "  Your submission is ready to submit." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

exit 0

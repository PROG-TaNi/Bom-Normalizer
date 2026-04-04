# BOM Normalizer - Inference Runner for Windows
# This script helps you run inference with proper environment setup

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "BOM Normalizer - Inference Runner" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Get HuggingFace token
Write-Host "Step 1: Configuration" -ForegroundColor Yellow
Write-Host ""
$hfToken = Read-Host "Enter your HuggingFace API token" -AsSecureString
$hfTokenPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($hfToken))
Write-Host ""

# Step 2: Set environment variables
Write-Host "Step 2: Setting environment variables..." -ForegroundColor Yellow
$env:HF_TOKEN = $hfTokenPlain
$env:API_BASE_URL = "https://router.huggingface.co/v1"
$env:MODEL_NAME = "meta-llama/Llama-3.3-70B-Instruct"
$env:ENV_URL = "http://localhost:7860"
Write-Host "✓ Environment configured" -ForegroundColor Green
Write-Host ""

# Step 3: Check if server is running
Write-Host "Step 3: Checking if backend server is running..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:7860/health" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "✓ Server is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Server is not running!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please start the server first:" -ForegroundColor Yellow
    Write-Host "  python -m uvicorn bom_normalizer.server:app --host 0.0.0.0 --port 7860" -ForegroundColor White
    Write-Host ""
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}
Write-Host ""

# Step 4: Run inference
Write-Host "Step 4: Running inference..." -ForegroundColor Yellow
Write-Host "This will take 10-60 minutes depending on LLM speed" -ForegroundColor Gray
Write-Host ""
Write-Host "Starting inference..." -ForegroundColor Cyan
Write-Host ""

# Run inference and save to file
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outputFile = "inference_results_$timestamp.txt"

python inference.py | Tee-Object -FilePath $outputFile

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Inference Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Results saved to: $outputFile" -ForegroundColor Green
Write-Host ""

# Extract scores
Write-Host "Extracting scores..." -ForegroundColor Yellow
$summary = Select-String -Path $outputFile -Pattern "# Summary:"
if ($summary) {
    Write-Host ""
    Write-Host "SCORES:" -ForegroundColor Cyan
    Write-Host $summary.Line -ForegroundColor Green
    Write-Host ""
    
    # Parse scores
    if ($summary.Line -match "easy=([\d.]+)") {
        $easyScore = $matches[1]
        Write-Host "Easy:    $easyScore (target: 0.80+)" -ForegroundColor $(if ([double]$easyScore -ge 0.80) { "Green" } else { "Yellow" })
    }
    if ($summary.Line -match "medium=([\d.]+)") {
        $mediumScore = $matches[1]
        Write-Host "Medium:  $mediumScore (target: 0.70+)" -ForegroundColor $(if ([double]$mediumScore -ge 0.70) { "Green" } else { "Yellow" })
    }
    if ($summary.Line -match "hard=([\d.]+)") {
        $hardScore = $matches[1]
        Write-Host "Hard:    $hardScore (target: 0.50+)" -ForegroundColor $(if ([double]$hardScore -ge 0.50) { "Green" } else { "Yellow" })
    }
    if ($summary.Line -match "average=([\d.]+)") {
        $avgScore = $matches[1]
        Write-Host "Average: $avgScore (target: 0.67+)" -ForegroundColor $(if ([double]$avgScore -ge 0.67) { "Green" } else { "Yellow" })
    }
} else {
    Write-Host "Could not extract scores from output" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "NEXT STEPS:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Update README.md with these scores" -ForegroundColor Yellow
Write-Host "   Find 'Baseline Performance' table (line ~147)" -ForegroundColor White
Write-Host "   Replace estimated scores with actual scores above" -ForegroundColor White
Write-Host ""
Write-Host "2. Commit and push changes:" -ForegroundColor Yellow
Write-Host "   git add README.md" -ForegroundColor White
Write-Host "   git commit -m 'Update baseline scores'" -ForegroundColor White
Write-Host "   git push hf main" -ForegroundColor White
Write-Host ""
Write-Host "3. Submit to competition!" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# BOM Normalizer - Deployment Script for Windows
# Run this script to prepare for HuggingFace deployment

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "BOM Normalizer - Deployment Helper" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if git is initialized
Write-Host "Step 1: Checking Git repository..." -ForegroundColor Yellow
if (Test-Path ".git") {
    Write-Host "✓ Git repository already initialized" -ForegroundColor Green
} else {
    Write-Host "✓ Initializing Git repository..." -ForegroundColor Green
    git init
}
Write-Host ""

# Step 2: Add all files
Write-Host "Step 2: Adding files to Git..." -ForegroundColor Yellow
git add .
Write-Host "✓ Files added" -ForegroundColor Green
Write-Host ""

# Step 3: Commit
Write-Host "Step 3: Creating commit..." -ForegroundColor Yellow
git commit -m "Competition submission - BOM Normalizer"
Write-Host "✓ Commit created" -ForegroundColor Green
Write-Host ""

# Step 4: Get HuggingFace username
Write-Host "Step 4: HuggingFace Configuration" -ForegroundColor Yellow
Write-Host ""
$username = Read-Host "Enter your HuggingFace username"
Write-Host ""

# Step 5: Add remote
Write-Host "Step 5: Adding HuggingFace remote..." -ForegroundColor Yellow
$remoteUrl = "https://huggingface.co/spaces/$username/bom-normalizer"
Write-Host "Remote URL: $remoteUrl" -ForegroundColor Cyan

# Check if remote already exists
$existingRemote = git remote get-url hf 2>$null
if ($existingRemote) {
    Write-Host "Remote 'hf' already exists. Removing..." -ForegroundColor Yellow
    git remote remove hf
}

git remote add hf $remoteUrl
Write-Host "✓ Remote added" -ForegroundColor Green
Write-Host ""

# Step 6: Instructions for pushing
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "NEXT STEPS:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Create Space on HuggingFace:" -ForegroundColor Yellow
Write-Host "   Go to: https://huggingface.co/spaces" -ForegroundColor White
Write-Host "   Click 'Create new Space'" -ForegroundColor White
Write-Host "   Name: bom-normalizer" -ForegroundColor White
Write-Host "   SDK: Docker" -ForegroundColor White
Write-Host "   Hardware: CPU basic" -ForegroundColor White
Write-Host ""
Write-Host "2. Push code to HuggingFace:" -ForegroundColor Yellow
Write-Host "   git push hf main" -ForegroundColor White
Write-Host "   (Use your HF token as password)" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Add HF_TOKEN secret in Space settings:" -ForegroundColor Yellow
Write-Host "   Go to: https://huggingface.co/spaces/$username/bom-normalizer/settings" -ForegroundColor White
Write-Host "   Add secret: HF_TOKEN = your_token" -ForegroundColor White
Write-Host ""
Write-Host "4. Wait for build (5-10 minutes)" -ForegroundColor Yellow
Write-Host ""
Write-Host "5. Verify deployment:" -ForegroundColor Yellow
Write-Host "   curl https://$username-bom-normalizer.hf.space/health" -ForegroundColor White
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Your Space URL will be:" -ForegroundColor Cyan
Write-Host "https://$username-bom-normalizer.hf.space" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Ready to push? Run: git push hf main" -ForegroundColor Yellow
Write-Host ""

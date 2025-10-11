# Validate OpenAI API Key Setup

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  OpenAI API Key Validator" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if docker-compose.yml exists
if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "X docker-compose.yml not found!" -ForegroundColor Red
    Write-Host "  Make sure you're in the Labmate directory" -ForegroundColor Yellow
    exit 1
}

# Read the API key from docker-compose.yml
$composeContent = Get-Content "docker-compose.yml" -Raw
if ($composeContent -match 'OPENAI_API_KEY=([^\s]+)') {
    $apiKey = $matches[1]
    
    Write-Host "[1] Checking API key in docker-compose.yml..." -ForegroundColor Yellow
    
    if ($apiKey -eq "sk-proj-YOUR_API_KEY_HERE_REPLACE_THIS") {
        Write-Host "X API key is still the placeholder!" -ForegroundColor Red
        Write-Host ""
        Write-Host "You need to:" -ForegroundColor Yellow
        Write-Host "  1. Get your key from: https://platform.openai.com/account/api-keys" -ForegroundColor White
        Write-Host "  2. Open docker-compose.yml" -ForegroundColor White
        Write-Host "  3. Replace line 28 with your actual key" -ForegroundColor White
        Write-Host "  4. Save and run: docker compose down && docker compose up -d" -ForegroundColor White
        Write-Host ""
        Write-Host "Read FIX_NOW.md for detailed steps!" -ForegroundColor Green
        exit 1
    }
    
    if ($apiKey.StartsWith("sk-")) {
        Write-Host "OK API key format looks correct (starts with 'sk-')" -ForegroundColor Green
    } else {
        Write-Host "? API key doesn't start with 'sk-' - might be invalid" -ForegroundColor Yellow
    }
    
    Write-Host "  Key: $($apiKey.Substring(0, [Math]::Min(20, $apiKey.Length)))..." -ForegroundColor Gray
} else {
    Write-Host "X Could not find OPENAI_API_KEY in docker-compose.yml" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[2] Checking if containers are running..." -ForegroundColor Yellow
$containers = docker compose ps --format json 2>&1 | ConvertFrom-Json

if ($containers) {
    $running = ($containers | Where-Object { $_.State -eq "running" }).Count
    Write-Host "OK $running containers running" -ForegroundColor Green
    
    if ($running -lt 3) {
        Write-Host "? Expected 3 containers (postgres, backend, frontend)" -ForegroundColor Yellow
        Write-Host "  Run: docker compose up -d" -ForegroundColor White
    }
} else {
    Write-Host "X No containers running" -ForegroundColor Red
    Write-Host "  Run: docker compose up -d" -ForegroundColor White
}

Write-Host ""
Write-Host "[3] Testing API key with OpenAI..." -ForegroundColor Yellow

# Test the API key by trying to call OpenAI
$testResult = docker compose exec -T backend python -c @"
import openai
import os
import sys

openai.api_key = os.getenv('OPENAI_API_KEY')

try:
    # Try to list models (minimal API call)
    models = openai.Model.list()
    print('SUCCESS')
except openai.error.AuthenticationError:
    print('AUTH_ERROR')
    sys.exit(1)
except openai.error.RateLimitError:
    print('QUOTA_EXCEEDED')
    sys.exit(1)
except Exception as e:
    print(f'ERROR: {str(e)}')
    sys.exit(1)
"@ 2>&1

if ($testResult -match "SUCCESS") {
    Write-Host "OK API key is valid and working!" -ForegroundColor Green
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  All Checks Passed!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Your LabMate AI is ready to use!" -ForegroundColor Cyan
    Write-Host "Go to: http://localhost:3000" -ForegroundColor White
    Write-Host ""
} elseif ($testResult -match "AUTH_ERROR") {
    Write-Host "X API key is invalid!" -ForegroundColor Red
    Write-Host ""
    Write-Host "The key you entered is not recognized by OpenAI." -ForegroundColor Yellow
    Write-Host "Please:" -ForegroundColor Yellow
    Write-Host "  1. Double-check the key at: https://platform.openai.com/account/api-keys" -ForegroundColor White
    Write-Host "  2. Make sure you copied the entire key" -ForegroundColor White
    Write-Host "  3. Update docker-compose.yml again" -ForegroundColor White
    Write-Host "  4. Run: docker compose down && docker compose up -d" -ForegroundColor White
    Write-Host ""
} elseif ($testResult -match "QUOTA_EXCEEDED") {
    Write-Host "X API key has exceeded quota (no credits)!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Your API key is valid but has no credits." -ForegroundColor Yellow
    Write-Host "Add credits at: https://platform.openai.com/account/billing" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "? Could not test API key" -ForegroundColor Yellow
    Write-Host "  Error: $testResult" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Make sure:" -ForegroundColor Yellow
    Write-Host "  1. Containers are running: docker compose ps" -ForegroundColor White
    Write-Host "  2. Backend is healthy: docker compose logs backend" -ForegroundColor White
    Write-Host ""
}

Write-Host "For detailed troubleshooting, read FIX_NOW.md" -ForegroundColor Cyan
Write-Host ""


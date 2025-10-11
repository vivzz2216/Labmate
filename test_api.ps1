# Test LabMate AI API

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "  LabMate AI - API Test Script" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Test 1: Health Check
Write-Host "[1] Testing health endpoint..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET
    Write-Host "OK Backend is healthy!" -ForegroundColor Green
    Write-Host "  Response: $($health | ConvertTo-Json)" -ForegroundColor Gray
} catch {
    Write-Host "X Backend health check failed!" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Test 2: Upload a test file (you'll need to have a file to test)
Write-Host "[2] To test file upload:" -ForegroundColor Yellow
Write-Host "  1. Go to http://localhost:3000" -ForegroundColor Gray
Write-Host "  2. Upload your lab assignment DOCX/PDF" -ForegroundColor Gray
Write-Host "  3. If you get a 500 error on analysis, it means:" -ForegroundColor Gray
Write-Host ""

Write-Host "     Possible causes of 500 error:" -ForegroundColor Cyan
Write-Host "     a OpenAI API key has exceeded quota" -ForegroundColor White
Write-Host "     b OpenAI API key is invalid" -ForegroundColor White
Write-Host "     c Model gpt-3.5-turbo is not available" -ForegroundColor White
Write-Host ""

# Test 3: Check if API key is set
Write-Host "[3] Checking OpenAI configuration..." -ForegroundColor Yellow
$logs = docker compose logs backend --tail=100 2>&1 | Out-String

if ($logs -match "OPENAI_API_KEY") {
    Write-Host "OK OpenAI API key environment variable is set" -ForegroundColor Green
} else {
    Write-Host "X OpenAI API key might not be set!" -ForegroundColor Red
}

if ($logs -match "exceeded your current quota") {
    Write-Host "X OpenAI API key has EXCEEDED QUOTA!" -ForegroundColor Red
    Write-Host "  Solution: Update your API key in docker-compose.yml" -ForegroundColor Yellow
} elseif ($logs -match "Incorrect API key") {
    Write-Host "X OpenAI API key is INVALID!" -ForegroundColor Red
    Write-Host "  Solution: Get a valid key from platform.openai.com" -ForegroundColor Yellow
} elseif ($logs -match "does not exist or you do not have access") {
    Write-Host "X Model not accessible with your API key!" -ForegroundColor Red
    Write-Host "  Solution: Change model to gpt-3.5-turbo" -ForegroundColor Yellow
} else {
    Write-Host "? No OpenAI errors found in logs yet" -ForegroundColor Gray
    Write-Host "  The error might appear when you upload a file" -ForegroundColor Gray
}

Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "  Next Steps:" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Update your OpenAI API key:" -ForegroundColor Yellow
Write-Host "   - Open docker-compose.yml" -ForegroundColor Gray
Write-Host "   - Find line 28: OPENAI_API_KEY=..." -ForegroundColor Gray
Write-Host "   - Replace with YOUR key from:" -ForegroundColor Gray
Write-Host "     https://platform.openai.com/account/api-keys" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Make sure you have billing setup:" -ForegroundColor Yellow
Write-Host "   https://platform.openai.com/account/billing" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Restart services:" -ForegroundColor Yellow
Write-Host "   docker compose down" -ForegroundColor Gray
Write-Host "   docker compose up -d" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Test again:" -ForegroundColor Yellow
Write-Host "   Open http://localhost:3000 and upload a file" -ForegroundColor Gray
Write-Host ""


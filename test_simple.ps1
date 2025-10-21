# Test all Labmate API endpoints
Write-Host "`n========== API TESTING ==========" -ForegroundColor Cyan

# 1. Health Check
Write-Host "`n1. Testing /health" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/health"
    Write-Host "   SUCCESS: $($response.status)" -ForegroundColor Green
} catch {
    Write-Host "   FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

# 2. API Health Check
Write-Host "`n2. Testing /api/health" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/health"
    Write-Host "   SUCCESS: $($response.status) - $($response.service)" -ForegroundColor Green
} catch {
    Write-Host "   FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

# 3. Root endpoint  
Write-Host "`n3. Testing / (root)" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/"
    Write-Host "   SUCCESS: $($response.message)" -ForegroundColor Green
} catch {
    Write-Host "   FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

# 4. Login endpoint
Write-Host "`n4. Testing /api/basic-auth/login" -ForegroundColor Yellow
try {
    $body = '{"username":"admin","password":"labmate2024"}'
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/basic-auth/login" `
        -Method POST -ContentType "application/json" -Body $body
    Write-Host "   SUCCESS: User $($response.username) logged in" -ForegroundColor Green
} catch {
    Write-Host "   FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

# 5. Get assignments
Write-Host "`n5. Testing /api/assignments" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/assignments"
    Write-Host "   SUCCESS: Found $($response.Count) assignments" -ForegroundColor Green
} catch {
    Write-Host "   FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n========== TESTS COMPLETE ==========`n" -ForegroundColor Cyan


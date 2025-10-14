# Simple Backend Restart Script
Write-Host "Restarting Backend Server..." -ForegroundColor Cyan

# Kill existing backend process on port 3001
Write-Host "Stopping existing backend process..." -ForegroundColor Yellow
Stop-Process -Id 37836 -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3

# Start backend server
Write-Host "Starting Backend Server on port 3001..." -ForegroundColor Green
Set-Location backend
Start-Process -FilePath "npm" -ArgumentList "start" -NoNewWindow
Set-Location ..

Write-Host "Backend server restart initiated!" -ForegroundColor Green

# Wait and test
Start-Sleep -Seconds 15
Write-Host "Testing backend connection..." -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri "http://localhost:3001/api/health" -Method GET -TimeoutSec 10
    Write-Host "Backend is healthy! Status: $($response.status)" -ForegroundColor Green
} catch {
    Write-Host "Backend health check failed - server may still be starting" -ForegroundColor Yellow
}
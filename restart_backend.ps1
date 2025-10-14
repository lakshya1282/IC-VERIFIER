# Restart Backend Server Script
Write-Host "🔄 Restarting Backend Server..." -ForegroundColor Cyan

# Kill existing backend process (port 3001)
$backendProcess = Get-Process | Where-Object {$_.Id -eq 37836}
if ($backendProcess) {
    Write-Host "🛑 Stopping existing backend process (PID: 37836)..." -ForegroundColor Yellow
    Stop-Process -Id 37836 -Force
    Start-Sleep -Seconds 3
}

# Change to backend directory and restart
Write-Host "🚀 Starting Backend Server on port 3001..." -ForegroundColor Green
Push-Location backend

# Start backend server in background
Start-Process -NoNewWindow -FilePath "npm" -ArgumentList "start" -WindowStyle Hidden

Write-Host "✅ Backend server restart initiated!" -ForegroundColor Green
Write-Host "🌐 Backend should be available at http://localhost:3001" -ForegroundColor Cyan

Pop-Location

Write-Host "`n🔍 Checking backend status in 10 seconds..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Test backend health
try {
    $response = Invoke-RestMethod -Uri "http://localhost:3001/api/health" -Method GET -TimeoutSec 5
    Write-Host "✅ Backend is healthy!" -ForegroundColor Green
    Write-Host "Status: $($response.status)" -ForegroundColor Cyan
} catch {
    Write-Host "⚠️ Backend health check failed - server may still be starting" -ForegroundColor Yellow
}
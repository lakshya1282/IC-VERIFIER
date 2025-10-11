# Stop all IC Verification System services

Write-Host "`n🛑 Stopping all IC Verification System services..." -ForegroundColor Yellow

# Stop Python processes
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Write-Host "   ✅ Stopped Python services" -ForegroundColor Green

# Stop Node.js processes
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Write-Host "   ✅ Stopped Node.js services" -ForegroundColor Green

# Kill processes on specific ports
$ports = @(3000, 3001, 5000, 5001)
foreach ($port in $ports) {
    $process = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
    if ($process) {
        Stop-Process -Id $process -Force -ErrorAction SilentlyContinue
        Write-Host "   ✅ Freed port $port" -ForegroundColor Green
    }
}

Write-Host "`n✅ All services stopped successfully!" -ForegroundColor Green
Write-Host ""
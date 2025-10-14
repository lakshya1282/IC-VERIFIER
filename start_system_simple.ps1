# IC Verification System - Simple Startup Script

Write-Host "🚀 IC Verification System Startup" -ForegroundColor Green
Write-Host "=" * 50

Write-Host "`n🎯 Select System to Start:" -ForegroundColor Yellow
Write-Host "1. Enhanced API Server (Recommended)" -ForegroundColor White
Write-Host "2. Traditional ML API" -ForegroundColor White
Write-Host "3. Full Stack (Backend + Frontend)" -ForegroundColor White
Write-Host "4. Test All Models" -ForegroundColor White

$choice = Read-Host "`nEnter your choice (1-4)"

switch ($choice) {
    "1" {
        Write-Host "`n🚀 Starting Enhanced API Server..." -ForegroundColor Green
        Set-Location "deep-learning-model"
        python enhanced_api_server.py
    }
    
    "2" {
        Write-Host "`n🚀 Starting Traditional ML API..." -ForegroundColor Green
        Set-Location "ml-model"
        python api_server.py
    }
    
    "3" {
        Write-Host "`n🚀 Starting Full Stack Application..." -ForegroundColor Green
        Write-Host "This will open multiple windows..." -ForegroundColor Yellow
        
        # Start ML API in new window
        Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd 'ml-model'; python api_server.py"
        Start-Sleep 2
        
        # Start Backend in new window  
        Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd 'backend'; npm start"
        Start-Sleep 3
        
        # Start Frontend in new window
        Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd 'frontend'; npm start"
        
        Write-Host "✅ All services starting in separate windows..." -ForegroundColor Green
    }
    
    "4" {
        Write-Host "`n🧪 Testing All Models..." -ForegroundColor Green
        
        # Test system components
        python test_enhanced_system.py
        
        Write-Host "`n🤖 Testing Traditional ML..." -ForegroundColor Yellow
        Set-Location "ml-model"
        python -c "from train_model import ICVerificationModel; model = ICVerificationModel.load_model('ic_model.pkl'); result = model.verify_ic('STM32F103C8T6'); print('✅ Traditional ML:', result['status'])"
        Set-Location ".."
        
        Write-Host "`n🧠 Testing Deep Learning..." -ForegroundColor Yellow
        Set-Location "deep-learning-model"
        python -c "from integrated_real_pipeline import RealDatasetICRecognitionPipeline; pipeline = RealDatasetICRecognitionPipeline(); print('✅ Deep Learning: OK')"
        Set-Location ".."
        
        Write-Host "`n✅ All Tests Complete!" -ForegroundColor Green
    }
    
    default {
        Write-Host "❌ Invalid choice" -ForegroundColor Red
    }
}

Write-Host "`n=" * 50
Read-Host "Press Enter to continue"
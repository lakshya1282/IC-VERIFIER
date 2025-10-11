# IC Verification System - Complete Startup Script
# Starts all components: Enhanced API, Traditional ML API, Backend, Frontend

Write-Host "🚀 Starting Complete IC Verification System..." -ForegroundColor Green
Write-Host "=" * 70

# Function to check if process is running on port
function Test-Port {
    param($Port)
    try {
        $connection = Test-NetConnection -ComputerName localhost -Port $Port -InformationLevel Quiet
        return $connection
    } catch {
        return $false
    }
}

# Function to start process in new window
function Start-ServiceInNewWindow {
    param($Title, $Command, $WorkingDirectory)
    Write-Host "🔧 Starting $Title..." -ForegroundColor Yellow
    $startInfo = @{
        FilePath = "powershell"
        ArgumentList = @("-NoExit", "-Command", "cd '$WorkingDirectory'; $Command")
        WindowStyle = "Normal"
        PassThru = $true
    }
    Start-Process @startInfo
    Start-Sleep -Seconds 2
}

# Check if MongoDB is needed and running
Write-Host "📊 Checking MongoDB..." -ForegroundColor Cyan
$mongoRunning = Test-Port 27017
if ($mongoRunning) {
    Write-Host "✅ MongoDB is already running" -ForegroundColor Green
} else {
    Write-Host "⚠️ MongoDB not detected - will start if needed for full stack" -ForegroundColor Yellow
}

# Check prerequisites
Write-Host "`n📦 Checking Prerequisites..." -ForegroundColor Cyan

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found" -ForegroundColor Red
    exit 1
}

# Check Node.js
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✅ Node.js $nodeVersion" -ForegroundColor Green
    $nodeAvailable = $true
} catch {
    Write-Host "⚠️ Node.js not found - Full stack won't be available" -ForegroundColor Yellow
    $nodeAvailable = $false
}

# Check key Python packages
$packages = @("torch", "cv2", "flask", "pandas")
foreach ($package in $packages) {
    try {
        python -c "import $($package.replace('-', '_')); print('✅ $package')" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ $package available" -ForegroundColor Green
        }
    } catch {
        Write-Host "❌ $package missing" -ForegroundColor Red
    }
}

Write-Host "`n🎯 Select System to Start:" -ForegroundColor Yellow
Write-Host "1. Enhanced API Server (Recommended - Port 5000)" -ForegroundColor White
Write-Host "2. Traditional ML API (Port 5000)" -ForegroundColor White
Write-Host "3. Full Stack Web Application (Ports 3000, 3001, 5000)" -ForegroundColor White
Write-Host "4. All Systems (Enhanced + Full Stack)" -ForegroundColor White
Write-Host "5. Test All Models" -ForegroundColor White

$choice = Read-Host "`nEnter your choice (1-5)"

switch ($choice) {
    "1" {
        Write-Host "`n🚀 Starting Enhanced API Server..." -ForegroundColor Green
        
        # Start Enhanced API Server
        $apiPath = "deep-learning-model"
        if (Test-Path $apiPath) {
            Write-Host "🔧 Starting Enhanced IC Verification API..." -ForegroundColor Yellow
            Start-ServiceInNewWindow "Enhanced IC API" "python enhanced_api_server.py" $apiPath
        } else {
            Write-Host "❌ Enhanced API path not found" -ForegroundColor Red
        }
        
        Write-Host "`n✅ Enhanced API Server starting..." -ForegroundColor Green
        Write-Host "🌐 Access at: http://localhost:5000" -ForegroundColor Cyan
        Write-Host "📚 API Documentation: http://localhost:5000" -ForegroundColor Cyan
    }
    
    "2" {
        Write-Host "`n🚀 Starting Traditional ML API..." -ForegroundColor Green
        
        # Start Traditional ML API
        $mlPath = "ml-model"
        if (Test-Path $mlPath) {
            Write-Host "🔧 Starting Traditional ML API..." -ForegroundColor Yellow
            Start-ServiceInNewWindow "Traditional ML API" "python api_server.py" $mlPath
        } else {
            Write-Host "❌ ML model path not found" -ForegroundColor Red
        }
        
        Write-Host "`n✅ Traditional ML API starting..." -ForegroundColor Green
        Write-Host "🌐 Access at: http://localhost:5000" -ForegroundColor Cyan
    }
    
    "3" {
        if (-not $nodeAvailable) {
            Write-Host "❌ Node.js required for full stack application" -ForegroundColor Red
            exit 1
        }
        
        Write-Host "`n🚀 Starting Full Stack Web Application..." -ForegroundColor Green
        
        # Start MongoDB if needed
        if (-not $mongoRunning) {
            Write-Host "🔧 Starting MongoDB..." -ForegroundColor Yellow
            try {
                Start-ServiceInNewWindow "MongoDB" "mongod --dbpath C:\data\db" "."
                Start-Sleep -Seconds 3
            } catch {
                Write-Host "⚠️ Could not start MongoDB automatically" -ForegroundColor Yellow
            }
        }
        
        # Start Traditional ML API
        $mlPath = "ml-model"
        if (Test-Path $mlPath) {
            Start-ServiceInNewWindow "ML API" "python api_server.py" $mlPath
            Start-Sleep -Seconds 2
        }
        
        # Start Backend
        $backendPath = "backend"
        if (Test-Path $backendPath) {
            Start-ServiceInNewWindow "Backend Server" "npm start" $backendPath
            Start-Sleep -Seconds 3
        }
        
        # Start Frontend
        $frontendPath = "frontend"
        if (Test-Path $frontendPath) {
            Start-ServiceInNewWindow "Frontend Server" "npm start" $frontendPath
        }
        
        Write-Host "`n✅ Full Stack System starting..." -ForegroundColor Green
        Write-Host "🌐 Frontend: http://localhost:3001 (or next available port)" -ForegroundColor Cyan
        Write-Host "🔧 Backend: http://localhost:3000" -ForegroundColor Cyan
        Write-Host "🤖 ML API: http://localhost:5000" -ForegroundColor Cyan
    }
    
    "4" {
        Write-Host "`n🚀 Starting All Systems..." -ForegroundColor Green
        
        # Start Enhanced API (on port 5000)
        $enhancedPath = "deep-learning-model"
        if (Test-Path $enhancedPath) {
            Start-ServiceInNewWindow "Enhanced API" "python enhanced_api_server.py" $enhancedPath
            Start-Sleep -Seconds 3
        }
        
        if ($nodeAvailable) {
            # Start Backend (will proxy to ML API on different port)
            $backendPath = "backend"
            if (Test-Path $backendPath) {
                Start-ServiceInNewWindow "Backend Server" "npm start" $backendPath
                Start-Sleep -Seconds 3
            }
            
            # Start Frontend
            $frontendPath = "frontend"
            if (Test-Path $frontendPath) {
                Start-ServiceInNewWindow "Frontend Server" "npm start" $frontendPath
            }
        }
        
        Write-Host "`n✅ All Systems starting..." -ForegroundColor Green
        Write-Host "🌐 Enhanced API: http://localhost:5000" -ForegroundColor Cyan
        Write-Host "🌐 Frontend: http://localhost:3001" -ForegroundColor Cyan
        Write-Host "🔧 Backend: http://localhost:3000" -ForegroundColor Cyan
    }
    
    "5" {
        Write-Host "`n🧪 Testing All Models..." -ForegroundColor Green
        
        # Test enhanced system
        Write-Host "`n📊 Running Enhanced System Tests..." -ForegroundColor Yellow
        python test_enhanced_system.py
        
        # Test traditional ML model
        Write-Host "`n🤖 Testing Traditional ML Model..." -ForegroundColor Yellow
        cd ml-model
        python -c "from train_model import ICVerificationModel; model = ICVerificationModel.load_model('ic_model.pkl'); result = model.verify_ic('STM32F103C8T6'); print('✅ Traditional ML Test:', result['status'], result['confidence'])"
        cd ..
        
        # Test deep learning pipeline
        Write-Host "`n🧠 Testing Deep Learning Pipeline..." -ForegroundColor Yellow
        cd deep-learning-model
        python -c "from integrated_real_pipeline import RealDatasetICRecognitionPipeline; pipeline = RealDatasetICRecognitionPipeline(); print('✅ Deep Learning Pipeline Test: OK')"
        cd ..
        
        Write-Host "`n✅ All Model Tests Complete!" -ForegroundColor Green
        Write-Host "Choose another option to start services." -ForegroundColor Cyan
        
        # Recursive call to show menu again
        & $MyInvocation.MyCommand.Path
        return
    }
    
    default {
        Write-Host "❌ Invalid choice" -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n" + "=" * 70
Write-Host "🎉 System Startup Complete!" -ForegroundColor Green
Write-Host "`n📋 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Wait for all services to fully start (check console outputs)" -ForegroundColor White
Write-Host "2. Test the health endpoints to verify everything is running" -ForegroundColor White
Write-Host "3. Access the web interfaces using the URLs shown above" -ForegroundColor White

Write-Host "`n🔍 Health Check Commands:" -ForegroundColor Cyan
Write-Host "curl http://localhost:5000/health" -ForegroundColor White
Write-Host "curl http://localhost:3000/api/health" -ForegroundColor White

Write-Host "`n💡 Tip: Keep this window open to see the startup status" -ForegroundColor Green
Write-Host "🔄 To stop all services: Close the opened PowerShell windows" -ForegroundColor Yellow
Write-Host "=" * 70

# Keep the window open
Write-Host "`nPress Enter to continue..." -ForegroundColor Gray
Read-Host
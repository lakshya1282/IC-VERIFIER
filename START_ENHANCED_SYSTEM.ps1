# Enhanced IC Verification System Startup Script
# Includes all advanced features: OCR, Internet Search, Image Marking, Database Storage

param(
    [switch]$SkipInstall,
    [switch]$QuickStart,
    [string]$Environment = "development"
)

Write-Host "🚀 Starting Enhanced IC Verification System..." -ForegroundColor Green
Write-Host "🤖 Features: OCR + Internet Search + ML Bot + Image Marking + Database" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Yellow

# Check if virtual environment exists
$VenvPath = ".\ic_enhanced_env"
if (-not (Test-Path $VenvPath)) {
    Write-Host "⚠️ Virtual environment not found. Creating new environment..." -ForegroundColor Yellow
    python -m venv $VenvPath
    Write-Host "✅ Virtual environment created!" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Blue
& "$VenvPath\Scripts\Activate.ps1"

# Install/update dependencies
if (-not $SkipInstall) {
    Write-Host "📦 Installing/updating dependencies..." -ForegroundColor Blue
    
    # Core ML and Computer Vision packages
    pip install torch torchvision opencv-python pillow numpy scikit-learn pandas --quiet
    
    # OCR packages
    pip install pytesseract --quiet
    
    # Web framework and API
    pip install flask flask-cors werkzeug --quiet
    
    # Database
    pip install sqlalchemy --quiet
    
    # Web scraping and internet search
    pip install requests beautifulsoup4 urllib3 --quiet
    
    # PDF processing
    pip install PyPDF2 pymupdf pdfminer.six pdfplumber --quiet
    
    # Image processing and QR codes
    pip install qrcode --quiet
    
    # Utilities
    pip install python-dotenv tqdm colorama --quiet
    
    Write-Host "✅ Dependencies installed!" -ForegroundColor Green
}

# Check Tesseract OCR installation
Write-Host "🔍 Checking Tesseract OCR installation..." -ForegroundColor Blue
try {
    $tesseractPath = Get-Command tesseract -ErrorAction SilentlyContinue
    if ($tesseractPath) {
        Write-Host "✅ Tesseract OCR found at: $($tesseractPath.Source)" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Tesseract OCR not found in PATH" -ForegroundColor Yellow
        Write-Host "📋 Install from: https://github.com/UB-Mannheim/tesseract/wiki" -ForegroundColor Cyan
        Write-Host "🔧 System will use fallback pattern-based OCR" -ForegroundColor Cyan
    }
} catch {
    Write-Host "⚠️ Could not check Tesseract installation" -ForegroundColor Yellow
}

# Create necessary directories
Write-Host "📁 Creating required directories..." -ForegroundColor Blue
$Directories = @(
    ".\deep-learning-model\processed_images",
    ".\deep-learning-model\processed_images\originals",
    ".\deep-learning-model\processed_images\marked", 
    ".\deep-learning-model\processed_images\thumbnails",
    ".\deep-learning-model\search_cache",
    ".\deep-learning-model\api_uploads",
    ".\deep-learning-model\logs"
)

foreach ($Dir in $Directories) {
    if (-not (Test-Path $Dir)) {
        New-Item -ItemType Directory -Path $Dir -Force | Out-Null
        Write-Host "✅ Created: $Dir" -ForegroundColor Gray
    }
}

# Test the comprehensive pipeline
if (-not $QuickStart) {
    Write-Host "🧪 Testing comprehensive pipeline..." -ForegroundColor Blue
    
    try {
        Set-Location ".\deep-learning-model"
        python -c "
from integrated_ocr_pipeline import ComprehensiveICVerificationPipeline
pipeline = ComprehensiveICVerificationPipeline()
status = pipeline.get_system_status()
print('✅ Pipeline Test Results:')
for component, details in status['components'].items():
    status_icon = '✅' if details['available'] else '❌'
    print(f'   {status_icon} {component}: {details.get(\"status\", \"unknown\")}')
print('\n🎯 Available Capabilities:')
for capability in status['capabilities']:
    if capability:
        print(f'   • {capability}')
"
        Set-Location ".."
        Write-Host "✅ Pipeline test completed!" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ Pipeline test failed - some features may not work" -ForegroundColor Yellow
        Set-Location ".."
    }
}

# Start the enhanced API server
Write-Host "`n🚀 Starting Enhanced IC Verification API Server..." -ForegroundColor Green
Write-Host "🌐 Server will be available at: http://localhost:5000" -ForegroundColor Cyan
Write-Host "📚 API Documentation: http://localhost:5000" -ForegroundColor Cyan
Write-Host "`n🔗 Enhanced API Endpoints:" -ForegroundColor Yellow
Write-Host "   • POST /api/v4/verify-comprehensive - Complete verification with all features" -ForegroundColor White
Write-Host "   • POST /api/v4/verify-quick - Quick verification without internet search" -ForegroundColor White
Write-Host "   • POST /api/v4/verify-batch - Process multiple images at once" -ForegroundColor White
Write-Host "   • GET  /api/v4/verification/<id> - Retrieve verification by unique ID" -ForegroundColor White
Write-Host "   • GET  /api/v4/search - Search verification records" -ForegroundColor White
Write-Host "   • GET  /api/v4/statistics - System statistics and analytics" -ForegroundColor White
Write-Host "   • GET  /health - System health check" -ForegroundColor White
Write-Host "   • GET  /system-status - Detailed component status" -ForegroundColor White

Write-Host "`n🎯 Enhanced Features Available:" -ForegroundColor Magenta
Write-Host "   ✅ Advanced OCR with multiple preprocessing techniques" -ForegroundColor White
Write-Host "   ✅ Internet surfing for manufacturer data and datasheets" -ForegroundColor White
Write-Host "   ✅ Automatic image watermarking with QR codes" -ForegroundColor White
Write-Host "   ✅ Comprehensive database storage with unique tracking IDs" -ForegroundColor White
Write-Host "   ✅ ML-based authenticity verification" -ForegroundColor White
Write-Host "   ✅ Batch processing capabilities" -ForegroundColor White
Write-Host "   ✅ Real-time statistics and analytics" -ForegroundColor White

Write-Host "`n💡 Usage Examples:" -ForegroundColor Yellow
Write-Host "   curl -X POST -F 'image=@ic_image.jpg' http://localhost:5000/api/v4/verify-comprehensive" -ForegroundColor Gray
Write-Host "   curl http://localhost:5000/health" -ForegroundColor Gray
Write-Host "   curl http://localhost:5000/api/v4/statistics" -ForegroundColor Gray

Write-Host "`n🔥 Starting server... Press Ctrl+C to stop" -ForegroundColor Red
Write-Host "=" * 80 -ForegroundColor Yellow

# Change to the model directory and start the server
Set-Location ".\deep-learning-model"

try {
    python complete_enhanced_api.py
} catch {
    Write-Host "`n❌ Server startup failed!" -ForegroundColor Red
    Write-Host "🔧 Troubleshooting:" -ForegroundColor Yellow
    Write-Host "   1. Check if all dependencies are installed" -ForegroundColor White
    Write-Host "   2. Verify Python version (3.8+ required)" -ForegroundColor White
    Write-Host "   3. Ensure virtual environment is activated" -ForegroundColor White
    Write-Host "   4. Check the logs for detailed error information" -ForegroundColor White
} finally {
    Set-Location ".."
    Write-Host "`n🛑 Enhanced IC Verification System stopped." -ForegroundColor Red
}
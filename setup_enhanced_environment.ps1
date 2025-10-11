# Enhanced IC Verification System - Virtual Environment Setup
# PowerShell script for Windows

Write-Host "🚀 Setting up Enhanced IC Verification System..." -ForegroundColor Green
Write-Host "=" * 70

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python (\d+)\.(\d+)") {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        if ($major -ge 3 -and $minor -ge 8) {
            Write-Host "✅ Python $pythonVersion found" -ForegroundColor Green
        } else {
            Write-Host "❌ Python 3.8+ required. Found: $pythonVersion" -ForegroundColor Red
            exit 1
        }
    }
} catch {
    Write-Host "❌ Python not found. Please install Python 3.8+." -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
$venvName = "ic_verification_env"

if (Test-Path $venvName) {
    Write-Host "⚠️ Virtual environment '$venvName' already exists. Removing..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $venvName
}

python -m venv $venvName
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Virtual environment created: $venvName" -ForegroundColor Green

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
$activateScript = "$venvName\Scripts\Activate.ps1"

if (Test-Path $activateScript) {
    & $activateScript
    Write-Host "✅ Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to find activation script" -ForegroundColor Red
    exit 1
}

# Upgrade pip
Write-Host "📦 Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️ Failed to upgrade pip, continuing..." -ForegroundColor Yellow
}

# Install basic requirements first
Write-Host "📦 Installing basic requirements..." -ForegroundColor Yellow
$basicPackages = @(
    "wheel",
    "setuptools",
    "numpy>=1.24.0",
    "torch>=2.0.0",
    "torchvision>=0.15.0"
)

foreach ($package in $basicPackages) {
    Write-Host "Installing $package..." -ForegroundColor Cyan
    python -m pip install $package
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️ Failed to install $package" -ForegroundColor Yellow
    }
}

# Install enhanced requirements
Write-Host "📦 Installing enhanced requirements..." -ForegroundColor Yellow
$requirementsFiles = @(
    "deep-learning-model\enhanced_requirements.txt",
    "deep-learning-model\requirements.txt",
    "ml-model\requirements.txt"
)

foreach ($reqFile in $requirementsFiles) {
    if (Test-Path $reqFile) {
        Write-Host "Installing from $reqFile..." -ForegroundColor Cyan
        python -m pip install -r $reqFile
        if ($LASTEXITCODE -ne 0) {
            Write-Host "⚠️ Some packages from $reqFile failed to install" -ForegroundColor Yellow
        }
    } else {
        Write-Host "⚠️ Requirements file not found: $reqFile" -ForegroundColor Yellow
    }
}

# Install additional packages for enhanced features
Write-Host "📦 Installing additional enhanced packages..." -ForegroundColor Yellow
$enhancedPackages = @(
    "PyMuPDF>=1.23.0",
    "pdfminer.six>=20220524", 
    "Flask-CORS>=4.0.0",
    "beautifulsoup4>=4.12.0",
    "pytesseract>=0.3.10"
)

foreach ($package in $enhancedPackages) {
    Write-Host "Installing $package..." -ForegroundColor Cyan
    python -m pip install $package
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️ Failed to install $package" -ForegroundColor Yellow
    }
}

# Verify installation
Write-Host "🔍 Verifying installation..." -ForegroundColor Yellow
$criticalPackages = @("torch", "opencv-python", "flask", "pandas", "numpy", "pymupdf")
$installationSuccess = $true

foreach ($package in $criticalPackages) {
    python -c "import $($package.replace('-', '_')); print('✅ $package')" 2>&1 | Out-Host
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ $package not properly installed" -ForegroundColor Red
        $installationSuccess = $false
    }
}

# Create activation script
$activationScript = @"
# Enhanced IC Verification System - Quick Start
# Run this script to activate the environment and start services

Write-Host "🚀 Enhanced IC Verification System" -ForegroundColor Green
Write-Host "Activating virtual environment..." -ForegroundColor Yellow

# Activate virtual environment
& "ic_verification_env\Scripts\Activate.ps1"

Write-Host "✅ Environment activated!" -ForegroundColor Green
Write-Host "📚 Available commands:" -ForegroundColor Cyan
Write-Host "  • cd deep-learning-model && python enhanced_api_server.py" -ForegroundColor White
Write-Host "  • cd deep-learning-model && python api_server_real.py" -ForegroundColor White
Write-Host "  • cd scripts && python download_datasets.py" -ForegroundColor White
Write-Host "  • cd deep-learning-model && python enhanced_oem_data_fetcher.py" -ForegroundColor White

Write-Host "`n🌐 To start the enhanced API server:" -ForegroundColor Yellow
Write-Host "cd deep-learning-model" -ForegroundColor White
Write-Host "python enhanced_api_server.py" -ForegroundColor White
"@

$activationScript | Out-File -FilePath "start_enhanced_system.ps1" -Encoding UTF8
Write-Host "✅ Created start_enhanced_system.ps1 for easy startup" -ForegroundColor Green

# Summary
Write-Host "`n" + "=" * 70
if ($installationSuccess) {
    Write-Host "🎉 Enhanced IC Verification System setup completed successfully!" -ForegroundColor Green
    Write-Host "📋 Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Run: .\start_enhanced_system.ps1" -ForegroundColor White
    Write-Host "  2. Navigate to deep-learning-model directory" -ForegroundColor White
    Write-Host "  3. Run: python enhanced_api_server.py" -ForegroundColor White
    Write-Host "  4. Access API at: http://localhost:5000" -ForegroundColor White
    
    Write-Host "`n🔗 Available features:" -ForegroundColor Yellow
    Write-Host "  • Enhanced IC database (30+ components)" -ForegroundColor White
    Write-Host "  • PDF datasheet parsing" -ForegroundColor White
    Write-Host "  • OEM data fetching" -ForegroundColor White
    Write-Host "  • Comprehensive verification APIs" -ForegroundColor White
} else {
    Write-Host "⚠️ Setup completed with some warnings" -ForegroundColor Yellow
    Write-Host "Some packages may need manual installation" -ForegroundColor Yellow
}

Write-Host "`n💡 Tip: Run 'python -m pip list' to see installed packages" -ForegroundColor Cyan
Write-Host "=" * 70
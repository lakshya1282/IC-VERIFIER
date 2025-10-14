# 📦 IC Verification System - Complete Requirements & Dependencies
## System Dependencies, Installation Requirements, and Environment Setup

---

## 🖥️ System Requirements

### **Minimum System Requirements:**
| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Windows 10, Ubuntu 18.04, macOS 10.15 | Windows 11, Ubuntu 20.04+, macOS 12+ |
| **RAM** | 8GB | 16GB+ |
| **CPU** | 4-core Intel/AMD | 8-core Intel/AMD |
| **GPU** | Optional | NVIDIA GTX 1060+ with CUDA 11.8+ |
| **Storage** | 10GB free space | 50GB+ SSD |
| **Network** | Broadband internet | Stable high-speed connection |

### **Hardware Acceleration (Optional):**
- **NVIDIA GPU** with CUDA Compute Capability 6.0+
- **CUDA Toolkit** 11.8 or later
- **cuDNN** 8.6 or later
- **GPU Memory**: 4GB+ VRAM recommended

---

## 🛠️ Core Software Requirements

### **1. Node.js & npm**
```bash
# Required Version: Node.js 16.x or higher
node --version  # Should show v16.x.x or higher
npm --version   # Should show 8.x.x or higher

# Installation:
# Windows: Download from https://nodejs.org/
# macOS: brew install node
# Ubuntu: curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt-get install -y nodejs
```

### **2. Python**
```bash
# Required Version: Python 3.8 or higher
python --version  # Should show Python 3.8.x or higher
pip --version     # Should show pip 20.x.x or higher

# Installation:
# Windows: Download from https://python.org/
# macOS: brew install python@3.9
# Ubuntu: sudo apt update && sudo apt install python3 python3-pip
```

### **3. MongoDB**
```bash
# Required Version: MongoDB 5.0 or higher
mongod --version  # Should show db version v5.x.x or higher

# Installation:
# Windows: Download MongoDB Community Server from https://www.mongodb.com/try/download/community
# macOS: brew install mongodb/brew/mongodb-community
# Ubuntu: Follow instructions at https://docs.mongodb.com/manual/tutorial/install-mongodb-on-ubuntu/
```

### **4. Git**
```bash
# Required for dependency management and version control
git --version  # Should show git version 2.x.x or higher

# Installation:
# Windows: Download from https://git-scm.com/
# macOS: brew install git
# Ubuntu: sudo apt install git
```

---

## 🐍 Python Dependencies

### **Deep Learning Model Requirements (`deep-learning-model/requirements.txt`):**
```txt
# Core Deep Learning Framework
torch>=1.13.0
torchvision>=0.14.0
torchaudio>=0.13.0

# Computer Vision Libraries
opencv-python>=4.7.0
opencv-contrib-python>=4.7.0
Pillow>=9.3.0

# Scientific Computing
numpy>=1.24.0
scipy>=1.10.0
matplotlib>=3.6.0
pandas>=1.5.0

# Web Framework & API
Flask>=2.2.0
Flask-CORS>=3.0.10
Werkzeug>=2.2.0

# Image Processing & OCR
pytesseract>=0.3.10
easyocr>=1.6.2

# File Processing
PyPDF2>=3.0.1
pdfminer.six>=20221105
PyMuPDF>=1.21.1  # Also known as fitz

# Data Processing & Utilities
requests>=2.28.0
beautifulsoup4>=4.11.0
lxml>=4.9.0
tqdm>=4.64.0

# Machine Learning Utilities
scikit-learn>=1.2.0
scikit-image>=0.19.0

# Optional: Enhanced Features
transformers>=4.25.0  # For advanced NLP features
onnx>=1.13.0         # For model optimization
onnxruntime>=1.13.0  # For ONNX inference

# Optional: GPU Acceleration (CUDA)
# torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Development & Testing
pytest>=7.2.0
pytest-cov>=4.0.0
black>=22.10.0
flake8>=6.0.0
```

### **Enhanced Dependencies (`deep-learning-model/enhanced_requirements.txt`):**
```txt
# Include all basic requirements
-r requirements.txt

# Advanced PDF Processing
grobid-client>=0.7.0    # Advanced scientific document parsing
pdfplumber>=0.7.6       # Enhanced PDF text extraction
tabula-py>=2.5.1        # PDF table extraction

# Web Scraping & Data Fetching
selenium>=4.7.0         # Browser automation for complex sites
cloudscraper>=1.2.66    # Anti-bot detection bypass

# Database & Caching
redis>=4.5.0            # Caching system
sqlalchemy>=2.0.0       # Database ORM (if needed)

# Performance & Monitoring
psutil>=5.9.0           # System resource monitoring
memory-profiler>=0.61.0 # Memory usage profiling

# API Documentation
flask-restx>=1.0.6      # API documentation with Swagger
marshmallow>=3.19.0     # Serialization/deserialization

# Security & Validation
cryptography>=39.0.0    # Encryption and security
cerberus>=1.3.4         # Data validation

# Image Enhancement
albumentations>=1.3.0   # Image augmentation library
imagehash>=4.3.1        # Perceptual image hashing
```

---

## 📦 Node.js Dependencies

### **Backend Dependencies (`backend/package.json`):**
```json
{
  "dependencies": {
    "express": "^4.18.2",
    "mongoose": "^6.8.0",
    "cors": "^2.8.5",
    "helmet": "^6.0.1",
    "morgan": "^1.10.0",
    "dotenv": "^16.0.3",
    "bcryptjs": "^2.4.3",
    "jsonwebtoken": "^9.0.0",
    "express-rate-limit": "^6.6.0",
    "express-validator": "^6.14.2",
    "multer": "^1.4.5-lts.1",
    "axios": "^1.2.1",
    "node-cron": "^3.0.2",
    "winston": "^3.8.2",
    "compression": "^1.7.4",
    "express-slow-down": "^1.6.0"
  },
  "devDependencies": {
    "nodemon": "^2.0.20",
    "jest": "^29.3.1",
    "supertest": "^6.3.3",
    "eslint": "^8.31.0",
    "prettier": "^2.8.1",
    "husky": "^8.0.3",
    "lint-staged": "^13.1.0"
  }
}
```

### **Frontend Dependencies (`frontend/package.json`):**
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.6.1",
    "react-scripts": "5.0.1",
    "@mui/material": "^5.11.0",
    "@mui/icons-material": "^5.11.0",
    "@emotion/react": "^11.10.5",
    "@emotion/styled": "^11.10.5",
    "@mui/x-charts": "^5.0.8",
    "react-webcam": "^7.0.1",
    "axios": "^1.2.1",
    "react-dropzone": "^14.2.3",
    "recharts": "^2.3.2",
    "react-hot-toast": "^2.4.0",
    "framer-motion": "^8.0.2",
    "react-query": "^3.39.2",
    "react-helmet": "^6.1.0"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^5.16.5",
    "@testing-library/react": "^13.4.0",
    "@testing-library/user-event": "^13.5.0",
    "web-vitals": "^2.1.4",
    "eslint": "^8.31.0",
    "prettier": "^2.8.1"
  }
}
```

---

## 🗃️ Database Requirements

### **MongoDB Configuration:**
```javascript
// Minimum MongoDB version: 5.0
// Recommended: MongoDB 6.0+

// Required MongoDB features:
- GridFS (for large file storage)
- Text indexes (for search functionality)
- Aggregation pipeline (for analytics)
- Change streams (for real-time updates)

// Database size estimates:
- Initial setup: ~100MB
- With training data: ~2GB
- Production (1M records): ~10GB

// Configuration recommendations:
{
  "storage": {
    "wiredTiger": {
      "engineConfig": {
        "cacheSizeGB": 2  // Adjust based on available RAM
      }
    }
  },
  "operationProfiling": {
    "slowOpThresholdMs": 100
  }
}
```

### **Sample Database Indexes:**
```javascript
// Create these indexes for optimal performance
db.verifications.createIndex({ "createdAt": -1 })
db.verifications.createIndex({ "scannedText": "text" })
db.verifications.createIndex({ "status": 1 })
db.verifications.createIndex({ "confidence": -1 })
db.icdata.createIndex({ "partNumber": 1, "manufacturer": 1 })
db.icdata.createIndex({ "markingText": "text" })
```

---

## 🔧 Development Environment Setup

### **1. Python Virtual Environment Setup:**
```bash
# Create virtual environment
cd deep-learning-model
python -m venv ic_deep_learning_env

# Activate environment (Windows)
ic_deep_learning_env\Scripts\activate

# Activate environment (Linux/macOS)
source ic_deep_learning_env/bin/activate

# Install dependencies
pip install -r requirements.txt

# For enhanced features
pip install -r enhanced_requirements.txt

# For GPU support (CUDA 11.8)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### **2. Node.js Environment Setup:**
```bash
# Backend setup
cd backend
npm install
cp .env.example .env  # Edit configuration as needed
npm run dev

# Frontend setup
cd ../frontend
npm install
npm start
```

### **3. MongoDB Setup:**
```bash
# Create data directory (Windows)
mkdir C:\data\db

# Create data directory (Linux/macOS)
sudo mkdir -p /data/db
sudo chown -R $USER:$USER /data/db

# Start MongoDB
mongod --dbpath /data/db

# Or start as service (Linux)
sudo systemctl start mongod
sudo systemctl enable mongod
```

---

## 🐳 Docker Requirements (Optional)

### **Docker Setup for Containerized Deployment:**
```dockerfile
# Dockerfile for Deep Learning API
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 5000
CMD ["python", "enhanced_api_server.py"]
```

### **Docker Compose Configuration:**
```yaml
version: '3.8'
services:
  mongodb:
    image: mongo:6.0
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    
  ml-api:
    build: ./deep-learning-model
    ports:
      - "5000:5000"
    volumes:
      - ./deep-learning-model:/app
    depends_on:
      - mongodb
      
  backend:
    build: ./backend
    ports:
      - "3001:3001"
    environment:
      - MONGODB_URI=mongodb://mongodb:27017/ic_verification
      - ML_API_URL=http://ml-api:5000
    depends_on:
      - mongodb
      - ml-api
      
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:3001/api
    depends_on:
      - backend

volumes:
  mongodb_data:
```

---

## ⚡ Performance Requirements

### **GPU Acceleration (Recommended):**
```bash
# NVIDIA GPU Requirements
- CUDA Compute Capability: 6.0+
- NVIDIA Driver: 470.57.02+
- CUDA Toolkit: 11.8
- cuDNN: 8.6.0

# Installation verification
nvidia-smi
nvcc --version
python -c "import torch; print(torch.cuda.is_available())"
```

### **Memory Requirements:**
```bash
# RAM Usage Estimates:
- Frontend: ~200MB
- Backend: ~150MB
- Deep Learning API: ~2GB (CPU) / ~4GB (GPU)
- MongoDB: ~500MB (with typical dataset)
- Total System: ~3GB (CPU) / ~5GB (GPU)

# Storage Requirements:
- Source code: ~500MB
- Dependencies: ~2GB
- Models: ~1GB
- Database: ~2GB (with training data)
- Total: ~5.5GB
```

### **Network Requirements:**
```bash
# Port Usage:
- Frontend: 3000
- Backend: 3001
- Deep Learning API: 5000
- MongoDB: 27017
- Redis (optional): 6379

# External Network:
- Internet access for OEM data fetching
- HTTPS/TLS support for production
- CDN integration for static assets (optional)
```

---

## 🧪 Testing Dependencies

### **Backend Testing:**
```json
{
  "devDependencies": {
    "jest": "^29.3.1",
    "supertest": "^6.3.3",
    "mongodb-memory-server": "^8.10.2",
    "@types/jest": "^29.2.5"
  }
}
```

### **Frontend Testing:**
```json
{
  "devDependencies": {
    "@testing-library/jest-dom": "^5.16.5",
    "@testing-library/react": "^13.4.0",
    "@testing-library/user-event": "^13.5.0",
    "jest-environment-jsdom": "^29.3.1"
  }
}
```

### **Python Testing:**
```txt
# Testing requirements
pytest>=7.2.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
pytest-asyncio>=0.20.3
requests-mock>=1.10.0
```

---

## 🔒 Security Requirements

### **SSL/TLS Configuration:**
```bash
# For production deployment
# SSL Certificate requirements:
- TLS 1.2 minimum
- Valid SSL certificate (Let's Encrypt recommended)
- HTTPS enforcement
- Secure headers (HSTS, CSP, etc.)
```

### **Environment Security:**
```bash
# Required security measures:
- Environment variables for secrets
- API rate limiting
- Input validation and sanitization
- CORS configuration
- Helmet.js for security headers
- Regular dependency updates
```

---

## 🌐 Browser Compatibility

### **Frontend Browser Support:**
| Browser | Minimum Version | Recommended |
|---------|----------------|-------------|
| **Chrome** | 88+ | Latest |
| **Firefox** | 85+ | Latest |
| **Safari** | 14+ | Latest |
| **Edge** | 88+ | Latest |

### **Required Browser Features:**
- WebRTC (for camera access)
- File API (for image uploads)
- Canvas API (for image processing)
- WebAssembly (for performance)
- ES2020 support
- WebGL (for GPU acceleration in browser)

---

## 📱 Mobile Requirements (Optional)

### **Mobile Browser Support:**
- iOS Safari 14+
- Android Chrome 88+
- Samsung Internet 13+

### **Mobile Development (Future):**
```bash
# React Native requirements (if developing mobile app)
- Node.js 16+
- React Native CLI
- Android Studio (for Android)
- Xcode (for iOS)
- Android SDK 30+
- iOS 12+ support
```

---

## ☁️ Cloud Deployment Requirements

### **AWS Deployment:**
```bash
# Required AWS services:
- EC2 (for application hosting)
- S3 (for static assets and backups)
- RDS or DocumentDB (for managed database)
- CloudFront (for CDN)
- Route 53 (for DNS)
- Certificate Manager (for SSL)
- ELB (for load balancing)

# Minimum EC2 instance:
- Type: t3.large (2 vCPU, 8GB RAM)
- Storage: 50GB EBS
- Network: Enhanced networking enabled
```

### **Google Cloud Platform:**
```bash
# Required GCP services:
- Compute Engine (for application hosting)
- Cloud Storage (for assets)
- Cloud SQL or Firestore (for database)
- Cloud CDN
- Cloud DNS
- Load Balancer

# Minimum compute instance:
- Type: n2-standard-2 (2 vCPU, 8GB RAM)
- Disk: 50GB SSD
```

### **Microsoft Azure:**
```bash
# Required Azure services:
- App Service or Virtual Machines
- Blob Storage
- Azure Database for MongoDB
- CDN
- Application Gateway

# Minimum VM:
- Size: Standard_B2s (2 vCPU, 4GB RAM)
- Disk: 50GB Premium SSD
```

---

## 🔧 Installation Scripts

### **Complete Setup Script (Windows PowerShell):**
```powershell
# setup_complete_environment.ps1
Write-Host "Setting up IC Verification System..."

# Check prerequisites
Write-Host "Checking prerequisites..."
$nodeVersion = node --version 2>$null
$pythonVersion = python --version 2>$null
$mongoVersion = mongod --version 2>$null

if (-not $nodeVersion) { Write-Error "Node.js not found. Please install Node.js 16+" }
if (-not $pythonVersion) { Write-Error "Python not found. Please install Python 3.8+" }
if (-not $mongoVersion) { Write-Warning "MongoDB not found. Please install MongoDB 5.0+" }

# Setup Python environment
Write-Host "Setting up Python environment..."
cd deep-learning-model
python -m venv ic_deep_learning_env
.\ic_deep_learning_env\Scripts\Activate.ps1
pip install -r requirements.txt

# Setup backend
Write-Host "Setting up backend..."
cd ..\backend
npm install

# Setup frontend
Write-Host "Setting up frontend..."
cd ..\frontend
npm install

Write-Host "Setup complete! Use QUICK_START_COMMANDS.md to start the system."
```

### **Linux/macOS Setup Script:**
```bash
#!/bin/bash
# setup_complete_environment.sh

echo "Setting up IC Verification System..."

# Check prerequisites
if ! command -v node &> /dev/null; then
    echo "Node.js not found. Please install Node.js 16+"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "Python not found. Please install Python 3.8+"
    exit 1
fi

# Setup Python environment
echo "Setting up Python environment..."
cd deep-learning-model
python3 -m venv ic_deep_learning_env
source ic_deep_learning_env/bin/activate
pip install -r requirements.txt

# Setup backend
echo "Setting up backend..."
cd ../backend
npm install

# Setup frontend
echo "Setting up frontend..."
cd ../frontend
npm install

echo "Setup complete! Use QUICK_START_COMMANDS.md to start the system."
```

---

## 🎯 Production Deployment Checklist

### **Pre-deployment Requirements:**
- [ ] All dependencies installed and tested
- [ ] Environment variables configured
- [ ] SSL certificates obtained
- [ ] Database optimized with indexes
- [ ] Security headers configured
- [ ] Rate limiting implemented
- [ ] Monitoring and logging setup
- [ ] Backup strategy implemented
- [ ] Load testing completed
- [ ] Documentation updated

### **Performance Benchmarks:**
- [ ] API response time < 1 second
- [ ] Model inference < 2 seconds
- [ ] Database queries < 100ms
- [ ] Frontend load time < 3 seconds
- [ ] System uptime > 99.9%
- [ ] Concurrent users: 100+

---

## 🆘 Support & Troubleshooting

### **Common Installation Issues:**

**Python Issues:**
```bash
# Multiple Python versions
python3 -m pip install --user virtualenv
python3 -m venv ic_env

# Permission issues (Linux/macOS)
sudo chown -R $USER:$USER /usr/local/lib/python3.9/

# Windows path issues
setx PATH "%PATH%;C:\Python39\Scripts"
```

**Node.js Issues:**
```bash
# Node version conflicts
nvm install 18
nvm use 18

# npm permission issues (Linux/macOS)
sudo chown -R $USER:$USER ~/.npm
```

**MongoDB Issues:**
```bash
# Service not starting
sudo systemctl status mongod
sudo journalctl -u mongod

# Data directory permissions
sudo chown -R mongodb:mongodb /var/lib/mongodb
sudo chown mongodb:mongodb /tmp/mongodb-27017.sock
```

### **Getting Help:**
- Check logs in respective service directories
- Verify all ports are available (3000, 3001, 5000, 27017)
- Ensure all environment variables are set
- Run health checks on all services
- Check system resources (RAM, disk space)

---

## 📊 System Resource Monitoring

### **Resource Usage Commands:**
```bash
# Monitor system resources
htop           # Overall system usage
nvidia-smi     # GPU usage (if applicable)
df -h          # Disk usage
free -m        # Memory usage
netstat -tlnp  # Network ports
```

### **Application Monitoring:**
```bash
# Monitor application processes
ps aux | grep node     # Node.js processes
ps aux | grep python   # Python processes
ps aux | grep mongod   # MongoDB process

# Monitor API endpoints
curl -w "Time: %{time_total}s\n" http://localhost:3001/api/health
curl -w "Time: %{time_total}s\n" http://localhost:5000/health
```

---

## 🎉 Final Verification

After installing all requirements, verify your setup with:

```bash
# 1. Check all versions
node --version    # Should be 16+
python --version  # Should be 3.8+
mongod --version  # Should be 5.0+

# 2. Test Python imports
python -c "import torch, torchvision, cv2, flask; print('✅ All Python packages working')"

# 3. Test Node.js packages
cd backend && npm ls --depth=0
cd ../frontend && npm ls --depth=0

# 4. Start all services and run tests
# See QUICK_START_COMMANDS.md for detailed instructions
```

**🎯 If all checks pass, your system is ready for the IC Verification System deployment!**

---

*Last updated: October 11, 2025*  
*Version: Production Ready v1.0*
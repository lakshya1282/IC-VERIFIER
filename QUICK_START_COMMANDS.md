# 🚀 IC Verification System - Quick Start Commands
## Complete Startup Guide for All System Components

---

## 📋 Prerequisites Check

Before starting, ensure you have:
- ✅ **Node.js** (v16 or higher) - `node --version`
- ✅ **Python** (v3.8 or higher) - `python --version`
- ✅ **MongoDB** (running locally or cloud) - `mongod --version`
- ✅ **Git** (for dependencies) - `git --version`

---

## 🎯 Quick Start (Recommended Method)

### **Option 1: Full System Startup (All Services)**
```powershell
# Run the complete startup script
.\START_COMPLETE_PROJECT.ps1

# This will start all services automatically:
# - MongoDB (if not running)
# - Deep Learning API (Port 5000)
# - Backend Server (Port 3001)  
# - Frontend Application (Port 3000)
```

### **Option 2: Manual Step-by-Step Startup**

#### **Step 1: Start MongoDB**
```powershell
# Windows - Start MongoDB service
net start MongoDB

# Or run manually with custom path
mongod --dbpath "C:\data\db"

# Linux/Mac - Start MongoDB service
sudo systemctl start mongod

# Or run manually
mongod --dbpath /data/db
```

#### **Step 2: Start Deep Learning API Server (Terminal 1)**
```powershell
# Navigate to deep learning directory
cd "deep-learning-model"

# Activate virtual environment (if exists)
.\ic_deep_learning_env\Scripts\Activate

# Install dependencies (first time)
pip install flask torch torchvision opencv-python pillow numpy matplotlib requests

# Start enhanced API server (recommended)
python enhanced_api_server.py

# Alternative: Start basic API server
python api_server_real.py
```
**Expected Output:** `Enhanced API server running on http://localhost:5000`

#### **Step 3: Start Backend Server (Terminal 2)**
```powershell
# Navigate to backend directory
cd "backend"

# Install dependencies (first time)
npm install

# Install Python dependencies for intelligent features
pip install requests beautifulsoup4 pypdf2

# Start the backend server
npm start

# Alternative: Direct node execution
node server.js
```
**Expected Output:** `Backend server running on http://localhost:3001`

#### **Step 4: Start Frontend Application (Terminal 3)**
```powershell
# Navigate to frontend directory
cd "frontend"

# Install dependencies (first time)
npm install

# Start the React development server
npm start
```
**Expected Output:** `Frontend application running on http://localhost:3000`

---

## 🌐 Access Points

Once all services are running, you can access:

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend App** | http://localhost:3000 | Main web interface |
| **Backend API** | http://localhost:3001 | RESTful API server |
| **ML API Server** | http://localhost:5000 | Deep learning endpoints |
| **Health Checks** | http://localhost:3001/api/health | System status |
| **ML Health** | http://localhost:5000/health | ML system status |
| **Testing Interface** | http://localhost:3000/test | Built-in test runner |

---

## 🧪 Testing Commands

### **Quick System Health Check**
```powershell
# Test all endpoints quickly
curl http://localhost:3001/api/health
curl http://localhost:5000/health
curl http://localhost:5000/model_info
```

### **Comprehensive System Test**
```powershell
# Navigate to backend directory
cd "backend"

# Run complete intelligent system test
node test_complete_intelligent_system.js

# Run IC endpoint tests
node test_ic_endpoints.js

# Quick functionality test
node quick_test.js
```

### **Frontend Testing**
```powershell
# Access built-in test runner via browser
# http://localhost:3000/test

# Or run tests programmatically
cd "frontend"
npm test
```

### **Deep Learning Model Testing**
```powershell
cd "deep-learning-model"

# Test enhanced system components
python test_enhanced_system.py

# Test API endpoints
python test_api_client.py

# Test standalone components
python test_api_standalone.py
```

---

## 📊 API Endpoint Testing

### **Backend API Testing (Port 3001)**
```bash
# Health check
curl http://localhost:3001/api/health

# Text verification
curl -X POST http://localhost:3001/api/verify-text \
  -H "Content-Type: application/json" \
  -d '{"marking_text": "STM32F103C8T6"}'

# Get statistics
curl http://localhost:3001/api/stats

# Get IC database
curl http://localhost:3001/api/ic-database

# Get verification history
curl "http://localhost:3001/api/verifications?page=1&limit=5"
```

### **Deep Learning API Testing (Port 5000)**
```bash
# Health check
curl http://localhost:5000/health

# Model information
curl http://localhost:5000/model_info

# Image verification (upload file)
curl -X POST -F "image=@sample_ic.jpg" http://localhost:5000/verify

# Enhanced database
curl http://localhost:5000/api/v2/database

# Database search
curl "http://localhost:5000/api/v2/database/search?q=STM32&manufacturer=STMicroelectronics"

# Comprehensive verification
curl -X POST -F "image=@sample_ic.jpg" http://localhost:5000/api/v2/verification/comprehensive
```

---

## 🔧 Environment Configuration

### **Backend Configuration (.env)**
Create `backend/.env` file:
```env
# Server Configuration
PORT=3001
NODE_ENV=development

# Database Configuration
MONGODB_URI=mongodb://localhost:27017/ic_verification

# ML API Configuration
ML_API_URL=http://localhost:5000

# Enhanced Features
ENHANCED_API_URL=http://localhost:5000

# Security
JWT_SECRET=your_jwt_secret_here
API_RATE_LIMIT=100
```

### **Frontend Configuration**
Create `frontend/.env` file:
```env
# API Configuration
REACT_APP_API_URL=http://localhost:3001/api
REACT_APP_ENHANCED_API_URL=http://localhost:5000

# Development Settings
REACT_APP_DEBUG=true
GENERATE_SOURCEMAP=false
```

### **Deep Learning Model Configuration**
Create `deep-learning-model/.env` file:
```env
# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=False

# Model Configuration
MODEL_PATH=./models/real_trained/best_verification_real.pth
CONFIDENCE_THRESHOLD=0.6

# Performance Settings
MAX_UPLOAD_SIZE=50MB
ENABLE_GPU=True
BATCH_SIZE=32

# Enhanced Features
ENHANCED_DB_PATH=../data/enhanced_datasheets.csv
ENABLE_CACHE=True
CACHE_DIR=./oem_cache
```

---

## 🚀 Deployment Commands

### **Local Production Deployment**
```powershell
# Build frontend for production
cd frontend
npm run build

# Start backend in production mode
cd ../backend
set NODE_ENV=production
npm start

# Start ML API with production settings
cd ../deep-learning-model
set FLASK_ENV=production
python enhanced_api_server.py
```

### **Docker Deployment**
```bash
# Build Docker images
docker build -t ic-verifier-frontend ./frontend
docker build -t ic-verifier-backend ./backend  
docker build -t ic-verifier-ml ./deep-learning-model

# Run with Docker Compose
docker-compose up -d

# Check running containers
docker ps
```

### **Cloud Deployment (AWS/GCP/Azure)**
```bash
# Package for cloud deployment
tar -czf ic-verifier-deployment.tar.gz \
  frontend/build \
  backend \
  deep-learning-model \
  docker-compose.yml \
  deployment-scripts

# Deploy to cloud platform (example for AWS)
aws s3 cp ic-verifier-deployment.tar.gz s3://your-deployment-bucket/
aws lambda update-function-code --function-name ic-verifier --zip-file fileb://deployment.zip
```

---

## 🛠️ Troubleshooting Commands

### **Port Conflicts**
```powershell
# Check what's using specific ports
netstat -ano | findstr :3000
netstat -ano | findstr :3001
netstat -ano | findstr :5000

# Kill processes using ports (Windows)
taskkill /PID <PID_NUMBER> /F

# Kill processes using ports (Linux/Mac)
sudo lsof -t -i:3000 | xargs kill -9
sudo lsof -t -i:3001 | xargs kill -9
sudo lsof -t -i:5000 | xargs kill -9
```

### **Dependency Issues**
```powershell
# Clear and reinstall Node.js dependencies
cd frontend
rm -rf node_modules package-lock.json
npm cache clean --force
npm install

cd ../backend
rm -rf node_modules package-lock.json
npm cache clean --force
npm install

# Reinstall Python dependencies
cd ../deep-learning-model
pip uninstall -r requirements.txt -y
pip install -r requirements.txt --upgrade
```

### **Database Issues**
```powershell
# Reset MongoDB database
mongo
use ic_verification
db.dropDatabase()
exit

# Restart MongoDB service
net stop MongoDB
net start MongoDB

# Or restart manually
taskkill /F /IM mongod.exe
mongod --dbpath "C:\data\db"
```

### **Model Loading Issues**
```powershell
cd deep-learning-model

# Check model files exist
ls models/real_trained/
ls models/verification_model.pth

# Retrain model if necessary
python simple_real_training.py

# Test model loading
python -c "import torch; print('PyTorch version:', torch.__version__)"
python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
```

### **Virtual Environment Issues**
```powershell
# Recreate Python virtual environment
cd deep-learning-model
rm -rf ic_deep_learning_env

# Create new environment
python -m venv ic_deep_learning_env

# Activate and install dependencies
.\ic_deep_learning_env\Scripts\Activate
pip install -r requirements.txt
```

---

## ⚡ Performance Optimization Commands

### **GPU Acceleration Setup**
```powershell
# Check CUDA availability
python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
python -c "import torch; print('CUDA devices:', torch.cuda.device_count())"

# Install CUDA-enabled PyTorch (if needed)
pip uninstall torch torchvision
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### **Memory Optimization**
```powershell
# Monitor system resources
# Windows
tasklist /fo table | findstr python
tasklist /fo table | findstr node

# Linux/Mac
htop
ps aux | grep python
ps aux | grep node
```

### **Database Optimization**
```javascript
// MongoDB indexing (run in mongo shell)
use ic_verification
db.verifications.createIndex({ "createdAt": -1 })
db.verifications.createIndex({ "scannedText": "text" })
db.verifications.createIndex({ "status": 1 })
```

---

## 📝 Development Commands

### **Code Quality**
```powershell
# Frontend code formatting
cd frontend
npm run lint
npm run format

# Backend code formatting
cd ../backend
npm run lint

# Python code formatting
cd ../deep-learning-model
pip install black flake8
black . --line-length 88
flake8 . --max-line-length 88
```

### **Testing Automation**
```powershell
# Run all tests
cd backend
npm test

cd ../frontend
npm test -- --coverage

cd ../deep-learning-model
python -m pytest tests/ -v --coverage
```

### **Documentation Generation**
```powershell
# Generate API documentation
cd backend
npm run docs

# Generate Python documentation
cd ../deep-learning-model
pip install sphinx
sphinx-build -b html docs docs/_build
```

---

## 🔄 Maintenance Commands

### **Regular Maintenance**
```powershell
# Update dependencies
cd frontend
npm update

cd ../backend
npm update

cd ../deep-learning-model
pip list --outdated
pip install --upgrade package_name
```

### **Backup Commands**
```powershell
# Backup database
mongodump --db ic_verification --out ./backup/$(date +%Y%m%d)

# Backup model files
cp -r deep-learning-model/models ./backup/models_$(date +%Y%m%d)

# Create full project backup
tar -czf ic-verifier-backup-$(date +%Y%m%d).tar.gz \
  --exclude=node_modules \
  --exclude=__pycache__ \
  --exclude=.git \
  .
```

### **Log Management**
```powershell
# View application logs
tail -f backend/logs/app.log
tail -f deep-learning-model/logs/api.log

# Clear old logs
find . -name "*.log" -mtime +7 -delete
```

---

## 🎯 Production Checklist

### **Pre-deployment Verification**
```bash
# 1. Run all tests
npm test          # Frontend
node test_*.js    # Backend
python test_*.py  # ML API

# 2. Check all health endpoints
curl http://localhost:3001/api/health
curl http://localhost:5000/health

# 3. Verify model performance
curl http://localhost:5000/model_info

# 4. Test complete workflow
curl -X POST -F "image=@test_ic.jpg" http://localhost:5000/verify

# 5. Check system resources
df -h            # Disk space
free -m          # Memory
top              # CPU usage
```

### **Deployment Commands**
```bash
# 1. Build production frontend
cd frontend && npm run build

# 2. Set production environment
export NODE_ENV=production
export FLASK_ENV=production

# 3. Start services with PM2 (process manager)
pm2 start ecosystem.config.js

# 4. Setup reverse proxy (Nginx)
sudo nginx -s reload

# 5. Setup SSL certificates
certbot --nginx -d yourdomain.com
```

---

## 📞 Support Commands

### **System Information**
```powershell
# Get system information
python --version
node --version
npm --version
mongod --version
git --version

# Check running processes
ps aux | grep -E "(python|node|mongod)"

# Check network connections
netstat -tulpn | grep -E "(3000|3001|5000|27017)"
```

### **Error Diagnosis**
```powershell
# Check application logs
tail -f backend/logs/error.log
tail -f deep-learning-model/logs/api.log

# Check system logs
# Windows
eventvwr.msc

# Linux
journalctl -f -u mongodb
journalctl -f -u nginx
```

---

## 🎉 Success Verification

After starting all services, verify the system is working by:

1. **✅ Check all URLs are accessible:**
   - http://localhost:3000 (Frontend)
   - http://localhost:3001/api/health (Backend)
   - http://localhost:5000/health (ML API)

2. **✅ Run comprehensive tests:**
   ```bash
   node backend/test_complete_intelligent_system.js
   python deep-learning-model/test_enhanced_system.py
   ```

3. **✅ Test IC verification workflow:**
   - Upload an IC image via the frontend
   - Verify you get accurate results
   - Check the dashboard shows statistics

4. **✅ Test built-in test runner:**
   - Navigate to http://localhost:3000/test
   - Run all tests and ensure >80% success rate

---

## 🚀 Ready to Use!

Your complete IC Verification System is now running and ready for:
- ✅ Real-time IC verification
- ✅ Batch image processing
- ✅ Analytics and reporting
- ✅ API integration
- ✅ Production deployment

**🎯 All services are now operational and ready for SIH 2025-26 demonstration!**
# Quick Start Guide

Follow these steps to get the IC Verification System up and running quickly.

## Prerequisites Check

```powershell
# Check Node.js installation
node --version

# Check Python installation
python --version

# Check MongoDB installation
mongod --version

# Check Tesseract installation (if OCR is needed)
tesseract --version
```

## Step-by-Step Setup

### Terminal 1 - Train ML Model & Start API

```powershell
cd ic-verification-system\ml-model

# Install dependencies
pip install -r requirements.txt

# Train the model
python train_model.py

# Start ML API server
python api_server.py
```

**Expected Output:** Server running on http://localhost:5000

---

### Terminal 2 - Start Backend Server

```powershell
cd ic-verification-system\backend

# Install dependencies
npm install

# Copy environment file
copy .env.example .env

# Start backend server
npm start
```

**Expected Output:** Server running on http://localhost:3000

---

### Terminal 3 - Start Frontend

```powershell
cd ic-verification-system\frontend

# Install dependencies
npm install

# Start React app
npm start
```

**Expected Output:** App opens at http://localhost:3001

---

### Terminal 4 - Start MongoDB (if not running as service)

```powershell
# Create data directory if it doesn't exist
mkdir C:\data\db

# Start MongoDB
mongod --dbpath C:\data\db
```

---

## Verify Everything is Running

Open your browser and check:

1. **Frontend:** http://localhost:3001
2. **Backend API:** http://localhost:3000/api/health
3. **ML API:** http://localhost:5000/api/health

## Test the System

### Manual Test

1. Go to http://localhost:3001
2. Click on "Scanner" in the navigation
3. Select "Manual Entry" tab
4. Enter: `ATmega328P`
5. Click "Verify IC"
6. You should see a successful verification!

### Camera Test

1. Go to the "Scanner" page
2. Select "Camera Scan" tab
3. Allow camera permissions
4. Point camera at any text
5. Click "Capture & Verify"
6. View the OCR result and verification

## Common Issues

### Port Already in Use

If you get a port conflict error:

**Frontend (React):**
- Create `frontend/.env` and add: `PORT=3001`

**Backend:**
- Edit `backend/.env` and change: `PORT=3001`

**ML API:**
- Edit `ml-model/api_server.py` line 194: change port to `5001`

### MongoDB Connection Failed

```powershell
# Check if MongoDB is running
mongod --version

# Start MongoDB if not running
mongod --dbpath C:\data\db
```

### Camera Not Working

- Check browser permissions (usually in address bar)
- Try a different browser (Chrome recommended)
- Use manual text entry as alternative

### Tesseract OCR Error

If you get "tesseract not found":
1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to: `C:\Program Files\Tesseract-OCR`
3. Add to PATH environment variable
4. Restart terminal/command prompt

## Sample Test Data

Use these IC markings for testing:

- `ATmega328P` - Should match (Microchip Technology)
- `STM32F103C8T6` - Should match (STMicroelectronics)
- `NE555P` - Should match (Texas Instruments)
- `ESP32-WROOM-32` - Should match (Espressif Systems)
- `FAKE12345` - Should NOT match (fraud detection)

## Next Steps

- Add more ICs to `ml-model/ic_dataset.csv`
- Retrain model: `python train_model.py`
- Explore the Dashboard to see statistics
- Check verification history
- Test with real IC chips!

## Getting Help

If you encounter issues:
1. Check the main README.md for detailed documentation
2. Verify all prerequisites are installed
3. Ensure all services are running
4. Check terminal outputs for error messages

---

Happy Verifying! 🎉

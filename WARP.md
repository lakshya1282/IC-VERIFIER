# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

IC Verification System - A full-stack application for verifying the authenticity of Integrated Circuit (IC) chips using machine learning and OCR. Built with MERN stack + Python ML model.

## Essential Development Commands

### Initial Setup (First Time)
```powershell
# 1. Train ML Model (REQUIRED before first run)
cd ml-model
pip install -r requirements.txt
python train_model.py

# 2. Setup Backend
cd backend
npm install
copy .env.example .env

# 3. Setup Frontend
cd frontend
npm install
```

### Daily Development Workflow
```powershell
# Start all services (use 4 separate terminals):

# Terminal 1: ML API Server (Port 5000)
cd ml-model
python api_server.py

# Terminal 2: Backend Server (Port 3000)
cd backend
npm start
# For development with auto-reload: npm run dev

# Terminal 3: Frontend (Port 3001)
cd frontend
npm start

# Terminal 4: MongoDB (if not running as service)
mongod --dbpath C:\data\db
```

### Testing Commands
```powershell
# Frontend Tests
cd frontend
npm test

# Backend Health Check
curl http://localhost:3000/api/health

# ML API Health Check
curl http://localhost:5000/api/health

# Test IC Verification (Manual)
curl -X POST http://localhost:3000/api/verify-text -H "Content-Type: application/json" -d "{\"marking_text\": \"ATmega328P\"}"
```

### Model Management
```powershell
cd ml-model

# Retrain model (after updating ic_dataset.csv)
python train_model.py

# Check model files exist
dir ic_model.pkl ic_metadata.json

# Reload model in running API
curl -X POST http://localhost:5000/api/reload-model
```

### Database Operations
```powershell
# Connect to MongoDB shell
mongo ic_verification

# View verifications
db.verifications.find().limit(5)

# Get verification count
db.verifications.count()

# Clear verification history (if needed)
db.verifications.deleteMany({})
```

## Architecture Overview

### Three-Layer Architecture
```
React Frontend (Port 3001)
    ↓ HTTP/REST
Node.js Backend (Port 3000)
    ↓ HTTP/REST
Flask ML API (Port 5000)
    ↓ Queries
MongoDB Database
```

### Key Components

**Frontend (`frontend/src/`)**
- `App.js` - Main app with routing and theme
- `pages/DashboardPage.jsx` - Statistics dashboard  
- `pages/ScannerPage.jsx` - Camera/text verification interface
- `components/WebcamScanner.jsx` - Camera capture component
- `components/VerificationResult.jsx` - Results display
- `services/api.js` - API communication layer

**Backend (`backend/`)**
- `server.js` - Express server with API routes
- `models/Verification.js` - MongoDB schema for verification history
- Proxy layer between frontend and ML model
- Handles data persistence and history tracking

**ML Model (`ml-model/`)**
- `train_model.py` - ICVerificationModel class and training script
- `api_server.py` - Flask REST API server
- `ic_dataset.csv` - IC database (20 sample records)
- Uses TF-IDF vectorization + cosine similarity for text matching
- OCR integration with Tesseract for image processing

### Data Flow
1. User inputs text/image via React frontend
2. Frontend calls Node.js backend API (`/api/verify-text` or `/api/verify-image`)
3. Backend proxies request to Flask ML API
4. ML model processes text (OCR if image) and returns similarity scores
5. Backend saves verification result to MongoDB
6. Result displayed in React UI with confidence score and IC details

### Database Schema
**Verification Collection:**
```javascript
{
  scannedText: String,           // User input
  extractedText: String,         // OCR output (if image)
  status: 'AUTHENTIC' | 'FRAUD/UNKNOWN',
  confidence: Number (0-1),      // Similarity score
  isValid: Boolean,
  matchedIC: {                   // Full IC details if found
    icModel, oemName, packageType,
    markingText, datasheetUrl, releaseDate
  },
  possibleMatches: Array,        // Alternative matches
  verificationType: 'text' | 'image',
  imageData: String,             // Base64 (truncated)
  createdAt: Date
}
```

## Key API Endpoints

### Backend (`localhost:3000/api/`)
- `POST /verify-text` - Verify IC from text input
- `POST /verify-image` - Verify IC from image (with OCR)
- `GET /verifications` - Get verification history (paginated)
- `GET /stats` - Get dashboard statistics

### ML API (`localhost:5000/api/`)
- `POST /verify-text` - Core ML verification
- `POST /verify-image` - OCR + ML verification  
- `GET /ic-database` - Get all IC records
- `GET /ic-stats` - Database statistics
- `POST /reload-model` - Reload trained model

## Development Guidelines

### Adding New IC Records
1. Edit `ml-model/ic_dataset.csv` with new IC data
2. Retrain model: `cd ml-model && python train_model.py`
3. Restart ML API server to load new model

### Environment Configuration
- Backend config in `backend/.env` (copy from `.env.example`)
- Default ports: Frontend 3001, Backend 3000, ML API 5000, MongoDB 27017
- Change ports in respective config files if conflicts occur

### Prerequisites
- Node.js v16+, Python 3.8+, MongoDB 5.0+
- Tesseract OCR for image text extraction
- Windows: Download from UB-Mannheim, add to PATH

### Common Issues
- **Camera not working**: Check browser permissions, try different browser
- **OCR failing**: Ensure Tesseract installed and in PATH
- **Model not loading**: Check `ic_model.pkl` exists, retrain if missing
- **MongoDB errors**: Verify service running, check connection string

### Code Organization Patterns
- React components use Material-UI for consistent styling
- Backend uses async/await for database operations
- ML API handles both file uploads and base64 image data
- Error handling with try/catch blocks throughout
- CORS enabled for cross-origin requests

### Testing Approach
- Use sample IC markings: `ATmega328P`, `STM32F103C8T6`, `NE555P`
- Test both text input and camera capture workflows
- Verify confidence scores and fraud detection with invalid inputs
- Check verification history and dashboard statistics

### Performance Considerations
- Image data truncated in database for storage efficiency
- Verification history paginated (20 records per page)
- TF-IDF model loaded once at startup, cached in memory
- Database indexes on status and creation date for faster queries
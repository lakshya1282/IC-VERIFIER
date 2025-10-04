# IC Verification System

A comprehensive web application for verifying the authenticity of Integrated Circuits (ICs) by scanning OEM markings using machine learning and OCR technology.

## 🎯 Overview

This system helps industries verify IC chips in bulk by:
- Scanning IC markings using a webcam or phone camera
- Using OCR (Optical Character Recognition) to extract text from images
- Verifying markings against an OEM database using ML-based text matching
- Providing confidence scores and detailed IC information
- Tracking verification history in MongoDB

## 🏗️ Architecture

The system consists of three main components:

1. **ML Model (Python/Flask)**: Text extraction and verification engine
2. **Backend (Node.js/Express/MongoDB)**: API server and data persistence
3. **Frontend (React)**: Web dashboard with webcam integration

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   React Web     │─────▶│  Node.js/Express │─────▶│  Flask ML API   │
│   Dashboard     │◀─────│     Backend      │◀─────│   (Python)      │
└─────────────────┘      └──────────────────┘      └─────────────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │    MongoDB       │
                         │    Database      │
                         └──────────────────┘
```

## 📋 Prerequisites

Before running the application, ensure you have the following installed:

- **Node.js** (v16 or higher) - [Download](https://nodejs.org/)
- **Python** (v3.8 or higher) - [Download](https://python.org/)
- **MongoDB** (v5.0 or higher) - [Download](https://www.mongodb.com/try/download/community)
- **Tesseract OCR** - [Installation Guide](https://github.com/tesseract-ocr/tesseract)

### Installing Tesseract OCR

**Windows:**
```powershell
# Download and install from: https://github.com/UB-Mannheim/tesseract/wiki
# Add to PATH: C:\Program Files\Tesseract-OCR
```

**macOS:**
```bash
brew install tesseract
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

## 🚀 Installation & Setup

### 1. Train the ML Model

Navigate to the ML model directory and train the model:

```bash
cd ml-model

# Install Python dependencies
pip install -r requirements.txt

# Train the model
python train_model.py
```

This will create `ic_model.pkl` and `ic_metadata.json` files.

### 2. Start the ML API Server

In the same `ml-model` directory:

```bash
python api_server.py
```

The Flask API will start on `http://localhost:5000`

### 3. Set Up Backend

Open a new terminal window:

```bash
cd backend

# Install Node.js dependencies
npm install

# Copy environment configuration
copy .env.example .env

# Edit .env file if needed (optional)
# Default MongoDB: mongodb://localhost:27017/ic_verification

# Start the backend server
npm start
```

The backend will start on `http://localhost:3000`

### 4. Set Up Frontend

Open another new terminal window:

```bash
cd frontend

# Install React dependencies
npm install

# Start the React development server
npm start
```

The frontend will open automatically at `http://localhost:3001` (or the next available port)

### 5. Start MongoDB

Ensure MongoDB is running:

**Windows:**
```powershell
# If MongoDB is installed as a service, it should start automatically
# Otherwise, start it manually:
mongod --dbpath "C:\data\db"
```

**macOS/Linux:**
```bash
# If installed via package manager:
sudo systemctl start mongod

# Or run directly:
mongod --dbpath /data/db
```

## 📱 Usage

### Webcam Scanner

1. Navigate to the **Scanner** page
2. Choose the **Camera Scan** tab
3. Grant camera permissions when prompted
4. Position the IC chip in front of the camera
5. Click **"Capture & Verify"**
6. View the verification result with confidence score

### Manual Text Entry

1. Navigate to the **Scanner** page
2. Choose the **Manual Entry** tab
3. Type the IC marking text (e.g., "ATmega328P")
4. Click **"Verify IC"**
5. View the verification result

### Dashboard

- View total verifications performed
- See authentic vs fraud/unknown statistics
- Track success rate
- View recent verification history
- See top verified manufacturers

## 📊 Features

### ML Model
- ✅ TF-IDF vectorization for text matching
- ✅ Character n-gram analysis (2-4 grams)
- ✅ Cosine similarity scoring
- ✅ Configurable confidence threshold (default: 60%)
- ✅ Provides possible matches for low-confidence results

### Backend API
- ✅ RESTful API endpoints
- ✅ MongoDB integration for history tracking
- ✅ Proxy communication with ML model
- ✅ Verification history with pagination
- ✅ Statistics and analytics

### Frontend Dashboard
- ✅ Modern React UI with Material-UI
- ✅ Webcam integration with react-webcam
- ✅ Real-time camera switching (front/rear)
- ✅ Manual text input option
- ✅ Detailed verification results
- ✅ Interactive dashboard with charts
- ✅ Responsive design for mobile/desktop

## 🔌 API Endpoints

### Backend (Port 3000)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/verify-text` | Verify IC from text |
| POST | `/api/verify-image` | Verify IC from image |
| GET | `/api/verifications` | Get verification history |
| GET | `/api/verifications/:id` | Get specific verification |
| GET | `/api/stats` | Get statistics |
| GET | `/api/ic-database` | Get IC database |
| GET | `/api/ic-stats` | Get IC statistics |

### ML API (Port 5000)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/verify-text` | Verify IC marking |
| POST | `/api/verify-image` | Verify IC from image (OCR) |
| GET | `/api/ic-database` | Get all ICs |
| GET | `/api/ic-stats` | Get database stats |

## 📁 Project Structure

```
ic-verification-system/
├── backend/                # Node.js/Express backend
│   ├── models/            # MongoDB models
│   │   └── Verification.js
│   ├── server.js          # Express server
│   ├── package.json
│   └── .env.example       # Environment configuration
│
├── frontend/              # React frontend
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/    # React components
│   │   │   ├── WebcamScanner.jsx
│   │   │   └── VerificationResult.jsx
│   │   ├── pages/         # Page components
│   │   │   ├── DashboardPage.jsx
│   │   │   └── ScannerPage.jsx
│   │   ├── services/      # API service
│   │   │   └── api.js
│   │   ├── App.js
│   │   ├── index.js
│   │   └── index.css
│   └── package.json
│
├── ml-model/              # Python ML model
│   ├── ic_dataset.csv     # IC database
│   ├── train_model.py     # Model training script
│   ├── api_server.py      # Flask API server
│   └── requirements.txt   # Python dependencies
│
└── README.md              # This file
```

## 🔧 Configuration

### Backend Configuration (`.env`)

```env
PORT=3000
NODE_ENV=development
MONGODB_URI=mongodb://localhost:27017/ic_verification
ML_API_URL=http://localhost:5000/api
```

### Frontend Configuration

Create `frontend/.env`:

```env
REACT_APP_API_URL=http://localhost:3000/api
```

## 📝 Adding New ICs to Database

To add new IC chips to the verification database:

1. Open `ml-model/ic_dataset.csv`
2. Add new rows with the following format:
   ```
   IC_Model_Number,OEM_Name,Package_Type,Marking_Text,Marking_Image_URL,Release_Date,Source_URL
   ```
3. Retrain the model:
   ```bash
   cd ml-model
   python train_model.py
   ```
4. Restart the ML API server

## 🐛 Troubleshooting

### Camera Not Working
- Check browser permissions for camera access
- Try switching between front/rear cameras
- Ensure no other application is using the camera

### OCR Not Extracting Text
- Ensure Tesseract is installed and in PATH
- Check image lighting and focus
- Try manual text entry instead

### MongoDB Connection Error
- Verify MongoDB is running: `mongod --version`
- Check connection string in `.env`
- Ensure MongoDB service is started

### ML Model Not Loading
- Verify `ic_model.pkl` exists in `ml-model/` directory
- Retrain the model if file is missing
- Check Python dependencies are installed

## 🎨 Tech Stack

- **Frontend**: React 18, Material-UI, React Router, React Webcam
- **Backend**: Node.js, Express, MongoDB, Mongoose, Axios
- **ML/AI**: Python, Flask, scikit-learn, Pandas, NumPy, Tesseract OCR
- **Database**: MongoDB

## 📄 License

MIT License

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Support

For issues or questions, please open an issue on the repository.

---

**Note**: This is a demo application using a sample dataset. In production, you should:
- Use a larger, verified IC database
- Implement authentication and authorization
- Add rate limiting and security measures
- Deploy using proper hosting services
- Use environment-specific configurations
- Implement comprehensive error handling
- Add automated testing

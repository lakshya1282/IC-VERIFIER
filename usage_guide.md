# IC Verification System - Complete Usage Guide

## Overview

The Enhanced IC Verification System is a comprehensive solution for authenticating integrated circuits using machine learning, OCR, internet search, and database storage. This guide covers all features and usage scenarios.

## Table of Contents

1. [Quick Start](#quick-start)
2. [System Components](#system-components)
3. [API Endpoints](#api-endpoints)
4. [Frontend Usage](#frontend-usage)
5. [Python Scripts](#python-scripts)
6. [Database Management](#database-management)
7. [Configuration](#configuration)
8. [Troubleshooting](#troubleshooting)
9. [Advanced Features](#advanced-features)

## Quick Start

### Prerequisites

- Python 3.8+ with virtual environment
- Node.js 16+ for frontend
- MongoDB for database storage
- Tesseract OCR installed on system

### Installation

1. **Setup Virtual Environment:**
   ```bash
   python -m venv ic_enhanced_env
   # Windows
   ic_enhanced_env\Scripts\activate
   # Linux/Mac
   source ic_enhanced_env/bin/activate
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r enhanced_requirements_complete.txt
   ```

3. **Start All Services:**
   ```bash
   # Windows PowerShell
   .\START_COMPLETE_PROJECT.ps1
   
   # Manual startup
   python complete_enhanced_api.py  # Port 5000
   npm start --prefix frontend      # Port 3000
   npm start --prefix backend       # Port 3001
   ```

### Basic Usage

1. **Web Interface:** Navigate to `http://localhost:3000`
2. **API Testing:** Use `http://localhost:5000/health` to check status
3. **Quick Verification:** Upload an IC image or enter text marking

## System Components

### Core APIs

1. **Enhanced API Server (Port 5000)**
   - Main verification endpoints
   - OCR and ML processing
   - Database integration
   - Internet search capabilities

2. **Backend Server (Port 3001)**
   - RESTful API for frontend
   - Verification history
   - Statistics and reporting
   - Database management

3. **Frontend React App (Port 3000)**
   - User interface
   - Camera integration
   - Real-time verification
   - Dashboard and analytics

### Python Modules

- `complete_enhanced_api.py` - Main API server
- `enhanced_ocr_pipeline.py` - OCR processing pipeline
- `enhanced_database_manager.py` - Database operations
- `enhanced_internet_search.py` - Web search integration
- `enhanced_image_processing.py` - Image marking and QR codes
- `oem_data_fetcher.py` - Manufacturer-specific searches

## API Endpoints

### Main Verification Endpoints

#### 1. Basic Verification
```http
POST /verify
Content-Type: multipart/form-data

Parameters:
- image: IC image file (JPG, PNG)
- chipText: Optional text override

Response:
{
  "status": "success",
  "results": {
    "overall_authenticity": "AUTHENTIC",
    "total_detections": 1,
    "detailed_results": [
      {
        "recognized_text": "STM32F103C8T6",
        "is_authentic": true,
        "authenticity_score": 1.0,
        "detection_confidence": 0.95
      }
    ]
  }
}
```

#### 2. Comprehensive Verification
```http
POST /api/v2/verification/comprehensive
Content-Type: multipart/form-data

Parameters:
- image: IC image file
- enable_internet_search: true/false

Response:
{
  "status": "success",
  "pipeline_results": {
    "recognized_texts": [...],
    "verification_results": [...],
    "pipeline_summary": {
      "overall_authenticity": "AUTHENTIC",
      "authentic_parts": 1,
      "suspicious_parts": 0
    }
  },
  "oem_data": [...],
  "database_matches": [...]
}
```

#### 3. Text-Only Verification
```http
POST /process
Content-Type: application/json

{
  "text": "STM32F103C8T6"
}

Response:
{
  "status": "success",
  "verification_result": "AUTHENTIC",
  "confidence_score": 0.95,
  "manufacturer_info": {...}
}
```

### Database Endpoints

#### 1. Get All Records
```http
GET /api/v2/database
```

#### 2. Search Database
```http
GET /api/v2/database/search?query=STM32&limit=20
```

#### 3. Get Statistics
```http
GET /api/v2/statistics
```

### Utility Endpoints

#### 1. System Health
```http
GET /health
```

#### 2. Model Information
```http
GET /model_info
```

#### 3. OEM Data Fetch
```http
POST /api/v2/oem/fetch
Content-Type: application/json

{
  "part_number": "STM32F103C8T6",
  "manufacturer": "STMicroelectronics"
}
```

## Frontend Usage

### Main Interface

1. **Scanner Page** (`/scanner`)
   - Camera integration for real-time scanning
   - Image upload functionality
   - Instant verification results

2. **Dashboard Page** (`/dashboard`)
   - Verification statistics
   - Recent activity
   - System health monitoring

3. **Database Browser** (`/database`)
   - Browse IC database
   - Search functionality
   - Export capabilities

### Camera Features

- **Real-time Preview:** Live camera feed
- **Auto-capture:** Automatic image capture when IC detected
- **Manual Controls:** Zoom, focus, flash controls
- **Image Enhancement:** Contrast and brightness adjustment

### Results Display

- **Authenticity Status:** Clear AUTHENTIC/SUSPICIOUS indicators
- **Confidence Scores:** ML model confidence levels
- **Detailed Analysis:** OCR text, manufacturer data
- **Historical Comparison:** Similar verification results

## Python Scripts

### 1. Enhanced OCR Pipeline

```python
from enhanced_ocr_pipeline import EnhancedOCRPipeline

# Initialize pipeline
pipeline = EnhancedOCRPipeline()

# Process image
result = pipeline.process_image('ic_image.jpg', enable_internet_search=True)

# Get verification results
print(f"Status: {result['status']}")
print(f"Authenticity: {result['pipeline_results']['pipeline_summary']['overall_authenticity']}")
```

### 2. Database Operations

```python
from enhanced_database_manager import EnhancedDatabaseManager

# Initialize database
db_manager = EnhancedDatabaseManager()

# Store verification result
record_id = db_manager.store_comprehensive_record(
    original_image_path='image.jpg',
    marked_image_path='marked_image.jpg',
    ocr_results=ocr_data,
    verification_results=ml_results,
    internet_data=search_results
)

# Search database
results = db_manager.search_records(query="STM32", limit=10)
```

### 3. Internet Search

```python
from enhanced_internet_search import UnifiedInternetSearchService

# Initialize search service
search_service = UnifiedInternetSearchService()

# Search for IC data
results = search_service.comprehensive_search("STM32F103C8T6")

print(f"Found {len(results['consolidated_results'])} results")
```

### 4. Image Processing

```python
from enhanced_image_processing import EnhancedImageProcessor

# Initialize processor
processor = EnhancedImageProcessor()

# Add verification watermark
marked_image = processor.add_verification_watermark(
    'original.jpg',
    verification_result='AUTHENTIC',
    confidence=0.95,
    timestamp='2024-01-15 10:30:00'
)
```

## Database Management

### Database Schema

The system uses SQLite with the following main tables:

1. **ic_verification_records** - Main verification records
2. **extracted_text** - OCR results
3. **verification_results** - ML verification outcomes
4. **internet_search_results** - Web search data
5. **manufacturer_database** - IC specifications

### Key Operations

1. **Backup Database:**
   ```python
   db_manager.export_database('backup.db')
   ```

2. **Import CSV Data:**
   ```python
   db_manager.import_from_csv('enhanced_datasheets.csv')
   ```

3. **Clean Old Records:**
   ```python
   db_manager.cleanup_old_records(days_old=30)
   ```

4. **Generate Statistics:**
   ```python
   stats = db_manager.get_system_statistics()
   ```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Database Configuration
DATABASE_PATH=./enhanced_verification.db
MONGODB_URI=mongodb://localhost:27017/ic_verification

# API Configuration
API_PORT=5000
FRONTEND_PORT=3000
BACKEND_PORT=3001

# Internet Search
ENABLE_INTERNET_SEARCH=true
SEARCH_TIMEOUT=30
MAX_SEARCH_RESULTS=50

# Image Processing
MAX_IMAGE_SIZE=5MB
SUPPORTED_FORMATS=jpg,jpeg,png,bmp

# OCR Configuration
TESSERACT_PATH=/usr/bin/tesseract
OCR_LANGUAGES=eng

# ML Model
MODEL_CONFIDENCE_THRESHOLD=0.7
ENABLE_GPU=true
```

### System Configuration

1. **Tesseract OCR Setup:**
   ```bash
   # Windows (install from GitHub releases)
   # Add to PATH: C:\Program Files\Tesseract-OCR
   
   # Ubuntu/Debian
   sudo apt install tesseract-ocr
   
   # macOS
   brew install tesseract
   ```

2. **MongoDB Setup:**
   ```bash
   # Install MongoDB Community Edition
   # Start service
   sudo systemctl start mongod
   
   # Enable auto-start
   sudo systemctl enable mongod
   ```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   netstat -ano | findstr :5000
   
   # Kill process (Windows)
   taskkill /PID <process_id> /F
   ```

2. **Python Dependencies**
   ```bash
   # Reinstall requirements
   pip install --force-reinstall -r enhanced_requirements_complete.txt
   
   # Check specific package
   pip show opencv-python
   ```

3. **Tesseract Not Found**
   ```python
   # Verify installation
   import pytesseract
   pytesseract.get_tesseract_version()
   
   # Set custom path
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

4. **Database Connection Issues**
   ```python
   # Test database connection
   from enhanced_database_manager import EnhancedDatabaseManager
   db = EnhancedDatabaseManager()
   db.test_connection()
   ```

### Performance Optimization

1. **GPU Acceleration:**
   - Install CUDA for TensorFlow GPU support
   - Verify GPU detection: `python -c "import torch; print(torch.cuda.is_available())"`

2. **Memory Management:**
   - Monitor memory usage during batch processing
   - Adjust batch sizes in configuration

3. **Database Indexing:**
   - Ensure proper database indexes for search performance
   - Regular database maintenance and cleanup

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run with debug enabled
python complete_enhanced_api.py --debug
```

## Advanced Features

### 1. Batch Processing

Process multiple IC images:

```python
from enhanced_ocr_pipeline import EnhancedOCRPipeline

pipeline = EnhancedOCRPipeline()
results = pipeline.batch_process(['img1.jpg', 'img2.jpg', 'img3.jpg'])

for result in results:
    print(f"Image: {result['filename']}")
    print(f"Status: {result['status']}")
```

### 2. Custom ML Models

Add custom verification models:

```python
# models/custom_model.py
class CustomICVerifier:
    def __init__(self):
        # Load custom model
        pass
    
    def verify(self, text, image=None):
        # Custom verification logic
        return {
            'is_authentic': True,
            'confidence': 0.95
        }
```

### 3. API Integration

Integrate with external systems:

```python
# External API callback
def verification_callback(result):
    # Send to external system
    requests.post('https://external-api.com/ic-verification', json=result)

# Register callback
pipeline.add_callback(verification_callback)
```

### 4. Real-time Monitoring

Set up system monitoring:

```python
from enhanced_database_manager import EnhancedDatabaseManager

def monitor_system():
    db = EnhancedDatabaseManager()
    stats = db.get_real_time_stats()
    
    if stats['error_rate'] > 0.1:  # 10% error rate
        send_alert("High error rate detected")
```

## API Rate Limiting

The system includes built-in rate limiting:

- **Default Limits:** 100 requests per minute per IP
- **Verification Endpoints:** 50 requests per minute
- **Database Queries:** 200 requests per minute

Configure limits in `api_config.json`:

```json
{
  "rate_limits": {
    "default": {"requests": 100, "window": 60},
    "verification": {"requests": 50, "window": 60},
    "database": {"requests": 200, "window": 60}
  }
}
```

## Security Considerations

1. **Input Validation:** All uploaded images are validated for type and size
2. **SQL Injection Protection:** Parameterized queries throughout
3. **XSS Prevention:** Input sanitization in frontend
4. **HTTPS Recommended:** Use reverse proxy with SSL in production

## Production Deployment

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . /app

RUN pip install -r enhanced_requirements_complete.txt
RUN apt-get update && apt-get install -y tesseract-ocr

EXPOSE 5000 3000 3001

CMD ["python", "complete_enhanced_api.py"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  ic-verification-api:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_PATH=/data/verification.db
    volumes:
      - ./data:/data

  mongodb:
    image: mongo:latest
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - ic-verification-api

volumes:
  mongodb_data:
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/ {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Support and Contributing

### Getting Help

1. **Documentation:** Check this usage guide
2. **GitHub Issues:** Report bugs or feature requests
3. **Community Forum:** Join discussions and get help
4. **Email Support:** contact@ic-verification.com

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Development Setup

```bash
# Clone repository
git clone https://github.com/your-org/ic-verification-system.git
cd ic-verification-system

# Setup development environment
python -m venv dev_env
source dev_env/bin/activate  # or dev_env\Scripts\activate on Windows

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Start development server
python complete_enhanced_api.py --debug
```

---

## Quick Reference

### Essential Commands

```bash
# Start system
.\START_COMPLETE_PROJECT.ps1

# Check system status
curl http://localhost:5000/health

# Test verification
curl -X POST -F "image=@test.jpg" http://localhost:5000/verify

# View database
python -c "from enhanced_database_manager import *; db=EnhancedDatabaseManager(); print(db.get_system_statistics())"

# Backup database
python -c "from enhanced_database_manager import *; db=EnhancedDatabaseManager(); db.export_database('backup.db')"
```

### Important File Locations

- **Main API:** `complete_enhanced_api.py`
- **Database:** `enhanced_verification.db`
- **Configuration:** `.env`
- **Logs:** `logs/` directory
- **Uploads:** `uploads/` directory
- **Models:** `models/` directory

This completes the comprehensive usage guide for the Enhanced IC Verification System.
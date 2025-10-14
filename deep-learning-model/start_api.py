#!/usr/bin/env python3
"""
Start the Deep Learning API Server
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

# Set environment variables
os.environ['MODELS_DIR'] = './models'
os.environ['DL_API_PORT'] = '5001'
os.environ['DEBUG'] = 'true'

# Import and start API
from api.inference_api_fixed import app, initialize_pipeline

if __name__ == '__main__':
    print("🚀 Starting IC Recognition Deep Learning API...")
    
    # Initialize pipeline
    if initialize_pipeline():
        print("✅ Pipeline initialized successfully")
        print(f"🌐 Starting server on http://localhost:5001")
        print("📡 Available endpoints:")
        print("  - GET  /api/deep-learning/health")
        print("  - POST /api/deep-learning/verify-image-advanced")  
        print("  - GET  /api/deep-learning/stats")
        
        # Start server
        app.run(
            host='0.0.0.0',
            port=5001,
            debug=True
        )
    else:
        print("❌ Failed to initialize pipeline")
        sys.exit(1)
#!/usr/bin/env python3
"""
Enhanced IC Verification API Server
Combines all verification methods with database storage and internet search
"""

import os
import sys
import json
import base64
import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import tempfile

# Import our enhanced modules
from complete_enhanced_api import app as enhanced_app

# This file creates an alias/wrapper for the complete enhanced API
# All functionality is in complete_enhanced_api.py

if __name__ == '__main__':
    print("🚀 Starting Enhanced IC Verification API Server")
    print("=" * 60)
    print("This is a wrapper for complete_enhanced_api.py")
    print("All enhanced features are available through the main API")
    print("=" * 60)
    
    # Run the enhanced app
    enhanced_app.run(
        host='0.0.0.0',
        port=5000,
        debug=False
    )
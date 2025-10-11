#!/usr/bin/env python3
"""
Enhanced IC Verification System - Component Test Script
Tests all major components and dependencies
"""

import sys
import os
from pathlib import Path
import importlib
import traceback

def test_component(component_name, import_statement, test_func=None):
    """Test a system component"""
    print(f"🔍 Testing {component_name}...")
    
    try:
        # Test import
        if isinstance(import_statement, str):
            exec(import_statement)
        else:
            import_statement()
        
        # Run additional test if provided
        if test_func:
            test_func()
            
        print(f"✅ {component_name}: OK")
        return True
        
    except Exception as e:
        print(f"❌ {component_name}: FAILED - {str(e)}")
        return False

def test_pytorch():
    """Test PyTorch installation and GPU availability"""
    import torch
    print(f"   PyTorch version: {torch.__version__}")
    if torch.cuda.is_available():
        print(f"   GPU: ✅ {torch.cuda.get_device_name(0)}")
    else:
        print(f"   GPU: ❌ Not available (CPU only)")

def test_opencv():
    """Test OpenCV installation"""
    import cv2
    print(f"   OpenCV version: {cv2.__version__}")

def test_enhanced_database():
    """Test enhanced database loading"""
    import pandas as pd
    db_path = Path("./data/enhanced_datasheets.csv")
    if db_path.exists():
        df = pd.read_csv(db_path)
        print(f"   Enhanced database: ✅ {len(df)} records loaded")
        return True
    else:
        print(f"   Enhanced database: ❌ Not found at {db_path}")
        return False

def test_pdf_processing():
    """Test PDF processing capabilities"""
    try:
        import fitz  # PyMuPDF
        print(f"   PyMuPDF: ✅ Available")
    except ImportError:
        print(f"   PyMuPDF: ❌ Not available")
    
    try:
        from pdfminer.high_level import extract_text
        print(f"   pdfminer: ✅ Available")
    except ImportError:
        print(f"   pdfminer: ❌ Not available")

def test_api_components():
    """Test API framework components"""
    from flask import Flask
    from flask_cors import CORS
    print(f"   Flask with CORS: ✅ Available")

def main():
    """Run all system tests"""
    print("🚀 Enhanced IC Verification System - Component Tests")
    print("=" * 60)
    
    # Track test results
    test_results = {}
    
    # Core dependencies
    core_tests = [
        ("Python Version", lambda: print(f"   Python: {sys.version}") or (sys.version_info >= (3, 8)), None),
        ("NumPy", "import numpy as np", lambda: print(f"   NumPy version: {np.__version__}")),
        ("PyTorch", "import torch", test_pytorch),
        ("OpenCV", "import cv2", test_opencv),
        ("Pandas", "import pandas as pd", lambda: print(f"   Pandas version: {pd.__version__}")),
        ("scikit-learn", "import sklearn", lambda: print(f"   sklearn version: {sklearn.__version__}")),
    ]
    
    print("\n📦 Core Dependencies:")
    for test_name, import_stmt, test_func in core_tests:
        test_results[test_name] = test_component(test_name, import_stmt, test_func)
    
    # Enhanced features
    enhanced_tests = [
        ("Flask API", "from flask import Flask", test_api_components),
        ("PDF Processing", "import sys", test_pdf_processing),
        ("Enhanced Database", "import pandas as pd", test_enhanced_database),
    ]
    
    print("\n🔧 Enhanced Features:")
    for test_name, import_stmt, test_func in enhanced_tests:
        test_results[test_name] = test_component(test_name, import_stmt, test_func)
    
    # Optional features
    optional_tests = [
        ("BeautifulSoup", "from bs4 import BeautifulSoup"),
        ("Requests", "import requests"),
        ("Pillow", "from PIL import Image"),
    ]
    
    print("\n🎯 Optional Features:")
    for test_name, import_stmt in optional_tests:
        test_results[test_name] = test_component(test_name, import_stmt, None)
    
    # Test file structure
    print("\n📁 File Structure:")
    important_files = [
        "deep-learning-model/enhanced_api_server.py",
        "deep-learning-model/enhanced_oem_data_fetcher.py",
        "data/enhanced_datasheets.csv",
        "scripts/download_datasets.py",
        "deep-learning-model/integrated_real_pipeline.py"
    ]
    
    for file_path in important_files:
        path = Path(file_path)
        if path.exists():
            print(f"✅ {file_path}: Found")
            test_results[f"File: {file_path}"] = True
        else:
            print(f"❌ {file_path}: Missing")
            test_results[f"File: {file_path}"] = False
    
    # Summary
    print("\n" + "=" * 60)
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    
    if passed == total:
        print(f"🎉 All tests passed! ({passed}/{total})")
        print("✅ System is ready for enhanced IC verification")
    elif passed >= total * 0.8:
        print(f"⚠️ Most tests passed ({passed}/{total})")
        print("🔧 System should work but some features may be limited")
    else:
        print(f"❌ Many tests failed ({passed}/{total})")
        print("🔧 System needs attention before use")
    
    print(f"\n💡 To start the enhanced system:")
    print(f"   1. Ensure virtual environment is activated")
    print(f"   2. cd deep-learning-model")
    print(f"   3. python enhanced_api_server.py")
    print("=" * 60)
    
    return passed >= total * 0.8

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
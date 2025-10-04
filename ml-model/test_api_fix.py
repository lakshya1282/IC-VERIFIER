#!/usr/bin/env python3
"""
Simple test script to verify the API endpoint fixes
"""
import requests
import json
import base64
from PIL import Image
import io

# Test the health endpoint
def test_health():
    try:
        response = requests.get('http://localhost:5000/api/health')
        print(f"Health check: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Status: {data.get('status')}")
            print(f"Model loaded: {data.get('model_loaded')}")
            print(f"Tesseract available: {data.get('tesseract_available')}")
            return True
    except requests.ConnectionError:
        print("Server is not running")
        return False
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

# Test image verification with various request formats
def test_image_verification():
    print("\n--- Testing image verification endpoint ---")
    
    # Test 1: Empty request (should return 400)
    try:
        response = requests.post('http://localhost:5000/api/verify-image', json={})
        print(f"Empty request test: {response.status_code} (expected 400)")
        if response.status_code == 400:
            print(f"Response: {response.json().get('error')}")
    except Exception as e:
        print(f"Empty request test failed: {e}")
    
    # Test 2: Invalid JSON (should return 400)
    try:
        response = requests.post('http://localhost:5000/api/verify-image', 
                               headers={'Content-Type': 'application/json'}, 
                               data="invalid json")
        print(f"Invalid JSON test: {response.status_code}")
    except Exception as e:
        print(f"Invalid JSON test failed: {e}")
    
    # Test 3: Valid base64 image (create a simple test image)
    try:
        # Create a simple test image
        img = Image.new('RGB', (100, 50), color='white')
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        response = requests.post('http://localhost:5000/api/verify-image', 
                               json={'image_base64': f'data:image/jpeg;base64,{img_base64}'})
        print(f"Valid base64 test: {response.status_code}")
        if response.status_code != 200:
            print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Valid base64 test failed: {e}")

if __name__ == "__main__":
    print("Testing API fixes...")
    
    if test_health():
        test_image_verification()
        print("\nAPI tests completed!")
    else:
        print("Please start the server first: python api_server.py")
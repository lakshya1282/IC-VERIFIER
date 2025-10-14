#!/usr/bin/env python3
"""
Detailed IC Verification Test - Shows actual API responses
"""

import requests
import cv2
import numpy as np
import json
from pprint import pprint

def create_test_ic_image():
    """Create a test IC image with visible text"""
    img = np.ones((300, 400, 3), dtype=np.uint8) * 255
    cv2.rectangle(img, (50, 50), (350, 250), (0, 0, 0), 2)
    cv2.rectangle(img, (60, 60), (340, 80), (100, 100, 100), -1)
    
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img, 'STM32F103C8T6', (80, 130), font, 0.7, (0, 0, 0), 2)
    cv2.putText(img, 'ARM 32-BIT', (80, 160), font, 0.5, (0, 0, 0), 1)
    cv2.putText(img, '2024 STM', (80, 190), font, 0.4, (0, 0, 0), 1)
    cv2.putText(img, 'CHINA', (80, 220), font, 0.4, (0, 0, 0), 1)
    
    return img

def test_comprehensive_verification():
    print("🔍 Testing Comprehensive IC Verification")
    print("=" * 60)
    
    # Create test image
    test_img = create_test_ic_image()
    _, img_encoded = cv2.imencode('.jpg', test_img)
    img_bytes = img_encoded.tobytes()
    
    try:
        files = {'image': ('test_ic.jpg', img_bytes, 'image/jpeg')}
        response = requests.post(
            "http://localhost:5000/api/v2/verification/comprehensive", 
            files=files, 
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print("\n📋 Full API Response:")
        print("-" * 40)
        
        if response.status_code == 200:
            result = response.json()
            pprint(result, width=80, depth=6)
        else:
            print(f"Error Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_basic_verification():
    print("\n\n🔍 Testing Basic IC Verification")
    print("=" * 60)
    
    # Create test image
    test_img = create_test_ic_image()
    _, img_encoded = cv2.imencode('.jpg', test_img)
    img_bytes = img_encoded.tobytes()
    
    try:
        files = {'image': ('test_ic.jpg', img_bytes, 'image/jpeg')}
        response = requests.post(
            "http://localhost:5000/verify", 
            files=files, 
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print("\n📋 Full API Response:")
        print("-" * 40)
        
        if response.status_code == 200:
            result = response.json()
            pprint(result, width=80, depth=6)
        else:
            print(f"Error Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_comprehensive_verification()
    test_basic_verification()
    print("\n🏁 Detailed test completed!")
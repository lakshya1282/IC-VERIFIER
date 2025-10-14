#!/usr/bin/env python3
"""
Quick IC Verification System Test with Real Image Upload
Creates a test IC image and tests the verification endpoints
"""

import requests
import cv2
import numpy as np
import json
from io import BytesIO

def create_test_ic_image():
    """Create a test IC image with visible text"""
    # Create a 400x300 white image
    img = np.ones((300, 400, 3), dtype=np.uint8) * 255
    
    # Add some IC-like features
    cv2.rectangle(img, (50, 50), (350, 250), (0, 0, 0), 2)  # IC outline
    cv2.rectangle(img, (60, 60), (340, 80), (100, 100, 100), -1)  # Top section
    
    # Add text that looks like IC markings
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img, 'STM32F103C8T6', (80, 130), font, 0.7, (0, 0, 0), 2)
    cv2.putText(img, 'ARM 32-BIT', (80, 160), font, 0.5, (0, 0, 0), 1)
    cv2.putText(img, '2024 STM', (80, 190), font, 0.4, (0, 0, 0), 1)
    cv2.putText(img, 'CHINA', (80, 220), font, 0.4, (0, 0, 0), 1)
    
    # Add some pins
    for i in range(16):
        x = 70 + i * 17
        cv2.rectangle(img, (x, 250), (x+3, 270), (50, 50, 50), -1)  # Bottom pins
        cv2.rectangle(img, (x, 30), (x+3, 50), (50, 50, 50), -1)   # Top pins
    
    return img

def test_verification_endpoints():
    """Test the verification endpoints with image upload"""
    print("\n🧪 Quick IC Verification System Test")
    print("=" * 50)
    
    # Create test image
    print("📸 Creating test IC image...")
    test_img = create_test_ic_image()
    
    # Convert image to bytes
    _, img_encoded = cv2.imencode('.jpg', test_img)
    img_bytes = img_encoded.tobytes()
    
    # Save test image for reference
    cv2.imwrite('test_ic_image.jpg', test_img)
    print("✅ Test image saved as 'test_ic_image.jpg'")
    
    # Test endpoints
    endpoints = [
        ("http://localhost:5000/verify", "Basic Verification"),
        ("http://localhost:5000/api/v2/verification/comprehensive", "Comprehensive Verification"),
        ("http://localhost:3001/api/verify", "Backend Verification"),
    ]
    
    for url, name in endpoints:
        print(f"\n🔍 Testing {name}...")
        try:
            files = {'image': ('test_ic.jpg', img_bytes, 'image/jpeg')}
            response = requests.post(url, files=files, timeout=30)
            
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"   ✅ Success!")
                    
                    # Print key results
                    if 'chip_identification' in result:
                        print(f"   🔍 Identified: {result['chip_identification'].get('detected_text', 'N/A')}")
                    if 'verification_result' in result:
                        print(f"   ✅ Verification: {result['verification_result'].get('is_legitimate', 'N/A')}")
                    if 'database_matches' in result:
                        matches = len(result['database_matches'])
                        print(f"   📊 Database matches: {matches}")
                        
                except json.JSONDecodeError:
                    print(f"   📄 Response: {response.text[:200]}...")
            else:
                print(f"   ❌ Error: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection failed - service not running")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    # Test database endpoints
    print(f"\n📊 Testing database endpoints...")
    db_endpoints = [
        ("http://localhost:5000/api/v2/database", "Enhanced Database"),
        ("http://localhost:3001/api/ic-database", "Backend Database"),
    ]
    
    for url, name in db_endpoints:
        try:
            response = requests.get(url, timeout=10)
            print(f"   {name}: Status {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    print(f"     📊 Records: {len(data.get('records', data.get('data', [])))}")
        except Exception as e:
            print(f"   {name}: ❌ {str(e)}")

if __name__ == "__main__":
    test_verification_endpoints()
    print(f"\n🏁 Test completed!")
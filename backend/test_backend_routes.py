#!/usr/bin/env python3
"""
Test Backend API Routes
Test the new /api/verify route that was added to backend server
"""

import requests
import time
import cv2
import numpy as np
import base64

def create_test_image():
    """Create a simple test IC image"""
    img = np.ones((300, 400, 3), dtype=np.uint8) * 255
    cv2.rectangle(img, (50, 50), (350, 250), (0, 0, 0), 2)
    cv2.rectangle(img, (60, 60), (340, 80), (100, 100, 100), -1)
    
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img, 'STM32F103C8T6', (80, 130), font, 0.7, (0, 0, 0), 2)
    cv2.putText(img, 'ARM 32-BIT', (80, 160), font, 0.5, (0, 0, 0), 1)
    
    return img

def test_backend_routes():
    """Test all backend routes"""
    print("🧪 Testing Backend API Routes")
    print("=" * 50)
    
    base_url = "http://localhost:3001"
    
    # Test 1: Health Check
    print("\n1. Testing Health Check...")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Health: {data.get('status')}")
            print(f"   📊 Database: {data.get('database')}")
            print(f"   🤖 ML Model: {data.get('mlModel')}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 2: Text Verification (new combined route)
    print("\n2. Testing Combined Verify Route (Text)...")
    try:
        payload = {
            "marking_text": "STM32F103C8T6"
        }
        response = requests.post(f"{base_url}/api/verify", json=payload, timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success!")
            print(f"   📝 Response keys: {list(data.keys())}")
            if 'verificationId' in data:
                print(f"   🆔 Verification ID: {data['verificationId']}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 3: Image Verification (new combined route)
    print("\n3. Testing Combined Verify Route (Image)...")
    try:
        # Create test image and convert to base64
        test_img = create_test_image()
        _, buffer = cv2.imencode('.jpg', test_img)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        payload = {
            "image_base64": f"data:image/jpeg;base64,{img_base64}"
        }
        response = requests.post(f"{base_url}/api/verify", json=payload, timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success!")
            print(f"   📝 Response keys: {list(data.keys())}")
            if 'verificationId' in data:
                print(f"   🆔 Verification ID: {data['verificationId']}")
        else:
            print(f"   ❌ Error: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 4: Statistics
    print("\n4. Testing Statistics...")
    try:
        response = requests.get(f"{base_url}/api/stats", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success!")
            print(f"   📊 Total Verifications: {data.get('total_verifications', 0)}")
            print(f"   ✅ Authentic Count: {data.get('authentic_count', 0)}")
            print(f"   ❌ Fraud Count: {data.get('fraud_count', 0)}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 5: Database Endpoint
    print("\n5. Testing IC Database...")
    try:
        response = requests.get(f"{base_url}/api/ic-database", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success!")
            print(f"   📝 Response type: {type(data)}")
            if isinstance(data, dict):
                print(f"   🔍 Keys: {list(data.keys())}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    print("\n🏁 Backend API Test Complete!")

if __name__ == "__main__":
    print("⏳ Waiting 5 seconds for backend to be ready...")
    time.sleep(5)
    test_backend_routes()
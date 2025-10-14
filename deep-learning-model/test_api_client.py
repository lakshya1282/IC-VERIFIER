#!/usr/bin/env python3
"""
Test Client for Deep Learning API
Tests the deployed API server with sample requests
"""

import requests
import json
import base64
import cv2
import numpy as np
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from utils.image_utils import create_test_image, image_to_base64


class APITestClient:
    """Test client for the deep learning API"""
    
    def __init__(self, base_url="http://localhost:5001"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_health(self):
        """Test health endpoint"""
        print("\n=== Testing Health Endpoint ===")
        
        try:
            response = self.session.get(f"{self.base_url}/api/deep-learning/health")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health Check: {data.get('status', 'unknown')}")
                print(f"   Models Ready: {data.get('ready', False)}")
                print(f"   Device: {data.get('device', 'unknown')}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def test_image_verification(self):
        """Test image verification endpoint"""
        print("\n=== Testing Image Verification ===")
        
        # Create test images with different IC markings
        test_cases = [
            ("STM32F407VG", "STMicroelectronics microcontroller"),
            ("LM358N", "Texas Instruments op-amp"),  
            ("FAKE123XYZ", "Fake/suspicious marking"),
            ("74HC04", "Logic gate IC"),
            ("ATmega328P", "Microchip microcontroller")
        ]
        
        results = []
        
        for ic_text, description in test_cases:
            print(f"\nTesting: {ic_text} ({description})")
            
            try:
                # Create test image
                test_image = create_test_image(
                    text=ic_text,
                    width=400,
                    height=150,
                    font_scale=1.0
                )
                
                # Convert to base64
                image_base64 = image_to_base64(test_image)
                
                # Prepare request
                payload = {
                    "image_base64": image_base64,
                    "confidence_threshold": 0.3
                }
                
                # Send request
                response = self.session.post(
                    f"{self.base_url}/api/deep-learning/verify-image-advanced",
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extract results
                    success = data.get('success', False)
                    processing_time = data.get('processing_time', 0)
                    overall_status = data.get('overall_status', 'UNKNOWN')
                    overall_confidence = data.get('overall_confidence', 0)
                    detections = data.get('detections', [])
                    
                    print(f"   ✅ Status: {overall_status}")
                    print(f"   📊 Confidence: {overall_confidence:.3f}")
                    print(f"   ⏱️  Processing: {processing_time:.3f}s")
                    print(f"   🔍 Detections: {len(detections)}")
                    
                    # Show detailed results
                    for i, detection in enumerate(detections):
                        text = detection.get('recognized_text', 'N/A')
                        verification = detection.get('verification', {})
                        v_status = verification.get('status', 'UNKNOWN')
                        v_confidence = verification.get('confidence', 0)
                        
                        print(f"     Detection {i}: '{text}' -> {v_status} ({v_confidence:.3f})")
                    
                    results.append({
                        'input': ic_text,
                        'success': success,
                        'status': overall_status,
                        'confidence': overall_confidence,
                        'processing_time': processing_time,
                        'detections': len(detections)
                    })
                    
                else:
                    print(f"   ❌ Request failed: {response.status_code}")
                    print(f"      Response: {response.text}")
                    results.append({
                        'input': ic_text,
                        'success': False,
                        'error': f"HTTP {response.status_code}"
                    })
                
            except Exception as e:
                print(f"   ❌ Exception: {e}")
                results.append({
                    'input': ic_text,
                    'success': False,
                    'error': str(e)
                })
        
        return results
    
    def test_stats(self):
        """Test stats endpoint"""
        print("\n=== Testing Stats Endpoint ===")
        
        try:
            response = self.session.get(f"{self.base_url}/api/deep-learning/stats")
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"✅ Statistics Retrieved:")
                print(f"   Total Requests: {data.get('total_requests', 0)}")
                print(f"   Success Rate: {data.get('success_rate', 0):.1%}")
                print(f"   Avg Processing Time: {data.get('average_processing_time', 0):.3f}s")
                
                model_info = data.get('model_info', {})
                print(f"   Detection Model: {model_info.get('detection_model', 'N/A')}")
                print(f"   Recognition Model: {model_info.get('recognition_model', 'N/A')}")
                print(f"   Verification Model: {model_info.get('verification_model', 'N/A')}")
                
                return True
            else:
                print(f"❌ Stats request failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Stats error: {e}")
            return False
    
    def run_full_test_suite(self):
        """Run complete API test suite"""
        print("🧪 Starting Deep Learning API Test Suite")
        print("=" * 50)
        
        # Test results
        test_results = []
        
        # 1. Health Check
        health_result = self.test_health()
        test_results.append(("Health Check", health_result))
        
        if not health_result:
            print("\n❌ Health check failed - aborting further tests")
            return False
        
        # 2. Image Verification
        verification_results = self.test_image_verification()
        successful_verifications = sum(1 for r in verification_results if r.get('success', False))
        verification_success = successful_verifications > 0
        test_results.append(("Image Verification", verification_success))
        
        # 3. Stats Check
        stats_result = self.test_stats()
        test_results.append(("Statistics", stats_result))
        
        # Summary
        print("\n" + "=" * 50)
        print("🏁 TEST SUITE SUMMARY")
        print("=" * 50)
        
        passed = 0
        for test_name, result in test_results:
            status = "PASS" if result else "FAIL"
            print(f"{test_name:20} : {status}")
            if result:
                passed += 1
        
        success_rate = passed / len(test_results)
        print(f"\nOverall Success Rate: {success_rate:.1%} ({passed}/{len(test_results)})")
        
        if verification_results:
            print(f"\nImage Verification Details:")
            for result in verification_results:
                input_text = result['input']
                if result['success']:
                    status = result.get('status', 'UNKNOWN')
                    confidence = result.get('confidence', 0)
                    time_ms = result.get('processing_time', 0) * 1000
                    print(f"  {input_text:12} -> {status:15} ({confidence:.3f}) [{time_ms:.0f}ms]")
                else:
                    error = result.get('error', 'Unknown error')
                    print(f"  {input_text:12} -> ERROR: {error}")
        
        if success_rate >= 0.8:
            print("\n✅ API is working well and ready for production!")
            return True
        else:
            print("\n⚠️  API has some issues but basic functionality works.")
            return False


def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Deep Learning API')
    parser.add_argument('--url', default='http://localhost:5001', 
                       help='Base URL for the API server')
    parser.add_argument('--wait', type=int, default=0,
                       help='Wait time in seconds before starting tests')
    
    args = parser.parse_args()
    
    if args.wait > 0:
        import time
        print(f"⏳ Waiting {args.wait} seconds for server to start...")
        time.sleep(args.wait)
    
    # Run tests
    client = APITestClient(args.url)
    success = client.run_full_test_suite()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
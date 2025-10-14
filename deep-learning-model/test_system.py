"""
Test Client for IC Verification System
Demonstrates the complete system functionality
"""

import requests
import numpy as np
import cv2
import base64
import json
import os
from datetime import datetime

def create_test_ic_image():
    """Create a synthetic IC chip image for testing"""
    # Create a synthetic IC image
    img = np.ones((400, 600, 3), dtype=np.uint8) * 240  # Light gray background
    
    # Draw IC chip body (dark rectangle)
    cv2.rectangle(img, (50, 50), (550, 350), (60, 60, 60), -1)
    
    # Draw IC pins
    for i in range(8):
        # Top pins
        cv2.rectangle(img, (100 + i*50, 30), (120 + i*50, 50), (180, 180, 180), -1)
        # Bottom pins
        cv2.rectangle(img, (100 + i*50, 350), (120 + i*50, 370), (180, 180, 180), -1)
    
    # Add IC marking text
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img, 'STM32F407VG', (200, 150), font, 1, (255, 255, 255), 2)
    cv2.putText(img, 'ARM Cortex-M4', (210, 190), font, 0.6, (200, 200, 200), 1)
    cv2.putText(img, 'ST MICRO', (230, 230), font, 0.7, (200, 200, 200), 1)
    cv2.putText(img, '2025 GENUINE', (220, 270), font, 0.5, (150, 150, 150), 1)
    
    # Add some noise for realism
    noise = np.random.randint(0, 10, img.shape, dtype=np.uint8)
    img = cv2.add(img, noise)
    
    return img

def test_api_health():
    """Test API health endpoint"""
    print("\n" + "="*60)
    print("🏥 Testing API Health Check...")
    print("-"*60)
    
    try:
        response = requests.get("http://localhost:5000/health")
        if response.status_code == 200:
            health_data = response.json()
            print("✅ API is healthy!")
            print(f"  • Status: {health_data.get('status')}")
            print(f"  • Pipeline: {'Loaded' if health_data.get('pipeline_loaded') else 'Not Loaded'}")
            print(f"  • Device: {health_data.get('device')}")
            print(f"  • Model: {health_data.get('verification_model', 'Unknown')}")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error connecting to API: {e}")
        return False

def test_model_info():
    """Test model info endpoint"""
    print("\n" + "="*60)
    print("📊 Getting Model Information...")
    print("-"*60)
    
    try:
        response = requests.get("http://localhost:5000/model_info")
        if response.status_code == 200:
            model_data = response.json()
            print("✅ Model Information Retrieved!")
            print(f"  • Accuracy: {model_data.get('accuracy', 'N/A')}")
            print(f"  • Dataset: {model_data.get('dataset', 'N/A')}")
            print(f"  • Training Samples: {model_data.get('training_samples', 'N/A')}")
            return True
    except Exception as e:
        print(f"⚠️ Model info endpoint not available: {e}")
        return False

def test_ic_verification(image_path=None):
    """Test IC verification with an image"""
    print("\n" + "="*60)
    print("🔍 Testing IC Verification...")
    print("-"*60)
    
    try:
        # Create or load test image
        if image_path and os.path.exists(image_path):
            print(f"📷 Using image: {image_path}")
            with open(image_path, 'rb') as f:
                files = {'image': f}
                response = requests.post("http://localhost:5000/verify", files=files)
        else:
            print("🎨 Creating synthetic IC image for testing...")
            img = create_test_ic_image()
            
            # Save test image
            test_image_path = "test_ic_chip.jpg"
            cv2.imwrite(test_image_path, img)
            print(f"💾 Test image saved: {test_image_path}")
            
            # Send for verification
            with open(test_image_path, 'rb') as f:
                files = {'image': f}
                response = requests.post("http://localhost:5000/verify", files=files)
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Verification Complete!")
            print("\n📊 Results:")
            
            if 'results' in result:
                results = result['results']
                print(f"  • Total Detections: {results.get('total_detections', 0)}")
                print(f"  • Authentic Parts: {results.get('authentic_parts', 0)}")
                print(f"  • Suspicious Parts: {results.get('suspicious_parts', 0)}")
                print(f"  • Overall Status: {results.get('overall_authenticity', 'UNKNOWN')}")
                
                # Check detailed results
                if 'detailed_results' in results and results['detailed_results']:
                    print("\n📋 Detailed Results:")
                    for i, detail in enumerate(results['detailed_results'][:3]):  # Show first 3
                        print(f"\n  Detection {i+1}:")
                        print(f"    • Text: {detail.get('recognized_text', 'N/A')}")
                        print(f"    • Authentic: {detail.get('is_authentic', 'Unknown')}")
                        print(f"    • Confidence: {detail.get('confidence', 0):.2%}")
            
            return True
        else:
            print(f"❌ Verification failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_full_processing():
    """Test full processing pipeline with annotated output"""
    print("\n" + "="*60)
    print("🚀 Testing Full Processing Pipeline...")
    print("-"*60)
    
    try:
        print("🎨 Creating test image...")
        img = create_test_ic_image()
        test_image_path = "test_ic_full.jpg"
        cv2.imwrite(test_image_path, img)
        
        with open(test_image_path, 'rb') as f:
            files = {'image': f}
            response = requests.post("http://localhost:5000/process", files=files)
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Full Processing Complete!")
            
            # Check for annotated images
            if 'annotated_images' in result:
                print("\n🖼️ Annotated Images Generated:")
                for key, img_data in result['annotated_images'].items():
                    if img_data:
                        print(f"  • {key}: Available (base64 encoded)")
            
            # Show pipeline summary
            if 'pipeline_summary' in result:
                summary = result['pipeline_summary']
                print("\n📊 Pipeline Summary:")
                print(f"  • Processing Time: {summary.get('processing_time', 0):.3f}s")
                print(f"  • Total Detections: {summary.get('total_detections', 0)}")
                print(f"  • Overall Result: {summary.get('overall_authenticity', 'UNKNOWN')}")
            
            return True
        else:
            print(f"❌ Full processing failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error during full processing: {e}")
        return False

def run_complete_test():
    """Run complete system test"""
    print("\n" + "="*70)
    print("🚀 IC VERIFICATION SYSTEM - COMPLETE TEST")
    print("="*70)
    print(f"📅 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Track results
    test_results = {
        'health': False,
        'model_info': False,
        'verification': False,
        'full_processing': False
    }
    
    # Run tests
    test_results['health'] = test_api_health()
    test_results['model_info'] = test_model_info()
    
    if test_results['health']:
        test_results['verification'] = test_ic_verification()
        test_results['full_processing'] = test_full_processing()
    else:
        print("\n⚠️ Skipping verification tests - API not healthy")
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in test_results.values() if v)
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is working perfectly!")
    elif passed > 0:
        print("⚠️ Some tests passed. Check failed components.")
    else:
        print("❌ All tests failed. Check if the API server is running.")
    
    print("\n" + "="*70)
    print("✅ TEST COMPLETE")
    print("="*70)
    
    # Clean up test images
    for file in ['test_ic_chip.jpg', 'test_ic_full.jpg']:
        if os.path.exists(file):
            try:
                os.remove(file)
            except:
                pass

if __name__ == "__main__":
    run_complete_test()
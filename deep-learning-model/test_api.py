#!/usr/bin/env python3
"""
Test script for Deep Learning API
"""

import sys
import time
import base64
import io
import cv2
import numpy as np
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from api.inference_api_fixed import DeepLearningInferencePipeline
from utils.image_utils import create_test_image, image_to_base64


def test_api_pipeline():
    """Test the inference API pipeline"""
    print("=== Testing Deep Learning API Pipeline ===")
    
    try:
        # Initialize pipeline
        print("Initializing pipeline...")
        pipeline = DeepLearningInferencePipeline(
            models_dir='./models',
            device='cpu'  # Use CPU for testing
        )
        
        # Test health check
        print("Testing health check...")
        health = pipeline.health_check()
        print(f"Health status: {health['status']}")
        print(f"Models ready: {health['ready']}")
        
        # Create test image
        print("Creating test image...")
        test_image = create_test_image(
            text="STM32F407VG", 
            width=400, 
            height=120,
            font_scale=1.2
        )
        
        # Convert to base64
        image_base64 = image_to_base64(test_image)
        
        # Test image processing
        print("Testing image processing...")
        result = pipeline.process_image_base64(image_base64, confidence_threshold=0.1)
        
        # Print results
        print("\n--- API Test Results ---")
        print(f"Success: {result.get('success', False)}")
        print(f"Processing time: {result.get('processing_time', 0):.3f}s")
        print(f"Total detections: {result.get('summary', {}).get('total_detections', 0)}")
        
        # Print individual detections
        detections = result.get('detections', [])
        print(f"Processed {len(detections)} detections:")
        
        for i, detection in enumerate(detections):
            bbox = detection.get('bounding_box', {})
            text = detection.get('recognized_text', 'N/A')
            verification = detection.get('verification', {})
            status = verification.get('status', 'UNKNOWN')
            confidence = verification.get('confidence', 0.0)
            
            print(f"  Detection {i}:")
            print(f"    Text: '{text}'")
            print(f"    Status: {status}")
            print(f"    Confidence: {confidence:.3f}")
            print(f"    BBox: [{bbox.get('x1', 0)}, {bbox.get('y1', 0)}, {bbox.get('x2', 0)}, {bbox.get('y2', 0)}]")
        
        # Overall assessment
        overall_status = result.get('overall_status', 'UNKNOWN')
        overall_confidence = result.get('overall_confidence', 0.0)
        print(f"\nOverall Assessment: {overall_status} (confidence: {overall_confidence:.3f})")
        
        # Test statistics
        print("\nTesting performance statistics...")
        stats = pipeline.get_stats()
        print(f"Total requests: {stats.get('total_requests', 0)}")
        print(f"Success rate: {stats.get('success_rate', 0):.1%}")
        print(f"Average processing time: {stats.get('average_processing_time', 0):.3f}s")
        print(f"Device: {stats.get('model_info', {}).get('device', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multiple_images():
    """Test with multiple different IC images"""
    print("\n=== Testing Multiple IC Images ===")
    
    try:
        pipeline = DeepLearningInferencePipeline(device='cpu')
        
        test_cases = [
            ("LM358N", "Texas Instruments Op-Amp"),
            ("STM32F407VG", "STMicroelectronics MCU"),
            ("74HC04", "Logic Gate"),
            ("ATmega328P", "Atmel Microcontroller"),
            ("NE555", "Timer IC")
        ]
        
        print("Testing various IC markings:")
        
        for ic_text, description in test_cases:
            # Create test image
            test_image = create_test_image(
                text=ic_text,
                width=300,
                height=80,
                font_scale=0.8
            )
            
            # Convert and process
            image_base64 = image_to_base64(test_image)
            result = pipeline.process_image_base64(image_base64, confidence_threshold=0.1)
            
            # Extract results
            overall_status = result.get('overall_status', 'UNKNOWN')
            processing_time = result.get('processing_time', 0)
            
            print(f"  {ic_text:12} ({description:25}): {overall_status:15} ({processing_time:.2f}s)")
        
        return True
        
    except Exception as e:
        print(f"Multiple image test failed: {e}")
        return False


def main():
    """Run all API tests"""
    print("Deep Learning API Test Suite")
    print("=" * 40)
    
    test_results = []
    
    # Test 1: Basic pipeline
    test_results.append(("Basic Pipeline", test_api_pipeline()))
    
    # Test 2: Multiple images
    test_results.append(("Multiple Images", test_multiple_images()))
    
    # Summary
    print("\n" + "=" * 40)
    print("API TEST SUMMARY")
    print("=" * 40)
    
    passed = 0
    for test_name, result in test_results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name:20} : {status}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(test_results)}")
    
    if passed == len(test_results):
        print("✓ All API tests passed! Ready for deployment.")
        return True
    else:
        print("⚠ Some API tests failed.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
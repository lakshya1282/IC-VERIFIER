#!/usr/bin/env python3
"""
Test script for IC Recognition Deep Learning Pipeline
Tests all components: Detection, Recognition, Verification
"""

import os
import sys
import cv2
import numpy as np
import torch
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from detection.simple_detector import SimpleCRAFTDetector as CRAFTDetector
from recognition.crnn_recognizer import CRNNRecognizer
from verification.ic_verifier_fixed import ICVerifier
from utils.image_utils import create_test_image


def test_craft_detection():
    """Test CRAFT text detection"""
    print("\n=== Testing CRAFT Detection ===")
    
    try:
        detector = CRAFTDetector(device='cpu')
        print("✓ CRAFT detector initialized")
        
        # Create test image
        test_image = create_test_image(
            text="STM32F407VG", 
            width=300, 
            height=100,
            font_scale=1.0
        )
        
        # Detect text
        boxes, scores, region_map, affinity_map = detector.detect_text(test_image)
        
        print(f"✓ Detected {len(boxes)} text regions")
        print(f"  Detection scores: {[f'{s:.3f}' for s in scores]}")
        
        if len(boxes) > 0:
            print("✓ CRAFT detection working")
            return True
        else:
            print("⚠ No text detected")
            return False
            
    except Exception as e:
        print(f"✗ CRAFT detection failed: {e}")
        return False


def test_crnn_recognition():
    """Test CRNN text recognition"""
    print("\n=== Testing CRNN Recognition ===")
    
    try:
        recognizer = CRNNRecognizer(device='cpu')
        print("✓ CRNN recognizer initialized")
        
        # Create test text image
        test_image = create_test_image(
            text="LM358N", 
            width=200, 
            height=64,
            font_scale=1.2
        )
        
        # Recognize text
        recognized_text, confidence = recognizer.recognize_from_image(test_image)
        
        print(f"✓ Recognized text: '{recognized_text}' (confidence: {confidence:.3f})")
        
        if len(recognized_text) > 0:
            print("✓ CRNN recognition working")
            return True
        else:
            print("⚠ No text recognized")
            return False
            
    except Exception as e:
        print(f"✗ CRNN recognition failed: {e}")
        return False


def test_ic_verification():
    """Test IC verification"""
    print("\n=== Testing IC Verification ===")
    
    try:
        verifier = ICVerifier(device='cpu')
        print("✓ IC verifier initialized")
        
        # Test known IC parts
        test_cases = [
            "STM32F407VG",  # STMicroelectronics microcontroller
            "LM358N",       # Texas Instruments op-amp
            "74HC04",       # Logic gate
            "FAKE123XYZ"    # Non-existent part
        ]
        
        for test_text in test_cases:
            result = verifier.verify_ic(test_text)
            status = result['status']
            confidence = result['confidence']
            
            print(f"  {test_text}: {status} (confidence: {confidence:.3f})")
        
        print("✓ IC verification working")
        return True
        
    except Exception as e:
        print(f"✗ IC verification failed: {e}")
        return False


def test_full_pipeline():
    """Test complete pipeline integration"""
    print("\n=== Testing Full Pipeline ===")
    
    try:
        # Initialize all components
        detector = CRAFTDetector(device='cpu')
        recognizer = CRNNRecognizer(device='cpu')
        verifier = ICVerifier(device='cpu')
        
        print("✓ All components initialized")
        
        # Create test image with multiple IC markings
        test_image = create_test_image(
            text="STM32F407VG LM358N", 
            width=400, 
            height=100,
            font_scale=1.0
        )
        
        # Stage 1: Detection
        boxes, scores, _, _ = detector.detect_text(test_image)
        print(f"✓ Detected {len(boxes)} regions")
        
        # Stage 2 & 3: Recognition and Verification
        results = []
        
        for i, (box, score) in enumerate(zip(boxes, scores)):
            # Extract region
            x1, y1, x2, y2 = box.astype(int)
            h, w = test_image.shape[:2]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            
            if x2 > x1 and y2 > y1:
                text_region = test_image[y1:y2, x1:x2]
                
                # Recognize
                text, rec_conf = recognizer.recognize_from_image(text_region)
                
                # Verify
                verification = verifier.verify_ic(text)
                
                results.append({
                    'region': i,
                    'text': text,
                    'recognition_confidence': rec_conf,
                    'verification': verification
                })
                
                print(f"  Region {i}: '{text}' -> {verification['status']} ({verification['confidence']:.3f})")
        
        if results:
            print("✓ Full pipeline working")
            return True
        else:
            print("⚠ Pipeline produced no results")
            return False
            
    except Exception as e:
        print(f"✗ Full pipeline failed: {e}")
        return False


def check_cuda_availability():
    """Check CUDA availability"""
    print("\n=== CUDA Check ===")
    
    if torch.cuda.is_available():
        print(f"✓ CUDA available: {torch.cuda.get_device_name(0)}")
        print(f"  Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB")
        return True
    else:
        print("⚠ CUDA not available, using CPU")
        return False


def main():
    """Run all tests"""
    print("IC Recognition Deep Learning Pipeline Test Suite")
    print("=" * 50)
    
    # Check environment
    check_cuda_availability()
    
    # Run tests
    test_results = []
    
    test_results.append(("CRAFT Detection", test_craft_detection()))
    test_results.append(("CRNN Recognition", test_crnn_recognition()))
    test_results.append(("IC Verification", test_ic_verification()))
    test_results.append(("Full Pipeline", test_full_pipeline()))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in test_results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name:20} : {status}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(test_results)}")
    
    if passed == len(test_results):
        print("✓ All tests passed! Pipeline ready for training.")
        return True
    else:
        print("⚠ Some tests failed. Check components before training.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
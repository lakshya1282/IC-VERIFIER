#!/usr/bin/env python3
"""
Standalone test for the API - tests directly without HTTP server
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

# Set environment variables
os.environ['MODELS_DIR'] = './models'

from api.inference_api_fixed import DeepLearningInferencePipeline
from utils.image_utils import create_test_image, image_to_base64


def test_pipeline_directly():
    """Test the pipeline directly without HTTP"""
    print("🧪 Testing Deep Learning Pipeline Directly")
    print("=" * 50)
    
    try:
        # Initialize pipeline
        print("Initializing pipeline...")
        pipeline = DeepLearningInferencePipeline(
            models_dir='./models',
            device='cpu'  # Force CPU for testing
        )
        
        # Test health check
        health = pipeline.health_check()
        print(f"✅ Health: {health['status']}")
        print(f"   Ready: {health['ready']}")
        print(f"   Device: {health['device']}")
        
        if not health['ready']:
            print("⚠️  Pipeline not fully ready, but continuing tests...")
        
        # Test cases
        test_cases = [
            ("STM32F407VG", "STMicroelectronics MCU"),
            ("LM358N", "TI Op-Amp"), 
            ("FAKE123", "Fake IC"),
            ("74HC04", "Logic Gate"),
        ]
        
        print("\n=== Testing Image Processing ===")
        
        results = []
        for ic_text, description in test_cases:
            print(f"\nTesting: {ic_text} ({description})")
            
            try:
                # Create test image
                test_image = create_test_image(
                    text=ic_text,
                    width=350,
                    height=120,
                    font_scale=0.9
                )
                
                # Convert to base64
                image_base64 = image_to_base64(test_image)
                
                # Process through pipeline  
                result = pipeline.process_image_base64(
                    image_base64, 
                    confidence_threshold=0.1  # Low threshold for testing
                )
                
                # Extract results
                success = result.get('success', False)
                processing_time = result.get('processing_time', 0)
                overall_status = result.get('overall_status', 'UNKNOWN')
                overall_confidence = result.get('overall_confidence', 0)
                detections = result.get('detections', [])
                
                print(f"   ✅ Status: {overall_status}")
                print(f"   📊 Confidence: {overall_confidence:.3f}")
                print(f"   ⏱️  Time: {processing_time:.3f}s")
                print(f"   🔍 Detections: {len(detections)}")
                
                # Show detection details
                for i, detection in enumerate(detections):
                    recognized_text = detection.get('recognized_text', 'N/A')
                    verification = detection.get('verification', {})
                    v_status = verification.get('status', 'UNKNOWN')
                    v_confidence = verification.get('confidence', 0)
                    
                    print(f"     Detection {i}: '{recognized_text}' -> {v_status} ({v_confidence:.3f})")
                
                results.append({
                    'input': ic_text,
                    'success': success,
                    'status': overall_status,
                    'confidence': overall_confidence,
                    'processing_time': processing_time,
                    'detections': len(detections)
                })
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                results.append({
                    'input': ic_text,
                    'success': False,
                    'error': str(e)
                })
        
        # Get stats
        print("\n=== Pipeline Statistics ===")
        stats = pipeline.get_stats()
        print(f"Total Requests: {stats.get('total_requests', 0)}")
        print(f"Success Rate: {stats.get('success_rate', 0):.1%}")
        print(f"Avg Processing Time: {stats.get('average_processing_time', 0):.3f}s")
        
        model_info = stats.get('model_info', {})
        print(f"Models: Detection={model_info.get('detection_model', 'N/A')}, "
              f"Recognition={model_info.get('recognition_model', 'N/A')}, "
              f"Verification={model_info.get('verification_model', 'N/A')}")
        
        # Summary
        print("\n=== Test Summary ===")
        successful = sum(1 for r in results if r.get('success', False))
        print(f"Successful tests: {successful}/{len(results)}")
        
        for result in results:
            input_text = result['input']
            if result.get('success', False):
                status = result.get('status', 'UNKNOWN')
                confidence = result.get('confidence', 0)
                time_ms = result.get('processing_time', 0) * 1000
                print(f"  {input_text:12} -> {status:15} ({confidence:.3f}) [{time_ms:.0f}ms]")
            else:
                error = result.get('error', 'Unknown error')
                print(f"  {input_text:12} -> ERROR: {error}")
        
        if successful > 0:
            print("\n✅ Deep Learning Pipeline is working!")
            return True
        else:
            print("\n❌ Pipeline has issues")
            return False
            
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_pipeline_directly()
    print(f"\n🏁 Test {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)
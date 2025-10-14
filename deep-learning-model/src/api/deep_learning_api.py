"""
Deep Learning Inference API for IC Recognition & Verification
Integrates with existing Flask API system
"""

import os
import sys
import time
import torch
import cv2
import numpy as np
from PIL import Image
import base64
import io
import logging
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from detection.craft_detector import CRAFTDetector
from recognition.crnn_recognizer import CRNNRecognizer
from verification.ic_verifier_fixed import ICVerifier

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DeepLearningInferencePipeline:
    """
    Complete deep learning inference pipeline for IC recognition and verification
    """
    
    def __init__(self, models_dir='./models', device='auto'):
        """
        Initialize inference pipeline with trained models
        
        Args:
            models_dir: Directory containing trained model files
            device: 'cuda', 'cpu', or 'auto'
        """
        
        self.models_dir = Path(models_dir)
        
        # Auto-detect device
        if device == 'auto':
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
            
        logger.info(f"Initializing inference pipeline on device: {self.device}")
        
        # Initialize models
        self.detector = None
        self.recognizer = None
        self.verifier = None
        
        # Load models
        self._load_models()
        
        # Performance tracking
        self.inference_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'average_processing_time': 0.0,
            'detection_accuracy': 0.0,
            'recognition_accuracy': 0.0,
            'verification_accuracy': 0.0
        }
    
    def _load_models(self):
        """Load all trained models"""
        
        try:
            # Load CRAFT detection model
            craft_model_path = self.models_dir / 'craft_model.pth'
            if craft_model_path.exists():
                logger.info("Loading CRAFT detection model...")
                self.detector = CRAFTDetector(
                    model_path=str(craft_model_path),
                    device=self.device
                )
                logger.info("CRAFT model loaded successfully")
            else:
                logger.warning("CRAFT model not found, using default model")
                self.detector = CRAFTDetector(device=self.device)
            
            # Load CRNN recognition model
            crnn_model_path = self.models_dir / 'crnn_model.pth'
            if crnn_model_path.exists():
                logger.info("Loading CRNN recognition model...")
                self.recognizer = CRNNRecognizer(
                    model_path=str(crnn_model_path),
                    device=self.device
                )
                logger.info("CRNN model loaded successfully")
            else:
                logger.warning("CRNN model not found, using default model")
                self.recognizer = CRNNRecognizer(device=self.device)
            
            # Load verification model
            verification_model_path = self.models_dir / 'verification_model.pth'
            if verification_model_path.exists():
                logger.info("Loading verification model...")
                self.verifier = ICVerifier(
                    model_path=str(verification_model_path),
                    device=self.device
                )
                logger.info("Verification model loaded successfully")
            else:
                logger.warning("Verification model not found, using rule-based verification")
                self.verifier = ICVerifier(device=self.device)
                
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            raise
    
    def process_image_base64(self, image_base64_data, confidence_threshold=0.6):
        """
        Process base64 encoded image through complete pipeline
        
        Args:
            image_base64_data: Base64 encoded image data
            confidence_threshold: Minimum confidence threshold
            
        Returns:
            Dictionary with complete processing results
        """
        
        start_time = time.time()
        
        try:
            # Decode base64 image
            image = self._decode_base64_image(image_base64_data)
            
            # Process through pipeline
            result = self.process_image(image, confidence_threshold)
            
            # Update statistics
            processing_time = time.time() - start_time
            self._update_stats(processing_time, success=True)
            
            result['processing_time'] = processing_time
            return result
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            self._update_stats(0, success=False)
            
            return {
                'error': str(e),
                'processing_time': time.time() - start_time,
                'success': False
            }
    
    def process_image(self, image, confidence_threshold=0.6):
        """
        Process image through complete deep learning pipeline
        
        Args:
            image: OpenCV image (numpy array)
            confidence_threshold: Minimum confidence threshold
            
        Returns:
            Dictionary with complete processing results
        """
        
        result = {\n            'success': True,\n            'detections': [],\n            'recognitions': [],\n            'verifications': [],\n            'summary': {\n                'total_detections': 0,\n                'authentic_count': 0,\n                'fraud_count': 0,\n                'unknown_count': 0\n            }\n        }\n        \n        try:\n            # Stage 1: Text Detection\n            logger.info(\"Starting text detection...\")\n            detection_start = time.time()\n            \n            boxes, scores, region_map, affinity_map = self.detector.detect_text(\n                image,\n                text_threshold=0.7,\n                low_text=0.4,\n                link_threshold=0.4\n            )\n            \n            detection_time = time.time() - detection_start\n            result['detection_time'] = detection_time\n            result['summary']['total_detections'] = len(boxes)\n            \n            logger.info(f\"Detected {len(boxes)} text regions in {detection_time:.3f}s\")\n            \n            # Stage 2: Text Recognition for each detected region\n            recognition_start = time.time()\n            \n            for i, (box, score) in enumerate(zip(boxes, scores)):\n                try:\n                    # Extract text region\n                    x1, y1, x2, y2 = box.astype(int)\n                    \n                    # Ensure coordinates are within image bounds\n                    h, w = image.shape[:2]\n                    x1, y1 = max(0, x1), max(0, y1)\n                    x2, y2 = min(w, x2), min(h, y2)\n                    \n                    # Skip invalid regions\n                    if x2 <= x1 or y2 <= y1:\n                        continue\n                    \n                    text_region = image[y1:y2, x1:x2]\n                    \n                    # Skip very small regions\n                    if text_region.shape[0] < 8 or text_region.shape[1] < 8:\n                        continue\n                    \n                    # Stage 2: Text Recognition\n                    recognized_text, recognition_confidence = self.recognizer.recognize_from_image(text_region)\n                    \n                    # Filter by confidence\n                    if recognition_confidence < confidence_threshold:\n                        continue\n                    \n                    # Stage 3: IC Verification\n                    verification_result = self.verifier.verify_ic(\n                        recognized_text,\n                        ocr_confidence=recognition_confidence\n                    )\n                    \n                    # Compile results\n                    detection_result = {\n                        'detection_id': i,\n                        'bounding_box': {\n                            'x1': int(x1), 'y1': int(y1),\n                            'x2': int(x2), 'y2': int(y2)\n                        },\n                        'detection_score': float(score),\n                        'recognized_text': recognized_text,\n                        'recognition_confidence': float(recognition_confidence),\n                        'verification': verification_result\n                    }\n                    \n                    result['detections'].append(detection_result)\n                    result['recognitions'].append({\n                        'text': recognized_text,\n                        'confidence': recognition_confidence\n                    })\n                    result['verifications'].append(verification_result)\n                    \n                    # Update summary counts\n                    if verification_result['status'] == 'AUTHENTIC':\n                        result['summary']['authentic_count'] += 1\n                    elif verification_result['status'] == 'FRAUD/UNKNOWN':\n                        result['summary']['fraud_count'] += 1\n                    else:\n                        result['summary']['unknown_count'] += 1\n                        \n                except Exception as e:\n                    logger.warning(f\"Error processing detection {i}: {e}\")\n                    continue\n            \n            recognition_time = time.time() - recognition_start\n            result['recognition_time'] = recognition_time\n            \n            # Overall assessment\n            total_verified = len(result['verifications'])\n            if total_verified > 0:\n                authentic_ratio = result['summary']['authentic_count'] / total_verified\n                \n                if authentic_ratio >= 0.8:\n                    overall_status = 'MOSTLY_AUTHENTIC'\n                elif authentic_ratio >= 0.5:\n                    overall_status = 'MIXED'\n                else:\n                    overall_status = 'MOSTLY_FRAUD'\n            else:\n                overall_status = 'NO_TEXT_DETECTED'\n            \n            result['overall_status'] = overall_status\n            result['overall_confidence'] = np.mean([\n                v['confidence'] for v in result['verifications']\n            ]) if result['verifications'] else 0.0\n            \n            logger.info(f\"Pipeline completed: {overall_status} ({total_verified} items processed)\")\n            \n        except Exception as e:\n            logger.error(f\"Pipeline error: {e}\")\n            result['success'] = False\n            result['error'] = str(e)\n            result['traceback'] = traceback.format_exc()\n        \n        return result\n    \n    def _decode_base64_image(self, image_base64_data):\n        \"\"\"Decode base64 image data to OpenCV format\"\"\"\n        \n        try:\n            # Remove data URL prefix if present\n            if ',' in image_base64_data:\n                image_base64_data = image_base64_data.split(',')[1]\n            \n            # Decode base64\n            image_bytes = base64.b64decode(image_base64_data)\n            image = Image.open(io.BytesIO(image_bytes))\n            \n            # Convert to OpenCV format\n            image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)\n            \n            return image_cv\n            \n        except Exception as e:\n            logger.error(f\"Error decoding base64 image: {e}\")\n            raise ValueError(f\"Invalid image data: {e}\")\n    \n    def _update_stats(self, processing_time, success=True):\n        \"\"\"Update performance statistics\"\"\"\n        \n        self.inference_stats['total_requests'] += 1\n        \n        if success:\n            self.inference_stats['successful_requests'] += 1\n        \n        # Update average processing time\n        total_requests = self.inference_stats['total_requests']\n        current_avg = self.inference_stats['average_processing_time']\n        self.inference_stats['average_processing_time'] = (\n            (current_avg * (total_requests - 1) + processing_time) / total_requests\n        )\n    \n    def get_stats(self):\n        \"\"\"Get performance statistics\"\"\"\n        \n        success_rate = (\n            self.inference_stats['successful_requests'] / \n            max(1, self.inference_stats['total_requests'])\n        )\n        \n        return {\n            **self.inference_stats,\n            'success_rate': success_rate,\n            'model_info': {\n                'detection_model': 'CRAFT' if self.detector else 'None',\n                'recognition_model': 'CRNN' if self.recognizer else 'None',\n                'verification_model': 'Deep Learning' if self.verifier and self.verifier.is_trained else 'Rule-based',\n                'device': self.device\n            }\n        }\n    \n    def health_check(self):\n        \"\"\"Check if all models are loaded and ready\"\"\"\n        \n        return {\n            'status': 'healthy',\n            'models_loaded': {\n                'detector': self.detector is not None,\n                'recognizer': self.recognizer is not None,\n                'verifier': self.verifier is not None\n            },\n            'device': self.device,\n            'ready': all([\n                self.detector is not None,\n                self.recognizer is not None,\n                self.verifier is not None\n            ])\n        }\n\n\n# Flask API Integration\napp = Flask(__name__)\nCORS(app)\n\n# Global inference pipeline\npipeline = None\n\n\ndef initialize_pipeline():\n    \"\"\"Initialize the deep learning pipeline\"\"\"\n    global pipeline\n    \n    try:\n        models_dir = os.environ.get('MODELS_DIR', './models')\n        device = os.environ.get('INFERENCE_DEVICE', 'auto')\n        \n        logger.info(f\"Initializing pipeline with models from: {models_dir}\")\n        pipeline = DeepLearningInferencePipeline(models_dir=models_dir, device=device)\n        \n        logger.info(\"Deep learning pipeline initialized successfully\")\n        return True\n        \n    except Exception as e:\n        logger.error(f\"Failed to initialize pipeline: {e}\")\n        return False\n\n\n@app.route('/api/deep-learning/health', methods=['GET'])\ndef health_check():\n    \"\"\"Deep learning pipeline health check\"\"\"\n    \n    if pipeline is None:\n        return jsonify({\n            'status': 'unhealthy',\n            'error': 'Pipeline not initialized',\n            'ready': False\n        }), 500\n    \n    try:\n        health_status = pipeline.health_check()\n        return jsonify(health_status)\n        \n    except Exception as e:\n        return jsonify({\n            'status': 'unhealthy',\n            'error': str(e),\n            'ready': False\n        }), 500\n\n\n@app.route('/api/deep-learning/verify-image-advanced', methods=['POST'])\ndef verify_image_advanced():\n    \"\"\"Advanced image verification using deep learning pipeline\"\"\"\n    \n    if pipeline is None:\n        return jsonify({\n            'error': 'Deep learning pipeline not initialized'\n        }), 500\n    \n    try:\n        # Get request data\n        data = request.get_json()\n        \n        if not data or 'image_base64' not in data:\n            return jsonify({\n                'error': 'Missing image_base64 field in request'\n            }), 400\n        \n        image_base64 = data['image_base64']\n        confidence_threshold = data.get('confidence_threshold', 0.6)\n        \n        # Process image through pipeline\n        result = pipeline.process_image_base64(image_base64, confidence_threshold)\n        \n        return jsonify(result)\n        \n    except Exception as e:\n        logger.error(f\"Error in advanced verification: {e}\")\n        return jsonify({\n            'error': str(e),\n            'success': False\n        }), 500\n\n\n@app.route('/api/deep-learning/verify-text-advanced', methods=['POST'])\ndef verify_text_advanced():\n    \"\"\"Advanced text verification using deep learning verification model\"\"\"\n    \n    if pipeline is None:\n        return jsonify({\n            'error': 'Deep learning pipeline not initialized'\n        }), 500\n    \n    try:\n        data = request.get_json()\n        \n        if not data or 'marking_text' not in data:\n            return jsonify({\n                'error': 'Missing marking_text field in request'\n            }), 400\n        \n        marking_text = data['marking_text']\n        ocr_confidence = data.get('ocr_confidence', 1.0)\n        \n        # Verify text using advanced verification model\n        result = pipeline.verifier.verify_ic(marking_text, ocr_confidence)\n        \n        return jsonify(result)\n        \n    except Exception as e:\n        logger.error(f\"Error in advanced text verification: {e}\")\n        return jsonify({\n            'error': str(e)\n        }), 500\n\n\n@app.route('/api/deep-learning/stats', methods=['GET'])\ndef get_pipeline_stats():\n    \"\"\"Get pipeline performance statistics\"\"\"\n    \n    if pipeline is None:\n        return jsonify({\n            'error': 'Pipeline not initialized'\n        }), 500\n    \n    try:\n        stats = pipeline.get_stats()\n        return jsonify(stats)\n        \n    except Exception as e:\n        return jsonify({\n            'error': str(e)\n        }), 500\n\n\n@app.route('/api/deep-learning/benchmark', methods=['POST'])\ndef benchmark_pipeline():\n    \"\"\"Benchmark the pipeline with test data\"\"\"\n    \n    if pipeline is None:\n        return jsonify({\n            'error': 'Pipeline not initialized'\n        }), 500\n    \n    try:\n        # Create test image (dummy)\n        test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)\n        \n        # Run benchmark\n        start_time = time.time()\n        result = pipeline.process_image(test_image)\n        processing_time = time.time() - start_time\n        \n        benchmark_result = {\n            'processing_time': processing_time,\n            'pipeline_status': result.get('success', False),\n            'stages_completed': {\n                'detection': 'detection_time' in result,\n                'recognition': 'recognition_time' in result,\n                'verification': len(result.get('verifications', [])) > 0\n            },\n            'performance_rating': 'Good' if processing_time < 2.0 else 'Slow'\n        }\n        \n        return jsonify(benchmark_result)\n        \n    except Exception as e:\n        return jsonify({\n            'error': str(e)\n        }), 500\n\n\n# Initialize pipeline on startup\nif __name__ == '__main__':\n    logger.info(\"Starting Deep Learning IC Recognition API...\")\n    \n    # Initialize pipeline\n    if initialize_pipeline():\n        logger.info(\"Pipeline initialized successfully\")\n        \n        # Start Flask server\n        app.run(\n            host='0.0.0.0',\n            port=int(os.environ.get('DL_API_PORT', 5001)),\n            debug=os.environ.get('DEBUG', 'false').lower() == 'true'\n        )\n    else:\n        logger.error(\"Failed to initialize pipeline. Exiting.\")\n        sys.exit(1)
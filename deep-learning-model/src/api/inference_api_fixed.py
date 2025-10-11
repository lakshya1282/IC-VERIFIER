"""
Deep Learning Inference API for IC Recognition & Verification (Fixed)
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

from detection.simple_detector import SimpleCRAFTDetector as CRAFTDetector
from recognition.crnn_recognizer import CRNNRecognizer
from verification.ic_verifier_fixed import ICVerifier

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DeepLearningInferencePipeline:
    """Complete deep learning inference pipeline for IC recognition and verification"""
    
    def __init__(self, models_dir='./models', device='auto'):
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
            'average_processing_time': 0.0
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
            else:
                logger.warning("Verification model not found, using rule-based verification")
                self.verifier = ICVerifier(device=self.device)
                
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            raise
    
    def process_image_base64(self, image_base64_data, confidence_threshold=0.6):
        """Process base64 encoded image through complete pipeline"""
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
        """Process image through complete deep learning pipeline"""
        result = {
            'success': True,
            'detections': [],
            'recognitions': [],
            'verifications': [],
            'summary': {
                'total_detections': 0,
                'authentic_count': 0,
                'fraud_count': 0,
                'unknown_count': 0
            }
        }
        
        try:
            # Stage 1: Text Detection
            logger.info("Starting text detection...")
            detection_start = time.time()
            
            boxes, scores, region_map, affinity_map = self.detector.detect_text(
                image,
                text_threshold=0.7,
                low_text=0.4,
                link_threshold=0.4
            )
            
            detection_time = time.time() - detection_start
            result['detection_time'] = detection_time
            result['summary']['total_detections'] = len(boxes)
            
            logger.info(f"Detected {len(boxes)} text regions in {detection_time:.3f}s")
            
            # Stage 2: Text Recognition for each detected region
            recognition_start = time.time()
            
            for i, (box, score) in enumerate(zip(boxes, scores)):
                try:
                    # Extract text region
                    x1, y1, x2, y2 = box.astype(int)
                    
                    # Ensure coordinates are within image bounds
                    h, w = image.shape[:2]
                    x1, y1 = max(0, x1), max(0, y1)
                    x2, y2 = min(w, x2), min(h, y2)
                    
                    # Skip invalid regions
                    if x2 <= x1 or y2 <= y1:
                        continue
                    
                    text_region = image[y1:y2, x1:x2]
                    
                    # Skip very small regions
                    if text_region.shape[0] < 8 or text_region.shape[1] < 8:
                        continue
                    
                    # Stage 2: Text Recognition
                    recognized_text, recognition_confidence = self.recognizer.recognize_from_image(text_region)
                    
                    # Filter by confidence
                    if recognition_confidence < confidence_threshold:
                        continue
                    
                    # Stage 3: IC Verification
                    verification_result = self.verifier.verify_ic(
                        recognized_text,
                        ocr_confidence=recognition_confidence
                    )
                    
                    # Compile results
                    detection_result = {
                        'detection_id': i,
                        'bounding_box': {
                            'x1': int(x1), 'y1': int(y1),
                            'x2': int(x2), 'y2': int(y2)
                        },
                        'detection_score': float(score),
                        'recognized_text': recognized_text,
                        'recognition_confidence': float(recognition_confidence),
                        'verification': verification_result
                    }
                    
                    result['detections'].append(detection_result)
                    result['recognitions'].append({
                        'text': recognized_text,
                        'confidence': recognition_confidence
                    })
                    result['verifications'].append(verification_result)
                    
                    # Update summary counts
                    if verification_result['status'] == 'AUTHENTIC':
                        result['summary']['authentic_count'] += 1
                    elif verification_result['status'] == 'FRAUD/UNKNOWN':
                        result['summary']['fraud_count'] += 1
                    else:
                        result['summary']['unknown_count'] += 1
                        
                except Exception as e:
                    logger.warning(f"Error processing detection {i}: {e}")
                    continue
            
            recognition_time = time.time() - recognition_start
            result['recognition_time'] = recognition_time
            
            # Overall assessment
            total_verified = len(result['verifications'])
            if total_verified > 0:
                authentic_ratio = result['summary']['authentic_count'] / total_verified
                
                if authentic_ratio >= 0.8:
                    overall_status = 'MOSTLY_AUTHENTIC'
                elif authentic_ratio >= 0.5:
                    overall_status = 'MIXED'
                else:
                    overall_status = 'MOSTLY_FRAUD'
            else:
                overall_status = 'NO_TEXT_DETECTED'
            
            result['overall_status'] = overall_status
            result['overall_confidence'] = np.mean([
                v['confidence'] for v in result['verifications']
            ]) if result['verifications'] else 0.0
            
            logger.info(f"Pipeline completed: {overall_status} ({total_verified} items processed)")
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            result['success'] = False
            result['error'] = str(e)
        
        return result
    
    def _decode_base64_image(self, image_base64_data):
        """Decode base64 image data to OpenCV format"""
        try:
            # Remove data URL prefix if present
            if ',' in image_base64_data:
                image_base64_data = image_base64_data.split(',')[1]
            
            # Decode base64
            image_bytes = base64.b64decode(image_base64_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to OpenCV format
            image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            return image_cv
            
        except Exception as e:
            logger.error(f"Error decoding base64 image: {e}")
            raise ValueError(f"Invalid image data: {e}")
    
    def _update_stats(self, processing_time, success=True):
        """Update performance statistics"""
        self.inference_stats['total_requests'] += 1
        
        if success:
            self.inference_stats['successful_requests'] += 1
        
        # Update average processing time
        total_requests = self.inference_stats['total_requests']
        current_avg = self.inference_stats['average_processing_time']
        self.inference_stats['average_processing_time'] = (
            (current_avg * (total_requests - 1) + processing_time) / total_requests
        )
    
    def get_stats(self):
        """Get performance statistics"""
        success_rate = (
            self.inference_stats['successful_requests'] / 
            max(1, self.inference_stats['total_requests'])
        )
        
        return {
            **self.inference_stats,
            'success_rate': success_rate,
            'model_info': {
                'detection_model': 'CRAFT' if self.detector else 'None',
                'recognition_model': 'CRNN' if self.recognizer else 'None',
                'verification_model': 'Deep Learning' if self.verifier and self.verifier.is_trained else 'Rule-based',
                'device': self.device
            }
        }
    
    def health_check(self):
        """Check if all models are loaded and ready"""
        return {
            'status': 'healthy',
            'models_loaded': {
                'detector': self.detector is not None,
                'recognizer': self.recognizer is not None,
                'verifier': self.verifier is not None
            },
            'device': self.device,
            'ready': all([
                self.detector is not None,
                self.recognizer is not None,
                self.verifier is not None
            ])
        }


# Flask API Integration
app = Flask(__name__)
CORS(app)

# Global inference pipeline
pipeline = None


def initialize_pipeline():
    """Initialize the deep learning pipeline"""
    global pipeline
    
    try:
        models_dir = os.environ.get('MODELS_DIR', './models')
        device = os.environ.get('INFERENCE_DEVICE', 'auto')
        
        logger.info(f"Initializing pipeline with models from: {models_dir}")
        pipeline = DeepLearningInferencePipeline(models_dir=models_dir, device=device)
        
        logger.info("Deep learning pipeline initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize pipeline: {e}")
        return False


@app.route('/api/deep-learning/health', methods=['GET'])
def health_check():
    """Deep learning pipeline health check"""
    if pipeline is None:
        return jsonify({
            'status': 'unhealthy',
            'error': 'Pipeline not initialized',
            'ready': False
        }), 500
    
    try:
        health_status = pipeline.health_check()
        return jsonify(health_status)
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'ready': False
        }), 500


@app.route('/api/deep-learning/verify-image-advanced', methods=['POST'])
def verify_image_advanced():
    """Advanced image verification using deep learning pipeline"""
    if pipeline is None:
        return jsonify({
            'error': 'Deep learning pipeline not initialized'
        }), 500
    
    try:
        # Get request data
        data = request.get_json()
        
        if not data or 'image_base64' not in data:
            return jsonify({
                'error': 'Missing image_base64 field in request'
            }), 400
        
        image_base64 = data['image_base64']
        confidence_threshold = data.get('confidence_threshold', 0.6)
        
        # Process image through pipeline
        result = pipeline.process_image_base64(image_base64, confidence_threshold)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in advanced verification: {e}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500


@app.route('/api/deep-learning/stats', methods=['GET'])
def get_pipeline_stats():
    """Get pipeline performance statistics"""
    if pipeline is None:
        return jsonify({
            'error': 'Pipeline not initialized'
        }), 500
    
    try:
        stats = pipeline.get_stats()
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


if __name__ == '__main__':
    logger.info("Starting Deep Learning IC Recognition API...")
    
    # Initialize pipeline
    if initialize_pipeline():
        logger.info("Pipeline initialized successfully")
        
        # Start Flask server
        app.run(
            host='0.0.0.0',
            port=int(os.environ.get('DL_API_PORT', 5001)),
            debug=os.environ.get('DEBUG', 'false').lower() == 'true'
        )
    else:
        logger.error("Failed to initialize pipeline. Exiting.")
        sys.exit(1)
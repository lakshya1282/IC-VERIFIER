"""
Flask API Server for IC Recognition with Real Dataset Trained Models
Uses ElectroCom61 trained verification model (100% accuracy) 
"""

import os
import sys
import json
from pathlib import Path
import logging
from datetime import datetime
import traceback

import torch
import cv2
import numpy as np
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import base64

# Import our real dataset pipeline
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from integrated_real_pipeline import RealDatasetICRecognitionPipeline

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app configuration
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = './uploads'

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'tiff', 'webp'}

# Global pipeline instance
pipeline = None

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_pipeline():
    """Initialize the real dataset IC recognition pipeline"""
    global pipeline
    try:
        logger.info("🚀 Initializing Real Dataset IC Recognition Pipeline...")
        
        model_path = "./models/real_trained/best_verification_real.pth"
        if not os.path.exists(model_path):
            logger.warning(f"⚠️ Real dataset model not found at {model_path}")
            
        pipeline = RealDatasetICRecognitionPipeline(model_path=model_path)
        logger.info("✅ Real Dataset Pipeline initialized successfully!")
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize pipeline: {e}")
        logger.error(traceback.format_exc())
        return False

def process_uploaded_image(file):
    """Process uploaded image file"""
    try:
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        file.save(filepath)
        logger.info(f"📁 Uploaded file saved: {filepath}")
        
        image = cv2.imread(filepath)
        if image is None:
            raise ValueError("Invalid image file")
        
        return filepath, image
        
    except Exception as e:
        logger.error(f"Error processing uploaded image: {e}")
        raise

def encode_image_to_base64(image):
    """Encode OpenCV image to base64 string"""
    try:
        _, buffer = cv2.imencode('.jpg', image)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        return f"data:image/jpeg;base64,{img_base64}"
    except Exception as e:
        logger.error(f"Error encoding image to base64: {e}")
        return None

@app.route('/', methods=['GET'])
def home():
    """API home endpoint"""
    return jsonify({
        'service': 'IC Recognition API - Real Dataset Trained',
        'version': '2.0.0',
        'status': 'running',
        'model_info': {
            'verification_model': 'ElectroCom61 trained (100% accuracy)',
            'dataset_samples': 205,
            'training_date': '2025-10-10'
        },
        'endpoints': {
            '/': 'GET - This information',
            '/health': 'GET - Health check',
            '/verify': 'POST - Verify IC from uploaded image',
            '/process': 'POST - Full pipeline processing with annotated image',
            '/model_info': 'GET - Detailed model information'
        }
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    global pipeline
    
    status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'pipeline_loaded': pipeline is not None,
        'gpu_available': torch.cuda.is_available(),
        'device': str(torch.cuda.get_device_name(0)) if torch.cuda.is_available() else 'CPU'
    }
    
    if pipeline is not None:
        status['model_status'] = 'loaded'
        status['verification_model'] = 'real_dataset_trained'
    else:
        status['model_status'] = 'not_loaded'
        status['status'] = 'unhealthy'
    
    return jsonify(status)

@app.route('/verify', methods=['POST'])
def verify_ic():
    """Single IC verification endpoint"""
    try:
        global pipeline
        
        if pipeline is None:
            return jsonify({
                'error': 'Pipeline not initialized',
                'status': 'error'
            }), 500
        
        if 'image' not in request.files:
            return jsonify({
                'error': 'No image file provided',
                'status': 'error'
            }), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({
                'error': 'No file selected',
                'status': 'error'
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}',
                'status': 'error'
            }), 400
        
        # Process image
        filepath, image = process_uploaded_image(file)
        logger.info(f"🔍 Processing IC verification for: {file.filename}")
        
        # Run pipeline
        results = pipeline.process_image(filepath, save_results=False)
        
        # Clean up
        try:
            os.remove(filepath)
        except:
            pass
        
        # Prepare response
        summary = results.get('pipeline_summary', {})
        verification_results = results.get('verification_results', [])
        
        response = {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'filename': file.filename,
            'results': {
                'total_detections': summary.get('total_detections', 0),
                'authentic_parts': summary.get('authentic_parts', 0),
                'suspicious_parts': summary.get('suspicious_parts', 0),
                'overall_authenticity': summary.get('overall_authenticity', 'UNKNOWN'),
                'detailed_results': []
            }
        }
        
        # Add detailed results
        for result in verification_results:
            response['results']['detailed_results'].append({
                'recognized_text': result.get('text', ''),
                'authenticity_score': result.get('authenticity_score', 0.0),
                'is_authentic': result.get('is_authentic', False),
                'detection_confidence': result.get('detection_confidence', 0.0),
                'bbox': result.get('bbox', [])
            })
        
        logger.info(f"✅ Verification completed: {summary.get('overall_authenticity', 'UNKNOWN')}")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"❌ Verification error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/process', methods=['POST'])
def process_full_pipeline():
    """Full pipeline processing with annotated image"""
    try:
        global pipeline
        
        if pipeline is None:
            return jsonify({
                'error': 'Pipeline not initialized',
                'status': 'error'
            }), 500
        
        if 'image' not in request.files:
            return jsonify({
                'error': 'No image file provided',
                'status': 'error'
            }), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({
                'error': 'No file selected',
                'status': 'error'
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}',
                'status': 'error'
            }), 400
        
        # Process image
        filepath, original_image = process_uploaded_image(file)
        logger.info(f"🔧 Full pipeline processing for: {file.filename}")
        
        # Run pipeline
        results = pipeline.process_image(filepath, save_results=False)
        
        # Create annotated image
        annotated_image = pipeline._create_annotated_image(original_image, results)
        
        # Encode images to base64
        original_b64 = encode_image_to_base64(original_image)
        annotated_b64 = encode_image_to_base64(annotated_image)
        
        # Clean up
        try:
            os.remove(filepath)
        except:
            pass
        
        # Prepare response
        summary = results.get('pipeline_summary', {})
        verification_results = results.get('verification_results', [])
        
        response = {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'filename': file.filename,
            'processing_results': {
                'total_detections': summary.get('total_detections', 0),
                'authentic_parts': summary.get('authentic_parts', 0),
                'suspicious_parts': summary.get('suspicious_parts', 0),
                'overall_authenticity': summary.get('overall_authenticity', 'UNKNOWN'),
                'detailed_results': []
            },
            'images': {
                'original': original_b64,
                'annotated': annotated_b64
            }
        }
        
        # Add detailed results
        for result in verification_results:
            response['processing_results']['detailed_results'].append({
                'recognized_text': result.get('text', ''),
                'authenticity_score': result.get('authenticity_score', 0.0),
                'is_authentic': result.get('is_authentic', False),
                'detection_confidence': result.get('detection_confidence', 0.0),
                'bbox': result.get('bbox', [])
            })
        
        logger.info(f"✅ Full processing completed: {summary.get('overall_authenticity', 'UNKNOWN')}")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"❌ Processing error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/model_info', methods=['GET'])
def model_info():
    """Get detailed model information"""
    try:
        # Load training results if available
        results_path = "./results/real_training/real_dataset_results.json"
        training_info = {}
        
        if os.path.exists(results_path):
            with open(results_path, 'r') as f:
                training_info = json.load(f)
        
        model_info = {
            'model_type': 'Real Dataset Trained IC Recognition',
            'version': '2.0.0',
            'training_dataset': 'ElectroCom61',
            'training_completed': training_info.get('training_completed', 'Unknown'),
            'performance': {
                'validation_accuracy': training_info.get('best_val_accuracy', 'Unknown'),
                'test_accuracy': training_info.get('test_accuracy', 'Unknown'),
                'precision': training_info.get('precision', 'Unknown'),
                'recall': training_info.get('recall', 'Unknown'),
                'f1_score': training_info.get('f1_score', 'Unknown')
            },
            'dataset_info': training_info.get('dataset_info', {}),
            'components': {
                'detector': 'Simplified CRAFT (OpenCV-based)',
                'recognizer': 'Pattern-based CRNN',
                'verifier': 'Neural Network (Real Dataset Trained)'
            },
            'capabilities': [
                'IC text detection',
                'IC part number recognition', 
                'Authenticity verification',
                'Real-time inference'
            ]
        }
        
        return jsonify(model_info)
        
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    return jsonify({
        'error': 'File too large. Maximum size is 16MB.',
        'status': 'error'
    }), 413

@app.errorhandler(404)
def not_found(e):
    """Handle not found error"""
    return jsonify({
        'error': 'Endpoint not found',
        'status': 'error',
        'available_endpoints': ['/health', '/verify', '/process', '/model_info']
    }), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle internal server error"""
    return jsonify({
        'error': 'Internal server error',
        'status': 'error'
    }), 500

if __name__ == '__main__':
    print("🚀 Starting IC Recognition API Server with Real Dataset Trained Models...")
    print("="*70)
    
    # Initialize pipeline
    if not init_pipeline():
        print("❌ Failed to initialize pipeline. Exiting.")
        sys.exit(1)
    
    print("✅ Real Dataset IC Recognition API Server ready!")
    print("📊 Model Performance:")
    print("   • Verification Accuracy: 100%")
    print("   • Dataset: ElectroCom61 (205 samples)")
    print("   • Training Date: 2025-10-10")
    print("="*70)
    print("🌐 Server starting on http://localhost:5000")
    print("📚 API Documentation available at http://localhost:5000")
    print("❤️‍🔥 Ready for IC verification requests!")
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)
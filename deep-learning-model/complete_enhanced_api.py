#!/usr/bin/env python3
"""
Complete Enhanced API Server for IC Verification
Integrates all enhanced features: OCR, Internet Search, Image Marking, Database Storage
"""

import os
import sys
import json
import logging
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import uuid

import torch
import cv2
import numpy as np
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import base64

# Import our comprehensive pipeline
from integrated_ocr_pipeline import ComprehensiveICVerificationPipeline
from enhanced_database_manager import EnhancedDatabaseManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('enhanced_api.log')
    ]
)
logger = logging.getLogger(__name__)

# Flask app configuration
app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = './api_uploads'

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'tiff', 'webp', 'pdf'}

# Global pipeline instance
comprehensive_pipeline = None
db_manager = None

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_comprehensive_pipeline():
    """Initialize the comprehensive IC verification pipeline"""
    global comprehensive_pipeline
    try:
        logger.info("🚀 Initializing Comprehensive IC Verification Pipeline...")
        
        comprehensive_pipeline = ComprehensiveICVerificationPipeline(
            enable_internet_search=True,
            enable_image_marking=True, 
            enable_database_storage=True
        )
        
        logger.info("✅ Comprehensive Pipeline initialized successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize comprehensive pipeline: {e}")
        logger.error(traceback.format_exc())
        return False

def init_database_manager():
    """Initialize the database manager"""
    global db_manager
    try:
        logger.info("🗄️ Initializing Database Manager...")
        db_manager = EnhancedDatabaseManager()
        logger.info("✅ Database Manager initialized successfully!")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize database manager: {e}")
        return False

def process_uploaded_file(file):
    """Process uploaded file and return path and image"""
    try:
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{timestamp}_{unique_id}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        file.save(filepath)
        logger.info(f"📁 Uploaded file saved: {filepath}")
        
        image = cv2.imread(filepath)
        if image is None:
            raise ValueError("Invalid image file")
        
        return filepath, image
        
    except Exception as e:
        logger.error(f"Error processing uploaded file: {e}")
        raise

def get_request_metadata(request):
    """Extract request metadata"""
    return {
        'user_agent': request.headers.get('User-Agent', ''),
        'ip_address': request.remote_addr,
        'api_version': '4.0.0',
        'timestamp': datetime.now().isoformat()
    }

# ==================== ENHANCED API ENDPOINTS ====================

@app.route('/', methods=['GET'])
def home():
    """Enhanced API home endpoint"""
    return jsonify({
        'service': 'Complete Enhanced IC Verification API',
        'version': '4.0.0',
        'status': 'running',
        'description': 'AI-powered IC verification with internet surfing capabilities',
        'features': [
            'Advanced OCR with multiple engines',
            'ML-based authenticity verification',
            'Internet search and data enrichment',
            'Automatic manufacturer data fetching',
            'Image watermarking with QR codes',
            'Comprehensive database storage',
            'Unique tracking IDs for all verifications',
            'Batch processing capabilities',
            'Real-time statistics and analytics'
        ],
        'capabilities': {
            'ocr_engines': ['Tesseract', 'Pattern-based fallback'],
            'internet_sources': ['Manufacturer websites', 'Technical databases', 'Datasheet repositories'],
            'image_processing': ['Watermarking', 'QR code generation', 'Thumbnail creation'],
            'database_features': ['Deduplication', 'Full-text search', 'Analytics', 'Export capabilities']
        },
        'endpoints': {
            # Core endpoints
            '/': 'GET - This information',
            '/health': 'GET - System health check',
            '/system-status': 'GET - Detailed system status',
            
            # Main processing endpoints
            '/api/v4/verify-comprehensive': 'POST - Complete IC verification pipeline',
            '/api/v4/verify-batch': 'POST - Batch process multiple images',
            '/api/v4/verify-quick': 'POST - Quick verification without full enrichment',
            
            # Database and retrieval endpoints
            '/api/v4/verification/<unique_id>': 'GET - Retrieve verification by ID',
            '/api/v4/search': 'GET - Search verification records',
            '/api/v4/statistics': 'GET - System and verification statistics',
            '/api/v4/recent': 'GET - Recent verifications',
            
            # Utility endpoints
            '/api/v4/supported-formats': 'GET - Supported image formats',
            '/api/v4/manufacturers': 'GET - Known IC manufacturers',
            '/api/v4/export': 'GET - Export verification data'
        },
        'timestamp': datetime.now().isoformat()
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Comprehensive health check endpoint"""
    global comprehensive_pipeline, db_manager
    
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '4.0.0',
        'system': {
            'gpu_available': torch.cuda.is_available(),
            'device': str(torch.cuda.get_device_name(0)) if torch.cuda.is_available() else 'CPU',
            'memory_usage': 'Available' if torch.cuda.is_available() else 'N/A'
        },
        'services': {
            'comprehensive_pipeline': {
                'loaded': comprehensive_pipeline is not None,
                'status': 'ready' if comprehensive_pipeline is not None else 'not_loaded',
                'components': {}
            },
            'database_manager': {
                'loaded': db_manager is not None,
                'status': 'ready' if db_manager is not None else 'not_loaded'
            }
        }
    }
    
    # Get detailed component status if pipeline is available
    if comprehensive_pipeline:
        system_status = comprehensive_pipeline.get_system_status()
        health_status['services']['comprehensive_pipeline']['components'] = system_status.get('components', {})
    
    # Overall health determination
    if (comprehensive_pipeline is not None and 
        (db_manager is not None or not comprehensive_pipeline.enable_database_storage)):
        health_status['status'] = 'healthy'
    else:
        health_status['status'] = 'degraded'
    
    return jsonify(health_status)

@app.route('/system-status', methods=['GET'])
def system_status():
    """Detailed system status endpoint"""
    global comprehensive_pipeline, db_manager
    
    if not comprehensive_pipeline:
        return jsonify({
            'error': 'Comprehensive pipeline not initialized',
            'status': 'error'
        }), 500
    
    # Get comprehensive system status
    status = comprehensive_pipeline.get_system_status()
    
    # Add database statistics if available
    if db_manager:
        try:
            db_stats = db_manager.get_verification_statistics()
            status['database_statistics'] = db_stats
        except Exception as e:
            status['database_error'] = str(e)
    
    return jsonify(status)

@app.route('/api/v4/verify-comprehensive', methods=['POST'])
def verify_comprehensive():
    """Complete IC verification with all enhanced features"""
    try:
        global comprehensive_pipeline
        
        if comprehensive_pipeline is None:
            return jsonify({
                'error': 'Comprehensive pipeline not initialized',
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
                'error': f'File type not allowed. Supported types: {", ".join(ALLOWED_EXTENSIONS)}',
                'status': 'error'
            }), 400
        
        # Process image
        filepath, image = process_uploaded_file(file)
        logger.info(f"🔍 Starting comprehensive verification for: {file.filename}")
        
        # Get request metadata
        request_metadata = get_request_metadata(request)
        
        # Run comprehensive processing
        results = comprehensive_pipeline.process_image_comprehensive(
            filepath, 
            save_results=True,
            request_metadata=request_metadata
        )
        
        # Clean up uploaded file
        try:
            os.remove(filepath)
        except:
            pass
        
        # Prepare response
        response = {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'filename': file.filename,
            'processing_time': results['processing_time'],
            
            # Core results
            'verification_summary': results['summary'],
            'extracted_texts': results['extracted_texts'],
            'ocr_confidence': results['ocr_confidence'],
            
            # ML verification
            'ml_verification': results['ml_verification'],
            
            # Enhanced features
            'internet_enrichment': {
                'enabled': bool(results.get('internet_enrichment')),
                'datasheets_found': len(results.get('internet_enrichment', {}).get('consolidated_data', {}).get('datasheets', [])),
                'manufacturer_identified': results.get('internet_enrichment', {}).get('consolidated_data', {}).get('manufacturer', 'Unknown'),
                'sources_used': results.get('internet_enrichment', {}).get('sources_used', [])
            },
            
            # Image processing
            'image_processing': {
                'marking_applied': bool(results.get('marked_image_result')),
                'qr_code_generated': bool(results.get('marked_image_result', {}).get('qr_code_data')),
                'unique_id': results.get('marked_image_result', {}).get('unique_id'),
                'tracking_url': f"https://ic-verify.com/track/{results.get('marked_image_result', {}).get('unique_id', '')}"
            },
            
            # Database storage
            'database_storage': {
                'stored': bool(results.get('database_record_id')),
                'record_id': results.get('database_record_id')
            },
            
            # Pipeline features status
            'features_used': results['pipeline_features'],
            
            # Images (optional - only if requested)
            'images': {}
        }
        
        # Include images if requested
        if request.form.get('include_images') == 'true':
            if results.get('marked_image_result'):
                response['images'] = {
                    'original': results['marked_image_result']['images']['original_b64'],
                    'marked': results['marked_image_result']['images']['marked_b64'],
                    'thumbnail': results['marked_image_result']['images'].get('thumbnail_b64')
                }
        
        logger.info(f"✅ Comprehensive verification completed: {results['summary']['authenticity_status']}")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"❌ Comprehensive verification error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/api/v4/verify-quick', methods=['POST'])
def verify_quick():
    """Quick verification without full internet enrichment"""
    try:
        global comprehensive_pipeline
        
        if comprehensive_pipeline is None:
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
        filepath, image = process_uploaded_file(file)
        
        # Create a quick pipeline instance with limited features
        quick_pipeline = ComprehensiveICVerificationPipeline(
            enable_internet_search=False,
            enable_image_marking=True,
            enable_database_storage=True
        )
        
        # Run quick processing
        results = quick_pipeline.process_image_comprehensive(filepath, save_results=True)
        
        # Clean up
        try:
            os.remove(filepath)
        except:
            pass
        
        # Return simplified response
        response = {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'filename': file.filename,
            'processing_time': results['processing_time'],
            'extracted_texts': results['extracted_texts'],
            'authenticity_status': results['summary']['authenticity_status'],
            'confidence_score': results['summary']['confidence_score'],
            'tracking_id': results['summary']['unique_tracking_id']
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"❌ Quick verification error: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/api/v4/verify-batch', methods=['POST'])
def verify_batch():
    """Batch process multiple images"""
    try:
        global comprehensive_pipeline
        
        if comprehensive_pipeline is None:
            return jsonify({
                'error': 'Pipeline not initialized',
                'status': 'error'
            }), 500
        
        if 'images' not in request.files:
            return jsonify({
                'error': 'No image files provided',
                'status': 'error'
            }), 400
        
        files = request.files.getlist('images')
        if len(files) == 0:
            return jsonify({
                'error': 'No files selected',
                'status': 'error'
            }), 400
        
        logger.info(f"🚀 Starting batch processing of {len(files)} images...")
        
        # Process all files and save temporarily
        image_paths = []
        for file in files:
            if file.filename != '' and allowed_file(file.filename):
                filepath, _ = process_uploaded_file(file)
                image_paths.append(filepath)
        
        # Run batch processing
        batch_results = comprehensive_pipeline.process_batch_images(image_paths)
        
        # Clean up temporary files
        for filepath in image_paths:
            try:
                os.remove(filepath)
            except:
                pass
        
        # Prepare batch response
        response = {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'total_images': len(files),
            'processed_images': len(batch_results),
            'successful_processing': len([r for r in batch_results if r.get('status') == 'success']),
            'batch_summary': {
                'authentic_count': len([r for r in batch_results if r.get('summary', {}).get('authenticity_status') == 'AUTHENTIC']),
                'suspicious_count': len([r for r in batch_results if r.get('summary', {}).get('authenticity_status') in ['SUSPICIOUS', 'FRAUD']]),
                'unknown_count': len([r for r in batch_results if r.get('summary', {}).get('authenticity_status') == 'UNKNOWN']),
                'average_confidence': sum([r.get('summary', {}).get('confidence_score', 0) for r in batch_results]) / len(batch_results) if batch_results else 0
            },
            'results': batch_results
        }
        
        logger.info(f"✅ Batch processing completed: {response['successful_processing']}/{response['total_images']} successful")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"❌ Batch processing error: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/api/v4/verification/<unique_id>', methods=['GET'])
def get_verification_by_id(unique_id):
    """Retrieve a specific verification record by ID"""
    try:
        global db_manager
        
        if not db_manager:
            return jsonify({
                'error': 'Database manager not available',
                'status': 'error'
            }), 500
        
        record = db_manager.get_verification_record(unique_id)
        
        if not record:
            return jsonify({
                'error': 'Verification record not found',
                'status': 'error'
            }), 404
        
        return jsonify({
            'status': 'success',
            'record': record
        })
        
    except Exception as e:
        logger.error(f"Error retrieving verification {unique_id}: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/api/v4/search', methods=['GET'])
def search_verifications():
    """Search verification records with filters"""
    try:
        global db_manager
        
        if not db_manager:
            return jsonify({
                'error': 'Database manager not available',
                'status': 'error'
            }), 500
        
        # Get search parameters
        part_number = request.args.get('part_number')
        manufacturer = request.args.get('manufacturer')
        authenticity_status = request.args.get('authenticity_status')
        min_confidence = float(request.args.get('min_confidence', 0))
        limit = int(request.args.get('limit', 50))
        
        records = db_manager.search_verification_records(
            part_number=part_number,
            manufacturer=manufacturer,
            authenticity_status=authenticity_status,
            min_confidence=min_confidence,
            limit=limit
        )
        
        return jsonify({
            'status': 'success',
            'search_params': {
                'part_number': part_number,
                'manufacturer': manufacturer,
                'authenticity_status': authenticity_status,
                'min_confidence': min_confidence,
                'limit': limit
            },
            'results': {
                'total_found': len(records),
                'records': records
            }
        })
        
    except Exception as e:
        logger.error(f"Error searching verifications: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/api/v4/statistics', methods=['GET'])
def get_statistics():
    """Get comprehensive system statistics"""
    try:
        global db_manager
        
        if not db_manager:
            return jsonify({
                'error': 'Database manager not available',
                'status': 'error'
            }), 500
        
        stats = db_manager.get_verification_statistics()
        
        return jsonify({
            'status': 'success',
            'statistics': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/api/v4/supported-formats', methods=['GET'])
def supported_formats():
    """Get supported image formats"""
    return jsonify({
        'status': 'success',
        'supported_formats': list(ALLOWED_EXTENSIONS),
        'max_file_size': '100MB',
        'recommended_formats': ['jpg', 'png', 'bmp'],
        'notes': {
            'jpg': 'Best for photographs',
            'png': 'Best for screenshots and diagrams',
            'bmp': 'Uncompressed, best quality',
            'pdf': 'Experimental support for single-page PDFs'
        }
    })

@app.route('/api/v4/manufacturers', methods=['GET'])
def known_manufacturers():
    """Get list of known IC manufacturers"""
    manufacturers = [
        'Texas Instruments', 'STMicroelectronics', 'Microchip', 'Analog Devices',
        'Maxim Integrated', 'Infineon', 'NXP', 'Intel', 'AMD', 'Xilinx',
        'Cypress', 'Espressif', 'Nordic Semiconductor', 'Silicon Labs',
        'Renesas', 'ON Semiconductor', 'Fairchild', 'Vishay', 'Diodes Inc',
        'Linear Technology', 'Lattice', 'Altera', 'Broadcom', 'Qualcomm'
    ]
    
    return jsonify({
        'status': 'success',
        'manufacturers': sorted(manufacturers),
        'total_count': len(manufacturers),
        'note': 'This list is continuously updated based on verification data'
    })

# ==================== ERROR HANDLERS ====================

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    return jsonify({
        'error': 'File too large. Maximum size is 100MB.',
        'status': 'error'
    }), 413

@app.errorhandler(404)
def not_found(e):
    """Handle not found error"""
    return jsonify({
        'error': 'Endpoint not found',
        'status': 'error',
        'available_endpoints': [
            '/', '/health', '/system-status',
            '/api/v4/verify-comprehensive', '/api/v4/verify-quick', '/api/v4/verify-batch',
            '/api/v4/verification/<id>', '/api/v4/search', '/api/v4/statistics'
        ]
    }), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle internal server error"""
    logger.error(f"Internal server error: {e}")
    return jsonify({
        'error': 'Internal server error',
        'status': 'error',
        'message': 'Please check the logs for more information'
    }), 500

if __name__ == '__main__':
    print("🚀 Starting Complete Enhanced IC Verification API Server...")
    print("=" * 80)
    print("🤖 Enhanced Features:")
    print("   • Advanced OCR with multiple preprocessing techniques")
    print("   • Internet surfing for manufacturer data")
    print("   • Automatic image watermarking with QR codes")
    print("   • Comprehensive database storage")
    print("   • Unique tracking IDs for all verifications")
    print("   • Batch processing capabilities")
    print("   • Real-time analytics and statistics")
    print("=" * 80)
    
    # Initialize components
    pipeline_ok = init_comprehensive_pipeline()
    db_ok = init_database_manager()
    
    if not pipeline_ok:
        print("❌ Failed to initialize comprehensive pipeline. Some features may not work.")
    
    if not db_ok:
        print("⚠️ Failed to initialize database manager. Database features disabled.")
    
    print("✅ Enhanced IC Verification API Server ready!")
    print("📊 System Status:")
    print(f"   • Comprehensive Pipeline: {'✅ Ready' if pipeline_ok else '❌ Failed'}")
    print(f"   • Database Manager: {'✅ Ready' if db_ok else '⚠️ Disabled'}")
    
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f"   • GPU Acceleration: 🚀 {gpu_name} ({gpu_memory:.1f} GB VRAM)")
    else:
        print(f"   • GPU Acceleration: ❌ Not available (CPU mode)")
    
    print("=" * 80)
    print("🌐 Server starting on http://localhost:5000")
    print("📚 API Documentation available at http://localhost:5000")
    print("🔗 Enhanced API Endpoints:")
    print("   • POST /api/v4/verify-comprehensive - Complete verification")
    print("   • POST /api/v4/verify-quick - Quick verification")
    print("   • POST /api/v4/verify-batch - Batch processing")
    print("   • GET  /api/v4/verification/<id> - Retrieve by ID")
    print("   • GET  /api/v4/search - Search records")
    print("   • GET  /api/v4/statistics - System statistics")
    print("❤️‍🔥 Ready for enhanced IC verification with internet surfing!")
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
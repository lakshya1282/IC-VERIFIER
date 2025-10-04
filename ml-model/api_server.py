from flask import Flask, request, jsonify
from flask_cors import CORS
from train_model import ICVerificationModel
import pytesseract
from PIL import Image
import io
import os
import base64

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Load the trained model
MODEL_PATH = 'ic_model.pkl'
model = None

def load_ml_model():
    """Load the trained ML model"""
    global model
    try:
        if os.path.exists(MODEL_PATH):
            model = ICVerificationModel.load_model(MODEL_PATH)
            print("Model loaded successfully!")
        else:
            print(f"Warning: Model file '{MODEL_PATH}' not found. Please train the model first.")
            model = None
    except Exception as e:
        print(f"Error loading model: {e}")
        model = None

# Load model on startup
load_ml_model()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'model_loaded': model is not None,
        'message': 'IC Verification API is running'
    })

@app.route('/api/verify-text', methods=['POST'])
def verify_text():
    """Verify IC marking from text input"""
    try:
        data = request.get_json()
        marking_text = data.get('marking_text', '').strip()
        
        if not marking_text:
            return jsonify({
                'error': 'Marking text is required'
            }), 400
        
        if model is None:
            return jsonify({
                'error': 'Model not loaded. Please train the model first.'
            }), 500
        
        # Verify IC
        result = model.verify_ic(marking_text)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/verify-image', methods=['POST'])
def verify_image():
    """Verify IC marking from uploaded image using OCR"""
    try:
        # Check if image is provided
        if 'image' not in request.files and 'image_base64' not in request.json:
            return jsonify({
                'error': 'Image is required (either as file upload or base64)'
            }), 400
        
        if model is None:
            return jsonify({
                'error': 'Model not loaded. Please train the model first.'
            }), 500
        
        # Get image from request
        if 'image' in request.files:
            image_file = request.files['image']
            image = Image.open(image_file.stream)
        else:
            # Handle base64 image
            image_data = request.json.get('image_base64')
            # Remove data URL prefix if present
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
        
        # Perform OCR on the image
        extracted_text = pytesseract.image_to_string(image)
        extracted_text = extracted_text.strip()
        
        if not extracted_text:
            return jsonify({
                'error': 'No text could be extracted from the image',
                'extracted_text': ''
            }), 400
        
        # Verify the extracted text
        result = model.verify_ic(extracted_text)
        result['extracted_text'] = extracted_text
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/ic-database', methods=['GET'])
def get_ic_database():
    """Get all IC records from database"""
    try:
        if model is None:
            return jsonify({
                'error': 'Model not loaded'
            }), 500
        
        # Convert dataframe to list of dictionaries
        ic_list = model.df.to_dict('records')
        
        return jsonify({
            'total_count': len(ic_list),
            'ics': ic_list
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/ic-stats', methods=['GET'])
def get_ic_stats():
    """Get statistics about IC database"""
    try:
        if model is None:
            return jsonify({
                'error': 'Model not loaded'
            }), 500
        
        stats = {
            'total_ic_models': len(model.df),
            'total_manufacturers': len(model.df['OEM_Name'].unique()),
            'manufacturers': list(model.df['OEM_Name'].unique()),
            'package_types': list(model.df['Package_Type'].unique()),
            'manufacturer_counts': model.df['OEM_Name'].value_counts().to_dict()
        }
        
        return jsonify(stats)
    
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/reload-model', methods=['POST'])
def reload_model():
    """Reload the ML model"""
    try:
        load_ml_model()
        return jsonify({
            'success': True,
            'message': 'Model reloaded successfully',
            'model_loaded': model is not None
        })
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("=" * 60)
    print("IC Verification API Server")
    print("=" * 60)
    print("Starting server on http://localhost:5000")
    print("\nAvailable endpoints:")
    print("  GET  /api/health          - Health check")
    print("  POST /api/verify-text     - Verify IC from text")
    print("  POST /api/verify-image    - Verify IC from image (OCR)")
    print("  GET  /api/ic-database     - Get all IC records")
    print("  GET  /api/ic-stats        - Get database statistics")
    print("  POST /api/reload-model    - Reload ML model")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)

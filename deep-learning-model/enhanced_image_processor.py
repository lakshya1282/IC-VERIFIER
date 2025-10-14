#!/usr/bin/env python3
"""
Enhanced Image Processing and Marking System for IC Verification
Adds unique identifiers, timestamps, verification status, and metadata to IC images
"""

import os
import cv2
import numpy as np
import qrcode
from PIL import Image, ImageDraw, ImageFont
import uuid
from datetime import datetime
import json
import base64
from typing import Dict, List, Tuple, Optional, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedImageProcessor:
    """Advanced image processing system for IC verification with marking capabilities"""
    
    def __init__(self, output_dir: str = "./processed_images"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Create subdirectories
        self.original_dir = os.path.join(output_dir, "originals")
        self.marked_dir = os.path.join(output_dir, "marked")
        self.thumbnails_dir = os.path.join(output_dir, "thumbnails")
        
        os.makedirs(self.original_dir, exist_ok=True)
        os.makedirs(self.marked_dir, exist_ok=True)
        os.makedirs(self.thumbnails_dir, exist_ok=True)
        
        # Font configurations (try to use system fonts)
        self.font_paths = [
            "/System/Library/Fonts/Arial.ttf",  # macOS
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
            "C:/Windows/Fonts/arial.ttf",  # Windows
            "./fonts/arial.ttf"  # Local fallback
        ]
        
        self.font_size_large = 48
        self.font_size_medium = 32
        self.font_size_small = 24
        
    def generate_unique_identifier(self) -> str:
        """Generate a unique identifier for the IC image"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8].upper()
        return f"IC_{timestamp}_{unique_id}"
    
    def create_qr_code(self, data: str, size: int = 200) -> np.ndarray:
        """Create QR code with the given data"""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            qr_image = qr.make_image(fill_color="black", back_color="white")
            qr_image = qr_image.resize((size, size))
            
            # Convert PIL to OpenCV format
            qr_array = np.array(qr_image)
            if len(qr_array.shape) == 2:  # Grayscale
                qr_array = cv2.cvtColor(qr_array, cv2.COLOR_GRAY2BGR)
            
            return qr_array
            
        except Exception as e:
            logger.error(f"Error creating QR code: {e}")
            # Create a placeholder QR code
            placeholder = np.ones((size, size, 3), dtype=np.uint8) * 255
            cv2.putText(placeholder, "QR", (size//2-20, size//2), 
                       cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 2)
            return placeholder
    
    def get_font(self, size: int) -> Optional[ImageFont.FreeTypeFont]:
        """Get font for PIL text rendering"""
        for font_path in self.font_paths:
            try:
                if os.path.exists(font_path):
                    return ImageFont.truetype(font_path, size)
            except:
                continue
        
        # Fallback to default font
        try:
            return ImageFont.load_default()
        except:
            return None
    
    def add_verification_watermark(self, image: np.ndarray, 
                                 verification_result: Dict[str, Any],
                                 unique_id: str) -> np.ndarray:
        """Add comprehensive verification watermark to image"""
        try:
            # Convert to PIL for better text rendering
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(pil_image)
            
            height, width = image.shape[:2]
            
            # Get fonts
            font_large = self.get_font(self.font_size_large)
            font_medium = self.get_font(self.font_size_medium)
            font_small = self.get_font(self.font_size_small)
            
            # Extract verification information
            authenticity = verification_result.get('overall_authenticity', 'UNKNOWN')
            confidence = verification_result.get('confidence_score', 0.0)
            detected_parts = verification_result.get('total_detections', 0)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Color coding based on authenticity
            if authenticity == 'AUTHENTIC':
                status_color = (0, 255, 0)  # Green
                bg_color = (0, 100, 0, 128)  # Semi-transparent green
            elif authenticity == 'SUSPICIOUS' or authenticity == 'FRAUD':
                status_color = (255, 0, 0)  # Red
                bg_color = (100, 0, 0, 128)  # Semi-transparent red
            else:
                status_color = (255, 165, 0)  # Orange
                bg_color = (100, 100, 0, 128)  # Semi-transparent orange
            
            # Add semi-transparent overlay for text background
            overlay = Image.new('RGBA', pil_image.size, (255, 255, 255, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            
            # Top banner
            banner_height = 120
            overlay_draw.rectangle([0, 0, width, banner_height], fill=bg_color)
            
            # Bottom info panel
            panel_height = 150
            overlay_draw.rectangle([0, height-panel_height, width, height], 
                                 fill=(50, 50, 50, 180))
            
            # Combine overlay with main image
            pil_image = Image.alpha_composite(pil_image.convert('RGBA'), overlay)
            draw = ImageDraw.Draw(pil_image)
            
            # Add main verification status
            status_text = f"STATUS: {authenticity}"
            if font_large:
                draw.text((20, 20), status_text, fill=status_color, font=font_large)
            else:
                # Fallback to cv2 text (convert back to cv2 format temporarily)
                pass
            
            # Add confidence score
            confidence_text = f"Confidence: {confidence:.1%}"
            if font_medium:
                draw.text((20, 70), confidence_text, fill=(255, 255, 255), font=font_medium)
            
            # Add bottom panel information
            y_pos = height - 140
            info_texts = [
                f"Unique ID: {unique_id}",
                f"Processed: {timestamp}",
                f"Components Detected: {detected_parts}",
                f"AI Model: IC Verification v3.0"
            ]
            
            for i, text in enumerate(info_texts):
                if font_small:
                    draw.text((20, y_pos + i*30), text, fill=(255, 255, 255), font=font_small)
            
            # Convert back to OpenCV format
            marked_image = cv2.cvtColor(np.array(pil_image.convert('RGB')), cv2.COLOR_RGB2BGR)
            
            return marked_image
            
        except Exception as e:
            logger.error(f"Error adding verification watermark: {e}")
            # Return original image if watermarking fails
            return image.copy()
    
    def add_qr_code_to_image(self, image: np.ndarray, qr_data: str) -> np.ndarray:
        """Add QR code to the corner of the image"""
        try:
            height, width = image.shape[:2]
            qr_size = min(200, width//5, height//5)  # Adaptive QR size
            
            qr_code = self.create_qr_code(qr_data, qr_size)
            
            # Position QR code in top-right corner
            x_offset = width - qr_size - 20
            y_offset = 20
            
            # Create a white background for QR code
            qr_bg_size = qr_size + 20
            qr_background = np.ones((qr_bg_size, qr_bg_size, 3), dtype=np.uint8) * 255
            
            # Center QR code on background
            bg_offset = 10
            qr_background[bg_offset:bg_offset+qr_size, 
                         bg_offset:bg_offset+qr_size] = qr_code
            
            # Ensure QR code fits in image
            if x_offset + qr_bg_size <= width and y_offset + qr_bg_size <= height:
                image[y_offset:y_offset+qr_bg_size, 
                     x_offset:x_offset+qr_bg_size] = qr_background
            
            return image
            
        except Exception as e:
            logger.error(f"Error adding QR code: {e}")
            return image
    
    def create_thumbnail(self, image: np.ndarray, size: Tuple[int, int] = (300, 300)) -> np.ndarray:
        """Create thumbnail of the image"""
        try:
            thumbnail = cv2.resize(image, size, interpolation=cv2.INTER_AREA)
            return thumbnail
        except Exception as e:
            logger.error(f"Error creating thumbnail: {e}")
            return image
    
    def process_and_mark_image(self, original_image: np.ndarray, 
                              verification_result: Dict[str, Any],
                              extracted_text: List[str],
                              internet_data: Optional[Dict[str, Any]] = None,
                              save_to_disk: bool = True) -> Dict[str, Any]:
        """Comprehensive image processing with marking and metadata generation"""
        try:
            # Generate unique identifier
            unique_id = self.generate_unique_identifier()
            timestamp = datetime.now().isoformat()
            
            # Create QR code data
            qr_data = {
                "id": unique_id,
                "timestamp": timestamp,
                "authenticity": verification_result.get('overall_authenticity', 'UNKNOWN'),
                "detected_text": extracted_text[:3] if extracted_text else [],  # First 3 items
                "url": f"https://ic-verify.com/details/{unique_id}"  # Your verification portal
            }
            qr_json = json.dumps(qr_data, separators=(',', ':'))
            
            # Create marked image
            marked_image = original_image.copy()
            
            # Add verification watermark
            marked_image = self.add_verification_watermark(
                marked_image, verification_result, unique_id
            )
            
            # Add QR code
            marked_image = self.add_qr_code_to_image(marked_image, qr_json)
            
            # Create thumbnail
            thumbnail = self.create_thumbnail(marked_image)
            
            # Prepare file paths
            original_filename = f"{unique_id}_original.jpg"
            marked_filename = f"{unique_id}_marked.jpg"
            thumbnail_filename = f"{unique_id}_thumb.jpg"
            
            original_path = os.path.join(self.original_dir, original_filename)
            marked_path = os.path.join(self.marked_dir, marked_filename)
            thumbnail_path = os.path.join(self.thumbnails_dir, thumbnail_filename)
            
            # Save images to disk if requested
            if save_to_disk:
                cv2.imwrite(original_path, original_image)
                cv2.imwrite(marked_path, marked_image)
                cv2.imwrite(thumbnail_path, thumbnail)
                logger.info(f"Images saved with ID: {unique_id}")
            
            # Create comprehensive metadata
            metadata = {
                "unique_id": unique_id,
                "timestamp": timestamp,
                "verification_result": verification_result,
                "extracted_text": extracted_text,
                "internet_data": internet_data,
                "qr_data": qr_data,
                "file_paths": {
                    "original": original_path if save_to_disk else None,
                    "marked": marked_path if save_to_disk else None,
                    "thumbnail": thumbnail_path if save_to_disk else None
                },
                "image_properties": {
                    "original_shape": original_image.shape,
                    "marked_shape": marked_image.shape,
                    "file_sizes": {}
                },
                "processing_info": {
                    "processed_at": timestamp,
                    "processor_version": "3.0.0",
                    "features_added": ["verification_watermark", "qr_code", "thumbnail"]
                }
            }
            
            # Add file sizes if saved
            if save_to_disk:
                try:
                    metadata["image_properties"]["file_sizes"] = {
                        "original_kb": os.path.getsize(original_path) / 1024,
                        "marked_kb": os.path.getsize(marked_path) / 1024,
                        "thumbnail_kb": os.path.getsize(thumbnail_path) / 1024
                    }
                except:
                    pass
            
            # Convert images to base64 for API responses
            def image_to_base64(img):
                _, buffer = cv2.imencode('.jpg', img)
                return base64.b64encode(buffer).decode('utf-8')
            
            # Return comprehensive result
            result = {
                "status": "success",
                "unique_id": unique_id,
                "metadata": metadata,
                "images": {
                    "original_b64": image_to_base64(original_image),
                    "marked_b64": image_to_base64(marked_image),
                    "thumbnail_b64": image_to_base64(thumbnail)
                },
                "file_paths": metadata["file_paths"] if save_to_disk else None,
                "qr_code_data": qr_json
            }
            
            logger.info(f"Successfully processed image with ID: {unique_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return {
                "status": "error",
                "error": str(e),
                "unique_id": None
            }
    
    def load_processed_image(self, unique_id: str) -> Optional[Dict[str, Any]]:
        """Load previously processed image by unique ID"""
        try:
            original_path = os.path.join(self.original_dir, f"{unique_id}_original.jpg")
            marked_path = os.path.join(self.marked_dir, f"{unique_id}_marked.jpg")
            thumbnail_path = os.path.join(self.thumbnails_dir, f"{unique_id}_thumb.jpg")
            
            if not os.path.exists(marked_path):
                return None
            
            # Load images
            result = {
                "unique_id": unique_id,
                "images": {},
                "file_paths": {
                    "original": original_path if os.path.exists(original_path) else None,
                    "marked": marked_path,
                    "thumbnail": thumbnail_path if os.path.exists(thumbnail_path) else None
                }
            }
            
            # Convert to base64 if needed
            if os.path.exists(marked_path):
                marked_img = cv2.imread(marked_path)
                _, buffer = cv2.imencode('.jpg', marked_img)
                result["images"]["marked_b64"] = base64.b64encode(buffer).decode('utf-8')
            
            return result
            
        except Exception as e:
            logger.error(f"Error loading processed image {unique_id}: {e}")
            return None
    
    def batch_process_images(self, image_batch: List[Tuple[np.ndarray, Dict, List[str]]], 
                           internet_data_batch: Optional[List[Dict]] = None) -> List[Dict[str, Any]]:
        """Process multiple images in batch"""
        results = []
        
        for i, (image, verification_result, extracted_text) in enumerate(image_batch):
            internet_data = internet_data_batch[i] if internet_data_batch and i < len(internet_data_batch) else None
            
            result = self.process_and_mark_image(
                image, verification_result, extracted_text, internet_data
            )
            results.append(result)
            
            logger.info(f"Processed batch item {i+1}/{len(image_batch)}")
        
        return results

# Example usage and testing
if __name__ == "__main__":
    processor = EnhancedImageProcessor()
    
    # Load a test image
    test_image_path = "./test_images/ic_sample.jpg"
    if os.path.exists(test_image_path):
        image = cv2.imread(test_image_path)
        
        # Mock verification result
        verification_result = {
            "overall_authenticity": "AUTHENTIC",
            "confidence_score": 0.95,
            "total_detections": 3,
            "authentic_parts": 3,
            "suspicious_parts": 0
        }
        
        # Mock extracted text
        extracted_text = ["STM32F103C8T6", "ARM", "LQFP48"]
        
        # Process image
        result = processor.process_and_mark_image(
            image, verification_result, extracted_text
        )
        
        if result["status"] == "success":
            print(f"✅ Image processed successfully!")
            print(f"Unique ID: {result['unique_id']}")
            print(f"QR Code Data: {result['qr_code_data']}")
        else:
            print(f"❌ Processing failed: {result['error']}")
    else:
        print("⚠️ Test image not found. Please provide a test IC image.")
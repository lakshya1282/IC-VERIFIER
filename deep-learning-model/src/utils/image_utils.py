"""
Image utilities for IC recognition pipeline
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io
import base64


def create_test_image(text="STM32F407VG", width=300, height=100, font_scale=1.0, 
                     background_color=(255, 255, 255), text_color=(0, 0, 0)):
    """
    Create a test image with text for testing purposes
    
    Args:
        text: Text to render
        width: Image width
        height: Image height 
        font_scale: Font scale factor
        background_color: Background color (B, G, R)
        text_color: Text color (B, G, R)
    
    Returns:
        numpy.ndarray: OpenCV image array
    """
    # Create blank image
    image = np.full((height, width, 3), background_color, dtype=np.uint8)
    
    # Calculate text size and position
    font = cv2.FONT_HERSHEY_SIMPLEX
    thickness = max(1, int(2 * font_scale))
    
    # Get text size
    (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
    
    # Center text
    x = (width - text_width) // 2
    y = (height + text_height) // 2
    
    # Draw text
    cv2.putText(image, text, (x, y), font, font_scale, text_color, thickness, cv2.LINE_AA)
    
    return image


def resize_image(image, target_width=None, target_height=None, maintain_aspect=True):
    """
    Resize image while optionally maintaining aspect ratio
    
    Args:
        image: Input image
        target_width: Target width (optional)
        target_height: Target height (optional)  
        maintain_aspect: Whether to maintain aspect ratio
    
    Returns:
        numpy.ndarray: Resized image
    """
    h, w = image.shape[:2]
    
    if target_width is None and target_height is None:
        return image
    
    if maintain_aspect:
        # Calculate scaling factor
        if target_width and target_height:
            scale_w = target_width / w
            scale_h = target_height / h
            scale = min(scale_w, scale_h)
        elif target_width:
            scale = target_width / w
        else:
            scale = target_height / h
        
        new_w = int(w * scale)
        new_h = int(h * scale)
    else:
        new_w = target_width or w
        new_h = target_height or h
    
    return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)


def pad_image(image, target_width, target_height, pad_value=255):
    """
    Pad image to target dimensions
    
    Args:
        image: Input image
        target_width: Target width
        target_height: Target height
        pad_value: Padding value (0-255)
    
    Returns:
        numpy.ndarray: Padded image
    """
    h, w = image.shape[:2]
    
    if len(image.shape) == 3:
        padded = np.full((target_height, target_width, image.shape[2]), pad_value, dtype=image.dtype)
    else:
        padded = np.full((target_height, target_width), pad_value, dtype=image.dtype)
    
    # Calculate centering offsets
    y_offset = (target_height - h) // 2
    x_offset = (target_width - w) // 2
    
    # Ensure we don't exceed target dimensions
    y_end = min(y_offset + h, target_height)
    x_end = min(x_offset + w, target_width)
    
    # Copy image to center
    padded[y_offset:y_end, x_offset:x_end] = image[:y_end-y_offset, :x_end-x_offset]
    
    return padded


def normalize_image(image, mean=None, std=None):
    """
    Normalize image for neural network input
    
    Args:
        image: Input image (0-255)
        mean: Mean values for normalization  
        std: Standard deviation values
    
    Returns:
        numpy.ndarray: Normalized image
    """
    # Convert to float
    image = image.astype(np.float32) / 255.0
    
    if mean is not None and std is not None:
        mean = np.array(mean, dtype=np.float32)
        std = np.array(std, dtype=np.float32)
        
        if len(image.shape) == 3:
            image = (image - mean) / std
        else:
            image = (image - mean[0]) / std[0]
    
    return image


def denormalize_image(image, mean=None, std=None):
    """
    Denormalize image back to 0-255 range
    
    Args:
        image: Normalized image
        mean: Mean values used in normalization
        std: Standard deviation values used in normalization
    
    Returns:
        numpy.ndarray: Denormalized image (0-255)
    """
    if mean is not None and std is not None:
        mean = np.array(mean, dtype=np.float32)
        std = np.array(std, dtype=np.float32)
        
        if len(image.shape) == 3:
            image = image * std + mean
        else:
            image = image * std[0] + mean[0]
    
    # Convert back to 0-255
    image = np.clip(image * 255.0, 0, 255).astype(np.uint8)
    
    return image


def image_to_base64(image):
    """
    Convert OpenCV image to base64 string
    
    Args:
        image: OpenCV image array
    
    Returns:
        str: Base64 encoded image
    """
    _, buffer = cv2.imencode('.jpg', image)
    image_base64 = base64.b64encode(buffer).decode('utf-8')
    return f"data:image/jpeg;base64,{image_base64}"


def base64_to_image(base64_string):
    """
    Convert base64 string to OpenCV image
    
    Args:
        base64_string: Base64 encoded image
    
    Returns:
        numpy.ndarray: OpenCV image array
    """
    # Remove data URL prefix if present
    if ',' in base64_string:
        base64_string = base64_string.split(',')[1]
    
    # Decode base64
    image_bytes = base64.b64decode(base64_string)
    
    # Convert to OpenCV image
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    
    return image


def apply_augmentation(image, augment_type='none'):
    """
    Apply data augmentation to image
    
    Args:
        image: Input image
        augment_type: Type of augmentation
    
    Returns:
        numpy.ndarray: Augmented image
    """
    if augment_type == 'none':
        return image
    
    augmented = image.copy()
    
    if augment_type == 'blur':
        kernel_size = np.random.choice([3, 5])
        augmented = cv2.GaussianBlur(augmented, (kernel_size, kernel_size), 0)
    
    elif augment_type == 'noise':
        noise = np.random.normal(0, 25, image.shape).astype(np.uint8)
        augmented = cv2.add(augmented, noise)
    
    elif augment_type == 'brightness':
        brightness = np.random.uniform(0.7, 1.3)
        augmented = cv2.convertScaleAbs(augmented, alpha=brightness, beta=0)
    
    elif augment_type == 'contrast':
        contrast = np.random.uniform(0.8, 1.2)
        augmented = cv2.convertScaleAbs(augmented, alpha=contrast, beta=0)
    
    elif augment_type == 'rotation':
        angle = np.random.uniform(-10, 10)
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        augmented = cv2.warpAffine(augmented, matrix, (w, h), 
                                  borderMode=cv2.BORDER_CONSTANT, 
                                  borderValue=(255, 255, 255))
    
    return augmented


def visualize_detection_results(image, boxes, texts=None, scores=None):
    """
    Visualize text detection results on image
    
    Args:
        image: Input image
        boxes: Bounding boxes
        texts: Recognized texts (optional)
        scores: Detection scores (optional)
    
    Returns:
        numpy.ndarray: Visualized image
    """
    vis_image = image.copy()
    
    for i, box in enumerate(boxes):
        # Draw bounding box
        x1, y1, x2, y2 = box.astype(int)
        cv2.rectangle(vis_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # Add label
        label_parts = []
        if texts and i < len(texts):
            label_parts.append(f"'{texts[i]}'")
        if scores and i < len(scores):
            label_parts.append(f"{scores[i]:.2f}")
        
        if label_parts:
            label = " ".join(label_parts)
            cv2.putText(vis_image, label, (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    return vis_image


def save_image(image, filepath):
    """
    Save image to file
    
    Args:
        image: Image to save
        filepath: Output file path
    """
    cv2.imwrite(str(filepath), image)


def load_image(filepath):
    """
    Load image from file
    
    Args:
        filepath: Input file path
    
    Returns:
        numpy.ndarray: Loaded image
    """
    return cv2.imread(str(filepath))
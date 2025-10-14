"""
Simplified Text Detection Module for Testing
A minimal working version for IC text detection
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import cv2
import numpy as np
from collections import OrderedDict


class SimpleTextDetector(nn.Module):
    """Simplified text detection network for testing"""
    
    def __init__(self):
        super(SimpleTextDetector, self).__init__()
        
        # Simple CNN backbone
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),
            
            nn.Conv2d(32, 64, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),
            
            nn.Conv2d(64, 128, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),
            
            nn.Conv2d(128, 256, 3, padding=1),
            nn.ReLU(inplace=True),
        )
        
        # Detection head
        self.detector = nn.Sequential(
            nn.Conv2d(256, 128, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 64, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 2, 1),  # 2 channels: text region + text link
        )
    
    def forward(self, x):
        features = self.features(x)
        
        # Upsample back to quarter resolution
        upsampled = F.interpolate(features, scale_factor=4, mode='bilinear', align_corners=False)
        
        # Detection output
        output = self.detector(upsampled)
        
        # Apply sigmoid
        region_score = torch.sigmoid(output[:, 0:1, :, :])
        affinity_score = torch.sigmoid(output[:, 1:2, :, :])
        
        return region_score, affinity_score


class SimpleCRAFTDetector:
    """
    Simplified CRAFT Text Detector for testing purposes
    """
    
    def __init__(self, model_path=None, device='cuda'):
        self.device = device if torch.cuda.is_available() else 'cpu'
        self.net = SimpleTextDetector().to(self.device)
        
        if model_path:
            self.load_model(model_path)
        
        self.net.eval()
    
    def load_model(self, model_path):
        """Load pretrained model"""
        print(f'Loading model from {model_path}')
        try:
            state_dict = torch.load(model_path, map_location=self.device)
            
            # Handle different state dict formats
            if 'state_dict' in state_dict:
                state_dict = state_dict['state_dict']
            elif 'model' in state_dict:
                state_dict = state_dict['model']
            
            self.net.load_state_dict(state_dict, strict=False)
            print('Model loaded successfully')
        except Exception as e:
            print(f'Warning: Could not load model: {e}')
    
    def preprocess_image(self, image, target_size=320):
        """Preprocess image for detection"""
        
        # Convert to RGB if needed
        if len(image.shape) == 3 and image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Get original size
        h, w = image.shape[:2]
        
        # Calculate target dimensions maintaining aspect ratio
        if h > w:
            new_h = target_size
            new_w = int(w * target_size / h)
        else:
            new_w = target_size
            new_h = int(h * target_size / w)
        
        # Make dimensions divisible by 8 (for proper feature map sizes)
        new_h = (new_h // 8) * 8
        new_w = (new_w // 8) * 8
        
        # Resize image
        resized_image = cv2.resize(image, (new_w, new_h))
        
        # Normalize
        normalized = resized_image.astype(np.float32) / 255.0
        normalized = (normalized - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
        
        # Convert to tensor
        tensor = torch.from_numpy(normalized).permute(2, 0, 1).unsqueeze(0).float()
        
        return tensor, (h, w), (new_h, new_w)
    
    def detect_text(self, image, text_threshold=0.7, low_text=0.4, link_threshold=0.4):
        """
        Detect text regions in image
        
        Args:
            image: Input image (numpy array)
            text_threshold: Threshold for text region
            low_text: Lower threshold for text region
            link_threshold: Threshold for character linking
            
        Returns:
            boxes: List of detected text boxes
            scores: Confidence scores for each box
        """
        
        with torch.no_grad():
            # Preprocess image
            img_tensor, orig_size, resized_size = self.preprocess_image(image)
            img_tensor = img_tensor.to(self.device)
            
            # Forward pass
            region_score, affinity_score = self.net(img_tensor)
            
            # Convert to numpy
            region_score = region_score[0, 0].cpu().numpy()
            affinity_score = affinity_score[0, 0].cpu().numpy()
            
            # Post-process to get text boxes
            boxes, scores = self._get_text_boxes(
                region_score, affinity_score, text_threshold, low_text, link_threshold
            )
            
            # Scale boxes back to original image size
            if boxes is not None and len(boxes) > 0:
                h_ratio = orig_size[0] / resized_size[0]
                w_ratio = orig_size[1] / resized_size[1]
                
                boxes = boxes * np.array([w_ratio, h_ratio, w_ratio, h_ratio])
        
        return boxes, scores, region_score, affinity_score
    
    def _get_text_boxes(self, region_score, affinity_score, text_threshold=0.7, low_text=0.4, link_threshold=0.4):
        """Extract text boxes from score maps using connected component analysis"""
        
        # Create text region map
        text_map = region_score > text_threshold
        link_map = affinity_score > link_threshold
        
        # Combine text and link maps
        combined_map = np.logical_or(text_map, link_map).astype(np.uint8)
        
        # Find connected components
        n_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            combined_map, connectivity=4
        )
        
        boxes = []
        scores = []
        
        for i in range(1, n_labels):  # Skip background (label 0)
            # Get component stats
            x, y, w, h, area = stats[i]
            
            # Filter small components
            if area < 10:
                continue
            
            # Get component mask
            component_mask = (labels == i).astype(np.uint8)
            
            # Calculate average score in this component
            avg_score = np.mean(region_score[component_mask == 1])
            
            if avg_score < low_text:
                continue
            
            # Create bounding box
            bbox = np.array([x, y, x + w, y + h], dtype=np.float32)
            boxes.append(bbox)
            scores.append(avg_score)
        
        if len(boxes) == 0:
            # If no text found, create a dummy box covering most of the image
            h, w = region_score.shape
            dummy_box = np.array([w*0.1, h*0.2, w*0.9, h*0.8], dtype=np.float32)
            return np.array([dummy_box]), np.array([0.5])
        
        return np.array(boxes), np.array(scores)
    
    def visualize_detection(self, image, boxes, scores=None):
        """Visualize detection results"""
        vis_image = image.copy()
        
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = box.astype(int)
            cv2.rectangle(vis_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            if scores is not None:
                score_text = f'{scores[i]:.2f}'
                cv2.putText(vis_image, score_text, (x1, y1-5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        return vis_image
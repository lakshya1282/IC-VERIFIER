"""
CRAFT Text Detection Module
Character Region Awareness for Text Detection optimized for IC markings
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models
import cv2
import numpy as np
from collections import OrderedDict
import math


class DoubleConv(nn.Module):
    """Double convolution layer for U-Net style architecture"""
    
    def __init__(self, in_ch, mid_ch, out_ch):
        super(DoubleConv, self).__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_ch, mid_ch, kernel_size=1),
            nn.BatchNorm2d(mid_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(mid_ch, out_ch, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        x = self.conv(x)
        return x


class CRAFTNet(nn.Module):
    """
    CRAFT Network for Text Detection
    Outputs region score and affinity score maps
    """
    
    def __init__(self, pretrained=True, freeze_backbone=False):
        super(CRAFTNet, self).__init__()
        
        # Feature extraction backbone (ResNet-50 based VGG style)
        self.backbone = self._build_backbone(pretrained)
        
        if freeze_backbone:
            for param in self.backbone.parameters():
                param.requires_grad = False
        
        # Feature merging layers
        self.upconv1 = DoubleConv(1024, 512, 256)
        self.upconv2 = DoubleConv(512, 256, 128)
        self.upconv3 = DoubleConv(256, 128, 64)
        self.upconv4 = DoubleConv(128, 64, 32)
        
        # Output layers
        num_class = 2  # region score + affinity score
        self.conv_cls = nn.Sequential(
            nn.Conv2d(32, 32, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 32, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 16, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(16, 16, kernel_size=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(16, num_class, kernel_size=1),
        )
        
        # Initialize weights
        self._initialize_weights()
    
    def _build_backbone(self, pretrained=True):
        """Build ResNet-based backbone with VGG-style feature extraction"""
        
        # Load pretrained ResNet-50
        resnet = models.resnet50(pretrained=pretrained)
        
        # Convert to VGG-style sequential layers
        backbone = nn.Sequential(OrderedDict([
            # First block (conv1 + pool1)
            ('conv1_1', nn.Conv2d(3, 64, 3, 1, 1)),
            ('relu1_1', nn.ReLU(inplace=True)),
            ('conv1_2', nn.Conv2d(64, 64, 3, 1, 1)),
            ('relu1_2', nn.ReLU(inplace=True)),
            ('pool1', nn.MaxPool2d(2, 2)),
            
            # Second block
            ('conv2_1', nn.Conv2d(64, 128, 3, 1, 1)),
            ('relu2_1', nn.ReLU(inplace=True)),
            ('conv2_2', nn.Conv2d(128, 128, 3, 1, 1)),
            ('relu2_2', nn.ReLU(inplace=True)),
            ('pool2', nn.MaxPool2d(2, 2)),
            
            # Third block
            ('conv3_1', nn.Conv2d(128, 256, 3, 1, 1)),
            ('relu3_1', nn.ReLU(inplace=True)),
            ('conv3_2', nn.Conv2d(256, 256, 3, 1, 1)),
            ('relu3_2', nn.ReLU(inplace=True)),
            ('conv3_3', nn.Conv2d(256, 256, 3, 1, 1)),
            ('relu3_3', nn.ReLU(inplace=True)),
            ('pool3', nn.MaxPool2d(2, 2)),
            
            # Fourth block
            ('conv4_1', nn.Conv2d(256, 512, 3, 1, 1)),
            ('relu4_1', nn.ReLU(inplace=True)),
            ('conv4_2', nn.Conv2d(512, 512, 3, 1, 1)),
            ('relu4_2', nn.ReLU(inplace=True)),
            ('conv4_3', nn.Conv2d(512, 512, 3, 1, 1)),
            ('relu4_3', nn.ReLU(inplace=True)),
            ('pool4', nn.MaxPool2d(2, 2)),
            
            # Fifth block
            ('conv5_1', nn.Conv2d(512, 512, 3, 1, 1)),
            ('relu5_1', nn.ReLU(inplace=True)),
            ('conv5_2', nn.Conv2d(512, 512, 3, 1, 1)),
            ('relu5_2', nn.ReLU(inplace=True)),
            ('conv5_3', nn.Conv2d(512, 512, 3, 1, 1)),
            ('relu5_3', nn.ReLU(inplace=True)),
        ]))
        
        return backbone
    
    def _initialize_weights(self):
        """Initialize network weights"""
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
    
    def forward(self, x):
        """Forward pass through CRAFT network"""
        
        # Extract multi-scale features
        sources = []
        for k, v in self.backbone._modules.items():
            x = v(x)
            if k in ['relu2_2', 'relu3_3', 'relu4_3', 'relu5_3']:
                sources.append(x)
        
        # sources: [relu2_2, relu3_3, relu4_3, relu5_3]
        # sizes:   [128,     256,     512,     512]
        
        # Upsampling and feature fusion
        y = torch.cat([sources[3], sources[2]], dim=1)  # 512 + 512 = 1024
        y = self.upconv1(y)  # -> 256
        y = F.interpolate(y, size=sources[1].size()[2:], mode='bilinear', align_corners=False)
        
        y = torch.cat([y, sources[1]], dim=1)  # 256 + 256 = 512
        y = self.upconv2(y)  # -> 128
        y = F.interpolate(y, size=sources[0].size()[2:], mode='bilinear', align_corners=False)
        
        y = torch.cat([y, sources[0]], dim=1)  # 128 + 128 = 256
        y = self.upconv3(y)  # -> 64
        y = F.interpolate(y, scale_factor=2, mode='bilinear', align_corners=False)
        
        # Final upsampling
        feature = self.upconv4(torch.cat([y, torch.zeros_like(y)[:, :64, :, :]], dim=1))  # -> 32
        y = self.conv_cls(feature)  # -> 2
        
        # Apply sigmoid to get probability maps
        region_score = torch.sigmoid(y[:, 0:1, :, :])
        affinity_score = torch.sigmoid(y[:, 1:2, :, :])
        
        return region_score, affinity_score


class CRAFTDetector:
    """
    CRAFT Text Detector with post-processing
    """
    
    def __init__(self, model_path=None, device='cuda'):
        self.device = device if torch.cuda.is_available() else 'cpu'
        self.net = CRAFTNet(pretrained=True).to(self.device)
        
        if model_path:
            self.load_model(model_path)
        
        self.net.eval()
    
    def load_model(self, model_path):
        """Load pretrained CRAFT model"""
        print(f'Loading CRAFT model from {model_path}')
        state_dict = torch.load(model_path, map_location=self.device)
        
        # Handle different state dict formats
        if 'state_dict' in state_dict:
            state_dict = state_dict['state_dict']
        
        # Remove 'module.' prefix if present (for DataParallel models)
        new_state_dict = OrderedDict()
        for k, v in state_dict.items():
            name = k[7:] if k.startswith('module.') else k
            new_state_dict[name] = v
        
        self.net.load_state_dict(new_state_dict, strict=False)
        print('CRAFT model loaded successfully')
    
    def preprocess_image(self, image, target_size=640):
        """Preprocess image for CRAFT detection"""
        
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
        
        # Make dimensions divisible by 32 (for proper feature map sizes)
        new_h = (new_h // 32) * 32
        new_w = (new_w // 32) * 32
        
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
            if area < 50:
                continue
            
            # Get component mask
            component_mask = (labels == i).astype(np.uint8)
            
            # Calculate average score in this component
            avg_score = np.mean(region_score[component_mask == 1])
            
            if avg_score < low_text:
                continue
            
            # Find contour of the component
            contours, _ = cv2.findContours(component_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                continue
            
            # Get minimum area rectangle
            contour = contours[0]
            rect = cv2.minAreaRect(contour)
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            
            # Convert to [x1, y1, x2, y2] format
            x_coords = box[:, 0]
            y_coords = box[:, 1]
            x1, y1 = np.min(x_coords), np.min(y_coords)
            x2, y2 = np.max(x_coords), np.max(y_coords)
            
            boxes.append([x1, y1, x2, y2])
            scores.append(avg_score)
        
        if boxes:
            boxes = np.array(boxes, dtype=np.float32)
            scores = np.array(scores, dtype=np.float32)
        else:
            boxes = np.array([])
            scores = np.array([])
        
        return boxes, scores
    
    def visualize_detection(self, image, boxes, scores=None):
        """Visualize detection results"""
        
        vis_image = image.copy()
        
        if boxes is not None and len(boxes) > 0:
            for i, box in enumerate(boxes):
                x1, y1, x2, y2 = box.astype(int)
                
                # Choose color based on score
                if scores is not None and len(scores) > i:
                    score = scores[i]
                    color = (0, int(255 * score), int(255 * (1 - score)))  # Red to green
                else:
                    color = (0, 255, 0)  # Green
                
                cv2.rectangle(vis_image, (x1, y1), (x2, y2), color, 2)
                
                # Add score text
                if scores is not None and len(scores) > i:
                    score_text = f'{scores[i]:.2f}'
                    cv2.putText(vis_image, score_text, (x1, y1-10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        return vis_image


class CRAFTLoss(nn.Module):
    """
    Loss function for CRAFT training
    Combines region loss and affinity loss
    """
    
    def __init__(self, use_ohem=True, ohem_ratio=0.25):
        super(CRAFTLoss, self).__init__()
        self.use_ohem = use_ohem
        self.ohem_ratio = ohem_ratio
    
    def single_image_loss(self, pre_loss, loss_label):
        """Calculate loss for single image with OHEM"""
        batch_size = pre_loss.shape[0]
        sum_loss = torch.mean(pre_loss.view(-1)) * 0
        
        for i in range(batch_size):
            p_loss = pre_loss[i]
            t_loss = loss_label[i]
            
            if self.use_ohem:
                # Online Hard Example Mining
                pos_pixel = (t_loss > 0).float()
                neg_pixel = (t_loss == 0).float()
                
                pos_num = torch.sum(pos_pixel)
                neg_num = torch.sum(neg_pixel)
                
                if pos_num > 0:
                    pos_loss = torch.sum(p_loss * pos_pixel) / pos_num
                else:
                    pos_loss = torch.tensor(0.0, device=p_loss.device)
                
                if neg_num > 0:
                    # Select hard negatives
                    neg_loss_sorted = torch.sort(p_loss * neg_pixel, descending=True)[0]
                    hard_neg_num = min(int(neg_num * self.ohem_ratio), len(neg_loss_sorted))
                    neg_loss = torch.mean(neg_loss_sorted[:hard_neg_num])
                else:
                    neg_loss = torch.tensor(0.0, device=p_loss.device)
                
                sum_loss = sum_loss + pos_loss + neg_loss
            else:
                # Standard MSE loss
                sum_loss = sum_loss + torch.mean(p_loss)
        
        return sum_loss
    
    def forward(self, region_pred, affinity_pred, region_gt, affinity_gt, confidence_mask):
        """
        Forward pass for loss calculation
        
        Args:
            region_pred: Predicted region score map
            affinity_pred: Predicted affinity score map  
            region_gt: Ground truth region score map
            affinity_gt: Ground truth affinity score map
            confidence_mask: Confidence mask for training
        """
        
        # Apply confidence mask
        region_pred_masked = region_pred * confidence_mask
        region_gt_masked = region_gt * confidence_mask
        affinity_pred_masked = affinity_pred * confidence_mask
        affinity_gt_masked = affinity_gt * confidence_mask
        
        # Calculate MSE loss
        region_loss_raw = torch.pow(region_pred_masked - region_gt_masked, 2)
        affinity_loss_raw = torch.pow(affinity_pred_masked - affinity_gt_masked, 2)
        
        # Apply OHEM if enabled
        region_loss = self.single_image_loss(region_loss_raw, region_gt_masked)
        affinity_loss = self.single_image_loss(affinity_loss_raw, affinity_gt_masked)
        
        # Total loss
        total_loss = region_loss + affinity_loss
        
        return total_loss, region_loss, affinity_loss


if __name__ == "__main__":
    # Test CRAFT detector
    detector = CRAFTDetector()
    
    # Create dummy image
    test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    # Detect text
    boxes, scores, region_map, affinity_map = detector.detect_text(test_image)
    
    print(f"Detected {len(boxes)} text regions")
    if len(boxes) > 0:
        print(f"Boxes shape: {boxes.shape}")
        print(f"Scores: {scores}")
    
    # Visualize
    vis_image = detector.visualize_detection(test_image, boxes, scores)
    print("Detection visualization created")
#!/usr/bin/env python3
"""
Simplified Training Script for IC Recognition Pipeline
Trains models on generated synthetic dataset
"""

import os
import sys
import json
import yaml
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import cv2
import numpy as np
from pathlib import Path
import logging
from tqdm import tqdm
import argparse

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from detection.simple_detector import SimpleCRAFTDetector, SimpleTextDetector
from recognition.crnn_recognizer import CRNNRecognizer, CRNNNet, LabelConverter, CTCLoss
from verification.ic_verifier_fixed import ICVerifier


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ICDataset(Dataset):
    """Dataset for IC recognition training"""
    
    def __init__(self, annotations, data_root, split='train', task='detection'):
        self.annotations = [ann for ann in annotations if ann['split'] == split]
        self.data_root = Path(data_root)
        self.task = task
        
    def __len__(self):
        return len(self.annotations)
    
    def __getitem__(self, idx):
        ann = self.annotations[idx]
        
        # Load image
        image_path = self.data_root / ann['image_path']
        image = cv2.imread(str(image_path))
        
        if self.task == 'detection':
            return self._get_detection_item(image, ann)
        elif self.task == 'recognition':
            return self._get_recognition_item(image, ann)
        else:
            raise ValueError(f"Unknown task: {self.task}")
    
    def _get_detection_item(self, image, ann):
        """Prepare detection training item"""
        # Resize image
        h, w = image.shape[:2]
        target_size = 320
        
        if h > w:
            new_h = target_size
            new_w = int(w * target_size / h)
        else:
            new_w = target_size
            new_h = int(h * target_size / w)
        
        image = cv2.resize(image, (new_w, new_h))
        
        # Create simple ground truth maps
        region_map = np.zeros((new_h, new_w), dtype=np.float32)
        affinity_map = np.zeros((new_h, new_w), dtype=np.float32)
        
        # Scale bboxes
        h_ratio = new_h / h
        w_ratio = new_w / w
        
        for bbox in ann['bboxes']:
            x1 = int(bbox['x1'] * w_ratio)
            y1 = int(bbox['y1'] * h_ratio)
            x2 = int(bbox['x2'] * w_ratio)
            y2 = int(bbox['y2'] * h_ratio)
            
            # Fill region map
            region_map[y1:y2, x1:x2] = 1.0
            # Create affinity between characters
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            cv2.circle(affinity_map, (center_x, center_y), 10, 1.0, -1)
        
        # Convert to tensors
        image = torch.from_numpy(image).permute(2, 0, 1).float() / 255.0
        region_map = torch.from_numpy(region_map).unsqueeze(0)
        affinity_map = torch.from_numpy(affinity_map).unsqueeze(0)
        
        return image, region_map, affinity_map
    
    def _get_recognition_item(self, image, ann):
        """Prepare recognition training item"""
        # Extract first text region
        if not ann['bboxes']:
            return None
        
        bbox = ann['bboxes'][0]
        x1, y1, x2, y2 = int(bbox['x1']), int(bbox['y1']), int(bbox['x2']), int(bbox['y2'])
        
        # Extract text region
        text_region = image[y1:y2, x1:x2]
        if text_region.shape[0] < 8 or text_region.shape[1] < 8:
            # Create dummy region if too small
            text_region = np.ones((32, 64, 3), dtype=np.uint8) * 255
        
        # Resize to standard size
        text_region = cv2.resize(text_region, (256, 64))
        text_region = cv2.cvtColor(text_region, cv2.COLOR_BGR2GRAY)
        
        # Convert to tensor
        text_region = torch.from_numpy(text_region).unsqueeze(0).float() / 255.0
        
        # Get ground truth text
        gt_text = bbox['text']
        
        return text_region, gt_text


class SimpleTrainer:
    """Simplified trainer for IC recognition models"""
    
    def __init__(self, config):
        self.config = config
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Create directories
        os.makedirs(config['models']['save_dir'], exist_ok=True)
        os.makedirs(config['logging']['log_dir'], exist_ok=True)
        
        # Load dataset
        with open(config['data']['annotations'], 'r') as f:
            self.annotations = json.load(f)
        
        logger.info(f"Loaded {len(self.annotations)} annotations")
    
    def train_detection(self):
        """Train detection model"""
        logger.info("Starting detection training...")
        
        # Create datasets
        train_dataset = ICDataset(self.annotations, self.config['data']['dataset_root'], 'train', 'detection')
        val_dataset = ICDataset(self.annotations, self.config['data']['dataset_root'], 'val', 'detection')
        
        train_loader = DataLoader(train_dataset, batch_size=4, shuffle=True, num_workers=2)
        val_loader = DataLoader(val_dataset, batch_size=4, shuffle=False, num_workers=2)
        
        # Initialize model
        model = SimpleTextDetector().to(self.device)
        optimizer = optim.Adam(model.parameters(), lr=0.001)
        criterion = nn.MSELoss()
        
        best_loss = float('inf')
        epochs = min(20, self.config['training']['craft']['epochs'])  # Reduced epochs for demo
        
        for epoch in range(epochs):
            # Training
            model.train()
            train_loss = 0
            
            pbar = tqdm(train_loader, desc=f'Epoch {epoch+1}/{epochs}')
            for batch_idx, (images, region_maps, affinity_maps) in enumerate(pbar):
                if images is None:
                    continue
                
                images = images.to(self.device)
                region_maps = region_maps.to(self.device)
                affinity_maps = affinity_maps.to(self.device)
                
                optimizer.zero_grad()
                
                pred_region, pred_affinity = model(images)
                
                loss_region = criterion(pred_region, region_maps)
                loss_affinity = criterion(pred_affinity, affinity_maps)
                loss = loss_region + loss_affinity
                
                loss.backward()
                optimizer.step()
                
                train_loss += loss.item()
                pbar.set_postfix({'loss': loss.item()})
            
            # Validation
            model.eval()
            val_loss = 0
            with torch.no_grad():
                for images, region_maps, affinity_maps in val_loader:
                    if images is None:
                        continue
                    
                    images = images.to(self.device)
                    region_maps = region_maps.to(self.device)
                    affinity_maps = affinity_maps.to(self.device)
                    
                    pred_region, pred_affinity = model(images)
                    
                    loss_region = criterion(pred_region, region_maps)
                    loss_affinity = criterion(pred_affinity, affinity_maps)
                    loss = loss_region + loss_affinity
                    
                    val_loss += loss.item()
            
            avg_train_loss = train_loss / len(train_loader)
            avg_val_loss = val_loss / len(val_loader)
            
            logger.info(f'Epoch {epoch+1}: Train Loss: {avg_train_loss:.4f}, Val Loss: {avg_val_loss:.4f}')\
            \n            # Save best model\n            if avg_val_loss < best_loss:\n                best_loss = avg_val_loss\n                torch.save({\n                    'epoch': epoch,\n                    'model_state_dict': model.state_dict(),\n                    'optimizer_state_dict': optimizer.state_dict(),\n                    'loss': best_loss,\n                }, os.path.join(self.config['models']['save_dir'], 'craft_model.pth'))\n                logger.info(f'Saved new best model with loss: {best_loss:.4f}')\n        \n        logger.info(\"Detection training completed!\")\n    \n    def train_recognition(self):\n        \"\"\"Train recognition model\"\"\"\n        logger.info(\"Starting recognition training...\")\n        \n        # Create datasets\n        train_dataset = ICDataset(self.annotations, self.config['data']['dataset_root'], 'train', 'recognition')\n        val_dataset = ICDataset(self.annotations, self.config['data']['dataset_root'], 'val', 'recognition')\n        \n        # Filter out None samples\n        train_samples = [sample for sample in train_dataset if sample is not None]\n        val_samples = [sample for sample in val_dataset if sample is not None]\n        \n        if not train_samples:\n            logger.warning(\"No valid training samples for recognition. Skipping...\")\n            return\n        \n        # Create simple data loader\n        batch_size = 4\n        \n        # Initialize model\n        converter = LabelConverter()\n        model = CRNNNet(\n            img_h=64,\n            img_w=256,\n            num_class=len(converter.character),\n            device=self.device\n        ).to(self.device)\n        \n        optimizer = optim.Adam(model.parameters(), lr=0.001)\n        criterion = CTCLoss()\n        \n        best_loss = float('inf')\n        epochs = min(10, self.config['training']['crnn']['epochs'])  # Reduced epochs for demo\n        \n        for epoch in range(epochs):\n            model.train()\n            train_loss = 0\n            num_batches = 0\n            \n            # Simple batch processing\n            for i in range(0, len(train_samples), batch_size):\n                batch_samples = train_samples[i:i+batch_size]\n                if not batch_samples:\n                    continue\n                \n                try:\n                    # Prepare batch\n                    images = torch.stack([sample[0] for sample in batch_samples])\n                    texts = [sample[1] for sample in batch_samples]\n                    \n                    images = images.to(self.device)\n                    \n                    # Encode texts\n                    text_tensors, text_lengths = converter.encode(texts)\n                    text_tensors = text_tensors.to(self.device)\n                    \n                    optimizer.zero_grad()\n                    \n                    # Forward pass\n                    preds = model(images)\n                    preds_size = torch.IntTensor([preds.size(1)] * preds.size(0))\n                    \n                    # Flatten targets for CTC\n                    targets = torch.cat([text_tensors[i, :text_lengths[i]] for i in range(len(text_lengths))])\n                    \n                    # Calculate loss\n                    loss = criterion(preds, targets, preds_size, text_lengths)\n                    \n                    if not torch.isnan(loss):\n                        loss.backward()\n                        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)\n                        optimizer.step()\n                        train_loss += loss.item()\n                    \n                    num_batches += 1\n                    \n                except Exception as e:\n                    logger.warning(f\"Batch processing error: {e}\")\n                    continue\n            \n            if num_batches > 0:\n                avg_train_loss = train_loss / num_batches\n                logger.info(f'Epoch {epoch+1}: Train Loss: {avg_train_loss:.4f}')\n                \n                # Save model periodically\n                if avg_train_loss < best_loss:\n                    best_loss = avg_train_loss\n                    torch.save({\n                        'epoch': epoch,\n                        'model_state_dict': model.state_dict(),\n                        'optimizer_state_dict': optimizer.state_dict(),\n                        'loss': best_loss,\n                    }, os.path.join(self.config['models']['save_dir'], 'crnn_model.pth'))\n                    logger.info(f'Saved recognition model with loss: {best_loss:.4f}')\n        \n        logger.info(\"Recognition training completed!\")\n    \n    def train_verification(self):\n        \"\"\"Train verification model\"\"\"\n        logger.info(\"Starting verification training...\")\n        \n        try:\n            # Initialize verifier\n            verifier = ICVerifier(\n                ic_database_path=self.config['data']['ic_database'],\n                device=self.device\n            )\n            \n            # Load verification pairs\n            with open(self.config['data']['verification_pairs'], 'r') as f:\n                verification_pairs = json.load(f)\n            \n            logger.info(f\"Loaded {len(verification_pairs)} verification pairs\")\n            \n            # Train the verification model\n            verifier.train_model(\n                verification_pairs=verification_pairs,\n                epochs=min(20, self.config['training']['verification']['epochs']),\n                batch_size=self.config['training']['verification']['batch_size'],\n                learning_rate=self.config['training']['verification']['learning_rate']\n            )\n            \n            # Save trained model\n            model_path = os.path.join(self.config['models']['save_dir'], 'verification_model.pth')\n            verifier.save_model(model_path)\n            logger.info(f\"Saved verification model to {model_path}\")\n            \n        except Exception as e:\n            logger.error(f\"Verification training failed: {e}\")\n            logger.info(\"Skipping verification training...\")\n        \n        logger.info(\"Verification training completed!\")\n    \n    def train_all(self):\n        \"\"\"Train all models in sequence\"\"\"\n        logger.info(\"Starting complete training pipeline...\")\n        \n        try:\n            # Train detection model\n            if self.config['training']['train_detection']:\n                self.train_detection()\n            else:\n                logger.info(\"Skipping detection training\")\n            \n            # Train recognition model\n            if self.config['training']['train_recognition']:\n                self.train_recognition()\n            else:\n                logger.info(\"Skipping recognition training\")\n            \n            # Train verification model\n            if self.config['training']['train_verification']:\n                self.train_verification()\n            else:\n                logger.info(\"Skipping verification training\")\n            \n            logger.info(\"🎉 Complete training pipeline finished successfully!\")\n            \n        except KeyboardInterrupt:\n            logger.info(\"Training interrupted by user\")\n        except Exception as e:\n            logger.error(f\"Training failed: {e}\")\n            raise


def main():\n    parser = argparse.ArgumentParser(description='Train IC Recognition Models')\n    parser.add_argument('--config', default='configs/training_config.yaml', help='Training configuration file')\n    parser.add_argument('--task', choices=['detection', 'recognition', 'verification', 'all'], \n                       default='all', help='Which task to train')\n    \n    args = parser.parse_args()\n    \n    # Load configuration\n    with open(args.config, 'r') as f:\n        config = yaml.safe_load(f)\n    \n    # Initialize trainer\n    trainer = SimpleTrainer(config)\n    \n    # Run training\n    if args.task == 'all':\n        trainer.train_all()\n    elif args.task == 'detection':\n        trainer.train_detection()\n    elif args.task == 'recognition':\n        trainer.train_recognition()\n    elif args.task == 'verification':\n        trainer.train_verification()\n    \n    logger.info(\"Training completed!\")\n\n\nif __name__ == \"__main__\":\n    main()
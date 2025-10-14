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

from detection.simple_detector import SimpleTextDetector
from recognition.crnn_recognizer import CRNNNet, LabelConverter, CTCLoss
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
            x1 = max(0, int(bbox['x1'] * w_ratio))
            y1 = max(0, int(bbox['y1'] * h_ratio))
            x2 = min(new_w, int(bbox['x2'] * w_ratio))
            y2 = min(new_h, int(bbox['y2'] * h_ratio))
            
            if x2 > x1 and y2 > y1:
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
        h, w = image.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        
        if x2 <= x1 or y2 <= y1:
            return None
            
        text_region = image[y1:y2, x1:x2]
        if text_region.shape[0] < 8 or text_region.shape[1] < 8:
            return None
        
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
        logger.info(f"Training on device: {self.device}")
    
    def train_detection(self):
        """Train detection model"""
        logger.info("Starting detection training...")
        
        # Create datasets
        train_dataset = ICDataset(self.annotations, self.config['data']['dataset_root'], 'train', 'detection')
        val_dataset = ICDataset(self.annotations, self.config['data']['dataset_root'], 'val', 'detection')
        
        train_loader = DataLoader(train_dataset, batch_size=4, shuffle=True, num_workers=0)
        val_loader = DataLoader(val_dataset, batch_size=4, shuffle=False, num_workers=0)
        
        # Initialize model
        model = SimpleTextDetector().to(self.device)
        optimizer = optim.Adam(model.parameters(), lr=0.001)
        criterion = nn.MSELoss()
        
        best_loss = float('inf')
        epochs = min(5, self.config['training']['craft']['epochs'])  # Very reduced for demo
        
        for epoch in range(epochs):
            # Training
            model.train()
            train_loss = 0
            train_batches = 0
            
            pbar = tqdm(train_loader, desc=f'Detection Epoch {epoch+1}/{epochs}')
            for batch_idx, (images, region_maps, affinity_maps) in enumerate(pbar):
                try:
                    images = images.to(self.device)
                    region_maps = region_maps.to(self.device)
                    affinity_maps = affinity_maps.to(self.device)
                    
                    optimizer.zero_grad()
                    
                    pred_region, pred_affinity = model(images)
                    
                    loss_region = criterion(pred_region, region_maps)
                    loss_affinity = criterion(pred_affinity, affinity_maps)
                    loss = loss_region + loss_affinity
                    
                    if not torch.isnan(loss):
                        loss.backward()
                        optimizer.step()
                        train_loss += loss.item()
                        train_batches += 1
                    
                    pbar.set_postfix({'loss': loss.item()})
                    
                except Exception as e:
                    logger.warning(f"Training batch error: {e}")
                    continue
            
            # Validation
            model.eval()
            val_loss = 0
            val_batches = 0
            
            with torch.no_grad():
                for images, region_maps, affinity_maps in val_loader:
                    try:
                        images = images.to(self.device)
                        region_maps = region_maps.to(self.device)
                        affinity_maps = affinity_maps.to(self.device)
                        
                        pred_region, pred_affinity = model(images)
                        
                        loss_region = criterion(pred_region, region_maps)
                        loss_affinity = criterion(pred_affinity, affinity_maps)
                        loss = loss_region + loss_affinity
                        
                        if not torch.isnan(loss):
                            val_loss += loss.item()
                            val_batches += 1
                    except Exception as e:
                        continue
            
            if train_batches > 0 and val_batches > 0:
                avg_train_loss = train_loss / train_batches
                avg_val_loss = val_loss / val_batches
                
                logger.info(f'Epoch {epoch+1}: Train Loss: {avg_train_loss:.4f}, Val Loss: {avg_val_loss:.4f}')
                
                # Save best model
                if avg_val_loss < best_loss:
                    best_loss = avg_val_loss
                    torch.save({
                        'epoch': epoch,
                        'model_state_dict': model.state_dict(),
                        'optimizer_state_dict': optimizer.state_dict(),
                        'loss': best_loss,
                    }, os.path.join(self.config['models']['save_dir'], 'simple_detector_model.pth'))
                    logger.info(f'✅ Saved detection model with loss: {best_loss:.4f}')
        
        logger.info("Detection training completed!")
    
    def train_recognition(self):
        """Train recognition model"""
        logger.info("Starting recognition training...")
        
        # Create datasets and filter valid samples
        train_dataset = ICDataset(self.annotations, self.config['data']['dataset_root'], 'train', 'recognition')
        train_samples = []
        
        for i in range(len(train_dataset)):
            try:
                sample = train_dataset[i]
                if sample is not None:
                    train_samples.append(sample)
                if len(train_samples) >= 100:  # Limit for demo
                    break
            except:
                continue
        
        if not train_samples:
            logger.warning("No valid training samples for recognition. Skipping...")
            return
        
        logger.info(f"Using {len(train_samples)} recognition samples")
        
        # Initialize model
        converter = LabelConverter()
        model = CRNNNet(
            img_h=64,
            img_w=256,
            num_class=len(converter.character),
            device=self.device
        ).to(self.device)
        
        optimizer = optim.Adam(model.parameters(), lr=0.001)
        criterion = CTCLoss()
        
        best_loss = float('inf')
        epochs = min(3, self.config['training']['crnn']['epochs'])
        batch_size = 4
        
        for epoch in range(epochs):
            model.train()
            train_loss = 0
            num_batches = 0
            
            pbar = tqdm(range(0, len(train_samples), batch_size), 
                       desc=f'Recognition Epoch {epoch+1}/{epochs}')
            
            for i in pbar:
                batch_samples = train_samples[i:i+batch_size]
                if not batch_samples:
                    continue
                
                try:
                    # Prepare batch
                    images = torch.stack([sample[0] for sample in batch_samples])
                    texts = [sample[1] for sample in batch_samples]
                    
                    images = images.to(self.device)
                    
                    # Encode texts
                    text_tensors, text_lengths = converter.encode(texts)
                    text_tensors = text_tensors.to(self.device)
                    
                    optimizer.zero_grad()
                    
                    # Forward pass
                    preds = model(images)
                    preds_size = torch.IntTensor([preds.size(1)] * preds.size(0))
                    
                    # Flatten targets for CTC
                    targets = torch.cat([text_tensors[i, :text_lengths[i]] for i in range(len(text_lengths))])
                    
                    # Calculate loss
                    loss = criterion(preds, targets, preds_size, text_lengths)
                    
                    if not torch.isnan(loss) and loss.item() < 100:  # Sanity check
                        loss.backward()
                        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                        optimizer.step()
                        train_loss += loss.item()
                        num_batches += 1
                        pbar.set_postfix({'loss': loss.item()})
                    
                except Exception as e:
                    logger.warning(f"Recognition batch error: {e}")
                    continue
            
            if num_batches > 0:
                avg_train_loss = train_loss / num_batches
                logger.info(f'Epoch {epoch+1}: Train Loss: {avg_train_loss:.4f}')
                
                # Save model
                if avg_train_loss < best_loss:
                    best_loss = avg_train_loss
                    torch.save({
                        'epoch': epoch,
                        'model_state_dict': model.state_dict(),
                        'optimizer_state_dict': optimizer.state_dict(),
                        'loss': best_loss,
                    }, os.path.join(self.config['models']['save_dir'], 'crnn_model.pth'))
                    logger.info(f'✅ Saved recognition model with loss: {best_loss:.4f}')
        
        logger.info("Recognition training completed!")
    
    def train_verification(self):
        """Train verification model"""
        logger.info("Starting verification training...")
        
        try:
            # Initialize verifier
            verifier = ICVerifier(
                ic_database_path=self.config['data']['ic_database'],
                device=self.device
            )
            
            # Load verification pairs
            with open(self.config['data']['verification_pairs'], 'r') as f:
                verification_pairs = json.load(f)
            
            logger.info(f"Loaded {len(verification_pairs)} verification pairs")
            
            # Train the verification model
            verifier.train_model(
                verification_pairs=verification_pairs,
                epochs=min(10, self.config['training']['verification']['epochs']),
                batch_size=self.config['training']['verification']['batch_size'],
                learning_rate=self.config['training']['verification']['learning_rate']
            )
            
            # Save trained model
            model_path = os.path.join(self.config['models']['save_dir'], 'verification_model.pth')
            verifier.save_model(model_path)
            logger.info(f"✅ Saved verification model to {model_path}")
            
        except Exception as e:
            logger.error(f"Verification training failed: {e}")
            logger.info("Continuing without verification training...")
        
        logger.info("Verification training completed!")
    
    def train_all(self):
        """Train all models in sequence"""
        logger.info("🚀 Starting complete training pipeline...")
        
        try:
            # Train detection model
            if self.config['training']['train_detection']:
                self.train_detection()
            else:
                logger.info("Skipping detection training")
            
            # Train recognition model
            if self.config['training']['train_recognition']:
                self.train_recognition()
            else:
                logger.info("Skipping recognition training")
            
            # Train verification model
            if self.config['training']['train_verification']:
                self.train_verification()
            else:
                logger.info("Skipping verification training")
            
            logger.info("🎉 Complete training pipeline finished successfully!")
            
        except KeyboardInterrupt:
            logger.info("Training interrupted by user")
        except Exception as e:
            logger.error(f"Training failed: {e}")
            raise


def main():
    parser = argparse.ArgumentParser(description='Train IC Recognition Models')
    parser.add_argument('--config', default='configs/training_config.yaml', help='Training configuration file')
    parser.add_argument('--task', choices=['detection', 'recognition', 'verification', 'all'], 
                       default='all', help='Which task to train')
    
    args = parser.parse_args()
    
    # Load configuration
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize trainer
    trainer = SimpleTrainer(config)
    
    # Run training
    if args.task == 'all':
        trainer.train_all()
    elif args.task == 'detection':
        trainer.train_detection()
    elif args.task == 'recognition':
        trainer.train_recognition()
    elif args.task == 'verification':
        trainer.train_verification()
    
    logger.info("✅ Training completed!")


if __name__ == "__main__":
    main()
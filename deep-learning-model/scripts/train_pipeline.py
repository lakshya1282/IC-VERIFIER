"""
Comprehensive Training Pipeline for IC Recognition & Verification
Includes curriculum learning, data augmentation, and advanced evaluation metrics
"""

import os
import sys
import time
import yaml
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torch.utils.tensorboard import SummaryWriter
import numpy as np
import pandas as pd
import cv2
from PIL import Image
import albumentations as A
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
import logging
from pathlib import Path
import json
import wandb  # For experiment tracking

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.detection.craft_detector import CRAFTNet, CRAFTLoss
from src.recognition.crnn_recognizer import CRNNNet, CTCLoss, LabelConverter, CurriculumLearningScheduler
from src.verification.ic_verifier_fixed import ICVerifier, FeatureExtractor
from src.datasets.data_preprocessing import DataPreprocessor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ICDataset(Dataset):
    """
    Custom dataset for IC images with text detection and recognition annotations
    """
    
    def __init__(self, data_path, split='train', transform=None, curriculum_scheduler=None, epoch=0):
        """
        Args:
            data_path: Path to processed dataset
            split: 'train', 'val', or 'test'
            transform: Albumentations transform pipeline
            curriculum_scheduler: For curriculum learning
            epoch: Current training epoch
        """
        self.data_path = Path(data_path)
        self.split = split
        self.transform = transform
        self.curriculum_scheduler = curriculum_scheduler
        self.epoch = epoch
        
        # Load annotations
        annotations_file = self.data_path / split / 'detection_annotations.json'
        with open(annotations_file, 'r') as f:
            self.annotations = json.load(f)
        
        # Filter samples based on curriculum learning
        if curriculum_scheduler and split == 'train':
            self.annotations = self._apply_curriculum_filter(self.annotations, epoch)
        
        logger.info(f"Loaded {len(self.annotations)} samples for {split} split")
    
    def _apply_curriculum_filter(self, annotations, epoch):
        """Apply curriculum learning filtering based on character quality"""
        if not self.curriculum_scheduler:
            return annotations
        
        difficulty_weights = self.curriculum_scheduler.get_difficulty_weights(epoch)
        filtered_annotations = []
        
        for annotation in annotations:
            for region in annotation.get('text_regions', []):
                attributes = region.get('attributes', {})
                
                # Determine sample difficulty
                if any(attr in ['clear', 'high_quality'] for attr in attributes):
                    difficulty = 'high'
                elif any(attr in ['medium_quality', 'slight_blur'] for attr in attributes):
                    difficulty = 'medium'
                else:
                    difficulty = 'low'
                
                # Include sample based on curriculum weights
                if np.random.random() < difficulty_weights.get(difficulty, 0.0):
                    filtered_annotations.append(annotation)
                    break
        
        logger.info(f"Curriculum filtering: {len(filtered_annotations)} / {len(annotations)} samples included (epoch {epoch})")
        return filtered_annotations
    
    def __len__(self):
        return len(self.annotations)
    
    def __getitem__(self, idx):
        annotation = self.annotations[idx]
        
        # Load image
        image_path = annotation['image_path']
        image = cv2.imread(image_path)
        if image is None:
            # Return dummy data if image fails to load
            image = np.zeros((224, 224, 3), dtype=np.uint8)
        
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Prepare ground truth data
        gt_data = self._prepare_ground_truth(annotation, image.shape)
        
        # Apply augmentations
        if self.transform:
            transformed = self.transform(image=image)
            image = transformed['image']
        
        # Convert to tensor
        if isinstance(image, np.ndarray):
            image = torch.from_numpy(image).permute(2, 0, 1).float() / 255.0
        
        return {
            'image': image,
            'image_path': image_path,
            'gt_data': gt_data,
            'annotation': annotation
        }
    
    def _prepare_ground_truth(self, annotation, image_shape):
        """Prepare ground truth for detection and recognition"""
        h, w = image_shape[:2]
        
        # Detection ground truth
        region_map = np.zeros((h, w), dtype=np.float32)
        affinity_map = np.zeros((h, w), dtype=np.float32)
        confidence_mask = np.ones((h, w), dtype=np.float32)
        
        # Recognition ground truth
        text_labels = []
        
        for region in annotation.get('text_regions', []):
            bbox = region['bbox']  # Normalized coordinates
            text = region.get('text', '')
            
            # Convert normalized bbox to pixel coordinates
            x1, y1, x2, y2 = bbox
            x1, x2 = int(x1 * w), int(x2 * w)
            y1, y2 = int(y1 * h), int(y2 * h)
            
            # Create region map
            region_map[y1:y2, x1:x2] = 1.0
            
            # Create affinity map (simple approach - character adjacency)
            if len(text) > 1:
                char_width = (x2 - x1) // len(text)
                for i in range(len(text) - 1):
                    cx = x1 + (i + 0.5) * char_width
                    affinity_map[y1:y2, int(cx):int(cx + char_width)] = 1.0
            
            text_labels.append(text)
        
        return {
            'region_map': torch.from_numpy(region_map),
            'affinity_map': torch.from_numpy(affinity_map),
            'confidence_mask': torch.from_numpy(confidence_mask),
            'text_labels': text_labels
        }


class EarlyStopping:
    """Early stopping to prevent overfitting"""
    
    def __init__(self, patience=7, min_delta=0, restore_best_weights=True):
        self.patience = patience
        self.min_delta = min_delta
        self.restore_best_weights = restore_best_weights
        self.best_loss = None
        self.counter = 0
        self.best_weights = None
    
    def __call__(self, val_loss, model):
        if self.best_loss is None:
            self.best_loss = val_loss
            self.save_checkpoint(model)
        elif val_loss < self.best_loss - self.min_delta:
            self.best_loss = val_loss
            self.counter = 0
            self.save_checkpoint(model)
        else:
            self.counter += 1
        
        return self.counter >= self.patience
    
    def save_checkpoint(self, model):
        """Save the best model"""
        self.best_weights = model.state_dict().copy()


class MetricsTracker:
    """Track and log training metrics"""
    
    def __init__(self, log_dir='logs', use_wandb=True):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Initialize TensorBoard
        self.writer = SummaryWriter(log_dir / 'tensorboard')
        
        # Initialize Weights & Biases
        self.use_wandb = use_wandb
        if use_wandb:
            try:
                wandb.init(
                    project="ic-recognition-verification",
                    config={
                        "architecture": "CRAFT+CRNN+Verification",
                        "dataset": "ICText-AGCL"
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to initialize wandb: {e}")
                self.use_wandb = False
        
        self.metrics = {
            'train_loss': [],
            'val_loss': [],
            'train_acc': [],
            'val_acc': [],
            'detection_precision': [],
            'detection_recall': [],
            'recognition_accuracy': [],
            'verification_f1': []
        }
    
    def log_metrics(self, epoch, metrics_dict):
        """Log metrics to all tracking systems"""
        
        # Update internal tracking
        for key, value in metrics_dict.items():
            if key in self.metrics:
                self.metrics[key].append(value)
        
        # Log to TensorBoard
        for key, value in metrics_dict.items():
            self.writer.add_scalar(key, value, epoch)
        
        # Log to Weights & Biases
        if self.use_wandb:
            wandb.log(metrics_dict, step=epoch)
        
        # Log to console
        logger.info(f"Epoch {epoch}: " + ", ".join([f"{k}={v:.4f}" for k, v in metrics_dict.items()]))
    
    def log_confusion_matrix(self, cm, class_names, epoch, phase='val'):
        """Log confusion matrix visualization"""
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                   xticklabels=class_names, yticklabels=class_names, ax=ax)
        ax.set_title(f'Confusion Matrix - {phase.title()} (Epoch {epoch})')
        ax.set_ylabel('True Label')
        ax.set_xlabel('Predicted Label')
        
        # Save plot
        plot_path = self.log_dir / f'confusion_matrix_{phase}_epoch_{epoch}.png'
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        
        # Log to TensorBoard
        self.writer.add_figure(f'confusion_matrix/{phase}', fig, epoch)
        
        # Log to wandb
        if self.use_wandb:
            wandb.log({f"confusion_matrix_{phase}": wandb.Image(str(plot_path))}, step=epoch)
        
        plt.close(fig)
    
    def save_metrics(self):
        """Save metrics to file"""
        metrics_df = pd.DataFrame(self.metrics)
        metrics_df.to_csv(self.log_dir / 'training_metrics.csv', index=False)
    
    def close(self):
        """Close logging resources"""
        self.writer.close()
        if self.use_wandb:
            wandb.finish()


class ICTrainingPipeline:
    """
    Complete training pipeline for IC Recognition & Verification
    """
    
    def __init__(self, config_path='configs/training_config.yaml'):
        """
        Initialize training pipeline
        
        Args:
            config_path: Path to training configuration file
        """
        
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Setup device
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Using device: {self.device}")
        
        # Initialize metrics tracker
        self.metrics_tracker = MetricsTracker(
            log_dir=self.config['logging']['log_dir'],
            use_wandb=self.config['logging']['use_wandb']
        )
        
        # Setup data augmentation
        self.train_transform = self._setup_augmentation('train')
        self.val_transform = self._setup_augmentation('val')
        
        # Initialize curriculum learning
        self.curriculum_scheduler = CurriculumLearningScheduler(
            **self.config['curriculum_learning']
        )
        
        # Initialize models
        self._initialize_models()
        
        # Setup optimizers and schedulers
        self._setup_optimizers()
        
        # Initialize early stopping
        self.early_stopping = EarlyStopping(
            **self.config['early_stopping']
        )
    
    def _setup_augmentation(self, phase):
        """Setup data augmentation pipeline"""
        
        if phase == 'train':
            transform = A.Compose([
                A.RandomBrightnessContrast(
                    brightness_limit=0.2, 
                    contrast_limit=0.2, 
                    p=0.7
                ),
                A.HueSaturationValue(
                    hue_shift_limit=10,
                    sat_shift_limit=10,
                    val_shift_limit=10,
                    p=0.5
                ),
                A.RandomRotate90(p=0.3),
                A.ShiftScaleRotate(
                    shift_limit=0.1,
                    scale_limit=0.1,
                    rotate_limit=15,
                    p=0.5
                ),
                A.GaussianBlur(blur_limit=3, p=0.3),
                A.MotionBlur(blur_limit=3, p=0.2),
                A.GaussNoise(var_limit=10, p=0.3),
                A.Perspective(scale=0.05, p=0.3),
                A.Resize(
                    height=self.config['data']['image_size'],
                    width=self.config['data']['image_size']
                ),
                A.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                )
            ])
        else:
            transform = A.Compose([
                A.Resize(
                    height=self.config['data']['image_size'],
                    width=self.config['data']['image_size']
                ),
                A.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                )
            ])
        
        return transform
    
    def _initialize_models(self):
        """Initialize all models"""
        
        # CRAFT Text Detection
        self.craft_model = CRAFTNet(pretrained=True).to(self.device)
        self.craft_criterion = CRAFTLoss()
        
        # CRNN Text Recognition
        label_converter = LabelConverter()
        num_classes = len(label_converter.character)
        
        self.crnn_model = CRNNNet(
            img_h=self.config['models']['crnn']['img_h'],
            img_w=self.config['models']['crnn']['img_w'],
            num_class=num_classes,
            device=self.device
        ).to(self.device)
        self.crnn_criterion = CTCLoss()
        self.label_converter = label_converter
        
        # IC Verification
        self.verifier = ICVerifier(device=self.device)
        
        logger.info("Models initialized successfully")
    
    def _setup_optimizers(self):
        """Setup optimizers and learning rate schedulers"""
        
        # CRAFT optimizer
        self.craft_optimizer = optim.AdamW(
            self.craft_model.parameters(),
            lr=self.config['training']['craft']['learning_rate'],
            weight_decay=self.config['training']['craft']['weight_decay']
        )
        self.craft_scheduler = optim.lr_scheduler.StepLR(
            self.craft_optimizer,
            step_size=self.config['training']['craft']['lr_step_size'],
            gamma=self.config['training']['craft']['lr_gamma']
        )
        
        # CRNN optimizer
        self.crnn_optimizer = optim.AdamW(
            self.crnn_model.parameters(),
            lr=self.config['training']['crnn']['learning_rate'],
            weight_decay=self.config['training']['crnn']['weight_decay']
        )
        self.crnn_scheduler = optim.lr_scheduler.StepLR(
            self.crnn_optimizer,
            step_size=self.config['training']['crnn']['lr_step_size'],
            gamma=self.config['training']['crnn']['lr_gamma']
        )
    
    def create_data_loaders(self, data_path):
        """Create data loaders for training and validation"""
        
        # Training dataset
        train_dataset = ICDataset(
            data_path=data_path,
            split='train',
            transform=self.train_transform,
            curriculum_scheduler=self.curriculum_scheduler
        )
        
        # Validation dataset
        val_dataset = ICDataset(
            data_path=data_path,
            split='val',
            transform=self.val_transform
        )
        
        # Data loaders
        train_loader = DataLoader(
            train_dataset,
            batch_size=self.config['training']['batch_size'],
            shuffle=True,
            num_workers=self.config['training']['num_workers'],
            pin_memory=True
        )
        
        val_loader = DataLoader(
            val_dataset,
            batch_size=self.config['training']['batch_size'],
            shuffle=False,
            num_workers=self.config['training']['num_workers'],
            pin_memory=True
        )
        
        return train_loader, val_loader
    
    def train_detection(self, train_loader, val_loader, epochs):
        """Train CRAFT detection model"""
        
        logger.info("Starting CRAFT detection training...")
        
        for epoch in range(epochs):
            # Update curriculum learning for dataset
            for dataset in [train_loader.dataset]:
                if hasattr(dataset, 'epoch'):
                    dataset.epoch = epoch
            
            # Training phase
            self.craft_model.train()
            train_loss = 0.0
            train_samples = 0
            
            pbar = tqdm(train_loader, desc=f'CRAFT Epoch {epoch+1}/{epochs}')
            for batch in pbar:
                images = batch['image'].to(self.device)
                gt_data = batch['gt_data']
                
                region_gt = gt_data['region_map'].to(self.device)
                affinity_gt = gt_data['affinity_map'].to(self.device)
                confidence_mask = gt_data['confidence_mask'].to(self.device)
                
                # Forward pass
                region_pred, affinity_pred = self.craft_model(images)
                
                # Calculate loss
                loss, region_loss, affinity_loss = self.craft_criterion(
                    region_pred, affinity_pred, region_gt, affinity_gt, confidence_mask
                )
                
                # Backward pass
                self.craft_optimizer.zero_grad()
                loss.backward()
                self.craft_optimizer.step()
                
                # Update metrics
                train_loss += loss.item() * images.size(0)
                train_samples += images.size(0)
                
                pbar.set_postfix({
                    'Loss': f'{loss.item():.4f}',
                    'Region': f'{region_loss.item():.4f}',
                    'Affinity': f'{affinity_loss.item():.4f}'
                })
            
            # Validation phase
            val_loss, val_metrics = self._validate_detection(val_loader)
            
            # Update learning rate
            self.craft_scheduler.step()
            
            # Log metrics
            epoch_metrics = {
                'craft_train_loss': train_loss / train_samples,
                'craft_val_loss': val_loss,
                'craft_precision': val_metrics.get('precision', 0),
                'craft_recall': val_metrics.get('recall', 0),
                'craft_f1': val_metrics.get('f1', 0)
            }
            self.metrics_tracker.log_metrics(epoch, epoch_metrics)
            
            # Early stopping check
            if self.early_stopping(val_loss, self.craft_model):
                logger.info("Early stopping triggered for CRAFT model")
                break
        
        # Restore best weights
        if self.early_stopping.best_weights:
            self.craft_model.load_state_dict(self.early_stopping.best_weights)
        
        logger.info("CRAFT detection training completed")
    
    def _validate_detection(self, val_loader):
        """Validate CRAFT detection model"""
        
        self.craft_model.eval()
        val_loss = 0.0
        val_samples = 0
        
        # Metrics for detection evaluation
        true_positives = 0
        false_positives = 0
        false_negatives = 0
        
        with torch.no_grad():
            for batch in val_loader:
                images = batch['image'].to(self.device)
                gt_data = batch['gt_data']
                
                region_gt = gt_data['region_map'].to(self.device)
                affinity_gt = gt_data['affinity_map'].to(self.device)
                confidence_mask = gt_data['confidence_mask'].to(self.device)
                
                # Forward pass
                region_pred, affinity_pred = self.craft_model(images)
                
                # Calculate loss
                loss, _, _ = self.craft_criterion(
                    region_pred, affinity_pred, region_gt, affinity_gt, confidence_mask
                )
                
                val_loss += loss.item() * images.size(0)
                val_samples += images.size(0)
                
                # Calculate detection metrics (simplified)
                region_pred_binary = (region_pred > 0.5).float()
                region_gt_binary = (region_gt > 0.5).float()
                
                tp = torch.sum(region_pred_binary * region_gt_binary).item()
                fp = torch.sum(region_pred_binary * (1 - region_gt_binary)).item()
                fn = torch.sum((1 - region_pred_binary) * region_gt_binary).item()
                
                true_positives += tp
                false_positives += fp
                false_negatives += fn
        
        # Calculate metrics
        precision = true_positives / (true_positives + false_positives + 1e-8)
        recall = true_positives / (true_positives + false_negatives + 1e-8)
        f1 = 2 * precision * recall / (precision + recall + 1e-8)
        
        metrics = {
            'precision': precision,
            'recall': recall,
            'f1': f1
        }
        
        return val_loss / val_samples, metrics
    
    def train_recognition(self, train_loader, val_loader, epochs):
        """Train CRNN recognition model"""
        
        logger.info("Starting CRNN recognition training...")
        
        for epoch in range(epochs):
            # Training phase
            self.crnn_model.train()
            train_loss = 0.0
            train_samples = 0
            
            pbar = tqdm(train_loader, desc=f'CRNN Epoch {epoch+1}/{epochs}')
            for batch in pbar:
                images = batch['image'].to(self.device)
                gt_data = batch['gt_data']
                text_labels = gt_data['text_labels']
                
                # Convert text labels to indices
                batch_text = []
                batch_length = []
                
                for text_list in text_labels:
                    # Take first text from each image (simplified)
                    text = text_list[0] if text_list else ""
                    batch_text.append(text)
                    batch_length.append(len(text))
                
                # Encode text labels
                text_encoded, lengths = self.label_converter.encode(batch_text)
                text_encoded = text_encoded.to(self.device)
                
                # Forward pass
                preds = self.crnn_model(images)
                
                # Calculate CTC loss
                preds_size = torch.IntTensor([preds.size(1)] * preds.size(0))
                targets = text_encoded.view(-1)
                target_lengths = torch.IntTensor(lengths)
                
                loss = self.crnn_criterion(preds, targets, preds_size, target_lengths)
                
                # Backward pass
                self.crnn_optimizer.zero_grad()
                loss.backward()
                self.crnn_optimizer.step()
                
                # Update metrics
                train_loss += loss.item() * images.size(0)
                train_samples += images.size(0)
                
                pbar.set_postfix({'Loss': f'{loss.item():.4f}'})
            
            # Validation phase
            val_loss, val_accuracy = self._validate_recognition(val_loader)
            
            # Update learning rate
            self.crnn_scheduler.step()
            
            # Log metrics
            epoch_metrics = {
                'crnn_train_loss': train_loss / train_samples,
                'crnn_val_loss': val_loss,
                'crnn_val_accuracy': val_accuracy
            }
            self.metrics_tracker.log_metrics(epoch, epoch_metrics)
            
            # Early stopping check
            if self.early_stopping(val_loss, self.crnn_model):
                logger.info("Early stopping triggered for CRNN model")
                break
        
        # Restore best weights
        if self.early_stopping.best_weights:
            self.crnn_model.load_state_dict(self.early_stopping.best_weights)
        
        logger.info("CRNN recognition training completed")
    
    def _validate_recognition(self, val_loader):
        """Validate CRNN recognition model"""
        
        self.crnn_model.eval()
        val_loss = 0.0
        val_samples = 0
        correct_predictions = 0
        total_predictions = 0
        
        with torch.no_grad():
            for batch in val_loader:
                images = batch['image'].to(self.device)
                gt_data = batch['gt_data']
                text_labels = gt_data['text_labels']
                
                # Convert text labels
                batch_text = []
                for text_list in text_labels:
                    text = text_list[0] if text_list else ""
                    batch_text.append(text)
                
                # Encode text labels
                text_encoded, lengths = self.label_converter.encode(batch_text)
                text_encoded = text_encoded.to(self.device)
                
                # Forward pass
                preds = self.crnn_model(images)
                
                # Calculate loss
                preds_size = torch.IntTensor([preds.size(1)] * preds.size(0))
                targets = text_encoded.view(-1)
                target_lengths = torch.IntTensor(lengths)
                
                loss = self.crnn_criterion(preds, targets, preds_size, target_lengths)
                val_loss += loss.item() * images.size(0)
                val_samples += images.size(0)
                
                # Calculate accuracy (simplified)
                _, preds_index = preds.max(2)
                pred_texts = []
                for i in range(preds.size(0)):
                    # Simple CTC decoding
                    pred_text = ""
                    prev_char = -1
                    for char_idx in preds_index[i]:
                        char_idx = char_idx.item()
                        if char_idx != 0 and char_idx != prev_char:  # 0 is blank
                            if char_idx < len(self.label_converter.character):
                                pred_text += self.label_converter.character[char_idx]
                        prev_char = char_idx
                    pred_texts.append(pred_text)
                
                # Calculate character-level accuracy
                for pred_text, gt_text in zip(pred_texts, batch_text):
                    if pred_text.strip() == gt_text.strip():
                        correct_predictions += 1
                    total_predictions += 1
        
        accuracy = correct_predictions / (total_predictions + 1e-8)
        return val_loss / val_samples, accuracy
    
    def train_full_pipeline(self, data_path):
        """Train the complete IC recognition pipeline"""
        
        logger.info("Starting full pipeline training...")
        
        # Create data loaders
        train_loader, val_loader = self.create_data_loaders(data_path)
        
        # Stage 1: Train CRAFT detection
        if self.config['training']['train_detection']:
            self.train_detection(
                train_loader, 
                val_loader, 
                self.config['training']['craft']['epochs']
            )
        
        # Stage 2: Train CRNN recognition
        if self.config['training']['train_recognition']:
            self.train_recognition(
                train_loader, 
                val_loader,
                self.config['training']['crnn']['epochs']
            )
        
        # Stage 3: Train verification model (if training data available)
        if self.config['training']['train_verification']:
            self._train_verification(data_path)
        
        # Final evaluation
        self.evaluate_pipeline(val_loader)
        
        # Save trained models
        self.save_models()
        
        logger.info("Full pipeline training completed!")
    
    def _train_verification(self, data_path):
        """Train the verification model"""
        
        logger.info("Training verification model...")
        
        # Load verification training data
        verification_data_path = Path(data_path) / 'train' / 'verification_data.csv'
        if not verification_data_path.exists():
            logger.warning("No verification training data found, skipping verification training")
            return
        
        # Prepare training data
        X_train, y_train = self.verifier.prepare_training_data(verification_data_path)
        
        # Train verification model
        training_results = self.verifier.train(
            X_train, y_train,
            epochs=self.config['training']['verification']['epochs'],
            batch_size=self.config['training']['verification']['batch_size'],
            learning_rate=self.config['training']['verification']['learning_rate']
        )
        
        logger.info(f"Verification training completed. Best accuracy: {training_results['best_val_accuracy']:.4f}")
    
    def evaluate_pipeline(self, val_loader):
        """Evaluate the complete pipeline"""
        
        logger.info("Evaluating complete pipeline...")
        
        self.craft_model.eval()
        self.crnn_model.eval()
        
        total_samples = 0
        correct_detections = 0
        correct_recognitions = 0
        correct_verifications = 0
        
        pipeline_results = []
        
        with torch.no_grad():
            pbar = tqdm(val_loader, desc='Pipeline Evaluation')
            for batch in pbar:
                images = batch['image'].to(self.device)
                gt_data = batch['gt_data']
                
                batch_size = images.size(0)
                total_samples += batch_size
                
                # Detection
                region_pred, affinity_pred = self.craft_model(images)
                
                # Recognition (simplified - assume perfect detection boxes)
                recognition_preds = self.crnn_model(images)
                
                # Process each image in batch
                for i in range(batch_size):
                    # Simplified evaluation metrics
                    has_text_gt = len(gt_data['text_labels'][i]) > 0
                    has_text_pred = torch.max(region_pred[i]) > 0.5
                    
                    if has_text_gt == has_text_pred:
                        correct_detections += 1
                    
                    # Recognition accuracy (simplified)
                    if gt_data['text_labels'][i]:
                        gt_text = gt_data['text_labels'][i][0]
                        # Decode prediction (simplified)
                        _, pred_idx = recognition_preds[i].max(1)
                        pred_text = ""
                        prev_char = -1
                        for char_idx in pred_idx:
                            char_idx = char_idx.item()
                            if char_idx != 0 and char_idx != prev_char:
                                if char_idx < len(self.label_converter.character):
                                    pred_text += self.label_converter.character[char_idx]
                            prev_char = char_idx
                        
                        if pred_text.strip() == gt_text.strip():
                            correct_recognitions += 1
                        
                        # Verification (if model is trained)
                        if self.verifier.is_trained:
                            verification_result = self.verifier.verify_ic(pred_text)
                            if verification_result['status'] == 'AUTHENTIC':
                                correct_verifications += 1
                
                # Update progress
                pbar.set_postfix({
                    'Det Acc': f'{correct_detections/total_samples:.3f}',
                    'Rec Acc': f'{correct_recognitions/total_samples:.3f}',
                    'Ver Acc': f'{correct_verifications/total_samples:.3f}'
                })
        
        # Calculate final metrics
        detection_accuracy = correct_detections / total_samples
        recognition_accuracy = correct_recognitions / total_samples
        verification_accuracy = correct_verifications / total_samples if self.verifier.is_trained else 0
        
        # Log final metrics
        final_metrics = {
            'pipeline_detection_accuracy': detection_accuracy,
            'pipeline_recognition_accuracy': recognition_accuracy,
            'pipeline_verification_accuracy': verification_accuracy,
            'pipeline_end_to_end_accuracy': detection_accuracy * recognition_accuracy * (verification_accuracy if verification_accuracy > 0 else 1)
        }
        
        self.metrics_tracker.log_metrics(0, final_metrics)
        
        logger.info(f"Pipeline Evaluation Results:")
        logger.info(f"Detection Accuracy: {detection_accuracy:.4f}")
        logger.info(f"Recognition Accuracy: {recognition_accuracy:.4f}")
        logger.info(f"Verification Accuracy: {verification_accuracy:.4f}")
        logger.info(f"End-to-End Accuracy: {final_metrics['pipeline_end_to_end_accuracy']:.4f}")
        
        return final_metrics
    
    def save_models(self):
        """Save all trained models"""
        
        models_dir = Path(self.config['models']['save_dir'])
        models_dir.mkdir(exist_ok=True)
        
        # Save CRAFT model
        torch.save({
            'model_state_dict': self.craft_model.state_dict(),
            'config': self.config['models']['craft']
        }, models_dir / 'craft_model.pth')
        
        # Save CRNN model
        torch.save({
            'model_state_dict': self.crnn_model.state_dict(),
            'config': self.config['models']['crnn'],
            'label_converter': self.label_converter
        }, models_dir / 'crnn_model.pth')
        
        # Save verification model
        if self.verifier.is_trained:
            self.verifier.save_model(models_dir / 'verification_model.pth')
        
        logger.info(f"Models saved to {models_dir}")


def main():
    """Main training function"""
    
    # Setup directories
    os.makedirs('logs', exist_ok=True)
    os.makedirs('models', exist_ok=True)
    os.makedirs('outputs', exist_ok=True)
    
    # Initialize training pipeline
    trainer = ICTrainingPipeline('configs/training_config.yaml')
    
    # Start training
    data_path = 'data/processed'  # Path to processed dataset
    
    try:
        trainer.train_full_pipeline(data_path)
    except KeyboardInterrupt:
        logger.info("Training interrupted by user")
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise
    finally:
        # Clean up
        trainer.metrics_tracker.save_metrics()
        trainer.metrics_tracker.close()


if __name__ == "__main__":
    main()
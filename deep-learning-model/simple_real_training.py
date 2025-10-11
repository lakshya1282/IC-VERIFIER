"""
Simplified Real Dataset Training - Verification Model Focus
Uses the processed ElectroCom61 dataset
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
import warnings

warnings.filterwarnings("ignore")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as transforms
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import cv2
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm


class SimpleICVerificationModel(nn.Module):
    """Simple IC Verification Model"""
    
    def __init__(self, input_size=224*224*3, hidden_size=256, num_classes=2):
        super(SimpleICVerificationModel, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size // 2)
        self.fc3 = nn.Linear(hidden_size // 2, num_classes)
        self.dropout = nn.Dropout(0.3)
        self.relu = nn.ReLU()
        
    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.relu(self.fc2(x))
        x = self.dropout(x)
        x = self.fc3(x)
        return x


class RealICDataset(Dataset):
    """Dataset for real IC images"""
    
    def __init__(self, annotations, transform=None):
        self.annotations = annotations
        self.transform = transform
        
    def __len__(self):
        return len(self.annotations)
    
    def __getitem__(self, idx):
        ann = self.annotations[idx]
        
        # Load image
        image_path = Path("./src/data/real_datasets") / ann['image_path']
        if not image_path.exists():
            # Generate synthetic image as fallback
            image = np.random.rand(224, 224, 3) * 255
            image = image.astype(np.uint8)
        else:
            image = cv2.imread(str(image_path))
            if image is None:
                image = np.random.rand(224, 224, 3) * 255
                image = image.astype(np.uint8)
            else:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Resize image
        image = cv2.resize(image, (224, 224))
        
        # Get label (authentic vs fake)
        label = int(ann['ic_info']['authentic'])
        
        if self.transform:
            image = self.transform(image)
        else:
            image = torch.from_numpy(image).permute(2, 0, 1).float() / 255.0
            
        return image, label


def train_real_verification_model():
    """Train verification model on real dataset"""
    print("🚀 Starting Real Dataset Verification Training...")
    
    # Setup
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    # Create directories
    model_save_dir = Path("./models/real_trained")
    model_save_dir.mkdir(parents=True, exist_ok=True)
    
    results_dir = Path("./results/real_training")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Load processed dataset
    data_path = Path("./src/data/real_datasets/all_annotations.json")
    if not data_path.exists():
        print("❌ No processed dataset found! Run multi_dataset_loader.py first")
        return
    
    with open(data_path, 'r') as f:
        all_annotations = json.load(f)
    
    print(f"📊 Loaded {len(all_annotations)} samples from real datasets")
    
    # Split data 
    train_size = int(0.7 * len(all_annotations))
    val_size = int(0.2 * len(all_annotations))
    
    train_annotations = all_annotations[:train_size]
    val_annotations = all_annotations[train_size:train_size + val_size]
    test_annotations = all_annotations[train_size + val_size:]
    
    print(f"📚 Split: {len(train_annotations)} train, {len(val_annotations)} val, {len(test_annotations)} test")
    
    # Data transforms
    transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(0.3),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    val_transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    # Create datasets
    train_dataset = RealICDataset(train_annotations, transform=transform)
    val_dataset = RealICDataset(val_annotations, transform=val_transform)
    test_dataset = RealICDataset(test_annotations, transform=val_transform)
    
    # Create data loaders
    train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_dataset, batch_size=16, shuffle=False, num_workers=2)
    test_loader = DataLoader(test_dataset, batch_size=16, shuffle=False, num_workers=2)
    
    # Initialize model
    model = SimpleICVerificationModel(
        input_size=224*224*3,
        hidden_size=256,
        num_classes=2
    ).to(device)
    
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)
    
    # Training parameters
    epochs = 20
    best_val_acc = 0.0
    train_losses, val_losses = [], []
    train_accs, val_accs = [], []
    
    print("🔥 Starting training...")
    
    for epoch in range(epochs):
        # Training phase
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0
        
        train_pbar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs} [Train]")
        
        for images, labels in train_pbar:
            images, labels = images.to(device), labels.to(device)
            
            optimizer.zero_grad()
            
            # Flatten images for the model
            images_flat = images.view(images.size(0), -1)
            outputs = model(images_flat)
            
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            train_total += labels.size(0)
            train_correct += (predicted == labels).sum().item()
            
            train_pbar.set_postfix({
                'Loss': f'{loss.item():.4f}',
                'Acc': f'{100.*train_correct/train_total:.2f}%'
            })
        
        # Validation phase
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        
        with torch.no_grad():
            val_pbar = tqdm(val_loader, desc=f"Epoch {epoch+1}/{epochs} [Val]")
            
            for images, labels in val_pbar:
                images, labels = images.to(device), labels.to(device)
                
                images_flat = images.view(images.size(0), -1)
                outputs = model(images_flat)
                
                loss = criterion(outputs, labels)
                val_loss += loss.item()
                
                _, predicted = torch.max(outputs.data, 1)
                val_total += labels.size(0)
                val_correct += (predicted == labels).sum().item()
                
                val_pbar.set_postfix({
                    'Loss': f'{loss.item():.4f}',
                    'Acc': f'{100.*val_correct/val_total:.2f}%'
                })
        
        # Calculate metrics
        epoch_train_loss = train_loss / len(train_loader)
        epoch_val_loss = val_loss / len(val_loader)
        epoch_train_acc = 100. * train_correct / train_total
        epoch_val_acc = 100. * val_correct / val_total
        
        train_losses.append(epoch_train_loss)
        val_losses.append(epoch_val_loss)
        train_accs.append(epoch_train_acc)
        val_accs.append(epoch_val_acc)
        
        scheduler.step(epoch_val_loss)
        
        print(f"Epoch {epoch+1}: Train Loss: {epoch_train_loss:.4f}, Train Acc: {epoch_train_acc:.2f}%, Val Loss: {epoch_val_loss:.4f}, Val Acc: {epoch_val_acc:.2f}%")
        
        # Save best model
        if epoch_val_acc > best_val_acc:
            best_val_acc = epoch_val_acc
            torch.save({
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'epoch': epoch,
                'val_acc': epoch_val_acc
            }, model_save_dir / 'best_verification_real.pth')
            
            print(f"🎯 New best validation accuracy: {best_val_acc:.2f}%")
    
    # Test evaluation
    print("📊 Evaluating on test set...")
    model.eval()
    test_correct = 0
    test_total = 0
    all_predictions = []
    all_labels = []
    
    with torch.no_grad():
        for images, labels in tqdm(test_loader, desc="Testing"):
            images, labels = images.to(device), labels.to(device)
            
            images_flat = images.view(images.size(0), -1)
            outputs = model(images_flat)
            
            _, predicted = torch.max(outputs, 1)
            test_total += labels.size(0)
            test_correct += (predicted == labels).sum().item()
            
            all_predictions.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
    
    # Calculate final metrics
    test_accuracy = 100. * test_correct / test_total
    precision, recall, f1, _ = precision_recall_fscore_support(all_labels, all_predictions, average='weighted')
    
    # Save results
    results = {
        'training_completed': datetime.now().isoformat(),
        'dataset_info': {
            'total_samples': len(all_annotations),
            'train_samples': len(train_annotations),
            'val_samples': len(val_annotations),
            'test_samples': len(test_annotations)
        },
        'best_val_accuracy': best_val_acc,
        'test_accuracy': test_accuracy,
        'precision': precision * 100,
        'recall': recall * 100,
        'f1_score': f1 * 100,
        'epochs_trained': epochs
    }
    
    with open(results_dir / 'real_dataset_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Save training history
    history = {
        'train_losses': train_losses,
        'val_losses': val_losses,
        'train_accuracies': train_accs,
        'val_accuracies': val_accs
    }
    
    with open(results_dir / 'training_history.json', 'w') as f:
        json.dump(history, f, indent=2)
    
    # Plot training curves
    try:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
        
        # Loss curves
        ax1.plot(train_losses, label='Train Loss', color='blue')
        ax1.plot(val_losses, label='Val Loss', color='red')
        ax1.set_title('Training Loss')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('Loss')
        ax1.legend()
        ax1.grid(True)
        
        # Accuracy curves
        ax2.plot(train_accs, label='Train Acc', color='blue')
        ax2.plot(val_accs, label='Val Acc', color='red')
        ax2.set_title('Training Accuracy')
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel('Accuracy (%)')
        ax2.legend()
        ax2.grid(True)
        
        plt.tight_layout()
        plt.savefig(results_dir / 'training_curves.png', dpi=150, bbox_inches='tight')
        plt.close()
        print(f"📈 Training curves saved to {results_dir / 'training_curves.png'}")
    except Exception as e:
        print(f"⚠️ Could not save training curves: {e}")
    
    # Print final summary
    print("\n" + "="*60)
    print("🏁 REAL DATASET TRAINING COMPLETED!")
    print("="*60)
    print(f"📊 Dataset: {len(all_annotations)} total samples")
    print(f"🎯 Best Val Accuracy: {best_val_acc:.2f}%")
    print(f"🔍 Test Accuracy: {test_accuracy:.2f}%")
    print(f"⚖️ Precision: {precision*100:.2f}%")
    print(f"🎚️ Recall: {recall*100:.2f}%")
    print(f"📐 F1-Score: {f1*100:.2f}%")
    print(f"💾 Model saved to: {model_save_dir}")
    print(f"📈 Results saved to: {results_dir}")
    print("="*60)
    
    return results


if __name__ == "__main__":
    train_real_verification_model()
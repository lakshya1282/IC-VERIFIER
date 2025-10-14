#!/usr/bin/env python3
"""
Dataset Download and Setup Script for IC Verification System
Downloads and prepares various IC datasets for training and evaluation
"""

import os
import sys
import requests
import pandas as pd
from pathlib import Path
import zipfile
import json
import logging
from typing import Dict, List
import time

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ICDatasetManager:
    """Manages IC datasets for training and evaluation"""
    
    def __init__(self, base_dir: str = "./datasets"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
        # Dataset registry
        self.datasets = {
            'physicaldb_deepic': {
                'name': 'PhysicalDB DeepIC Dataset',
                'url': 'https://physicaldb.ece.ufl.edu/index.php/deeplogoic/',
                'type': 'gated',
                'description': 'Physical IC images and logos (980+ images)',
                'local_path': self.base_dir / 'physicaldb_deepic'
            },
            'physicaldb_synthlogo': {
                'name': 'PhysicalDB IC-SynthLogo',
                'url': 'https://physicaldb.ece.ufl.edu/index.php/elementor-430/',
                'type': 'gated', 
                'description': 'Synthetic IC logos and images',
                'local_path': self.base_dir / 'physicaldb_synthlogo'
            },
            'kaggle_counterfeit': {
                'name': 'Kaggle Counterfeit Products Dataset',
                'url': 'https://www.kaggle.com/datasets/aimlveera/counterfeit-product-detection-dataset',
                'type': 'public',
                'description': 'Synthetic + real product counterfeit images',
                'local_path': self.base_dir / 'kaggle_counterfeit'
            },
            'roboflow_counterfeit': {
                'name': 'Roboflow Counterfeit Detection Dataset',
                'url': 'https://universe.roboflow.com/cnn-kdxjk/counterfeit-product-detection/dataset/1',
                'type': 'public',
                'description': 'Small annotated dataset for real vs fake products',
                'local_path': self.base_dir / 'roboflow_counterfeit'
            }
        }
    
    def setup_directories(self):
        """Create necessary directories for datasets"""
        logger.info("Setting up dataset directories...")
        
        for dataset_name, dataset_info in self.datasets.items():
            dataset_info['local_path'].mkdir(exist_ok=True)
            
            # Create subdirectories
            (dataset_info['local_path'] / 'raw').mkdir(exist_ok=True)
            (dataset_info['local_path'] / 'processed').mkdir(exist_ok=True)
            (dataset_info['local_path'] / 'annotations').mkdir(exist_ok=True)
        
        logger.info("✅ Dataset directories created")
    
    def download_craft_weights(self):
        """Download CRAFT text detection pretrained weights"""
        logger.info("Downloading CRAFT pretrained weights...")
        
        models_dir = self.base_dir.parent / 'models' / 'pretrained'
        models_dir.mkdir(parents=True, exist_ok=True)
        
        craft_weights = {
            'craft_mlt_25k.pth': 'https://drive.google.com/uc?id=1Jk4eGD7crsqCCg9C9VjCLkMN3ze8kutZ',
            'craft_refiner_CTW1500.pth': 'https://drive.google.com/uc?id=1XSaFwBkOaFOdtk4Ane3DFyJGPRw6v5bO'
        }
        
        for filename, url in craft_weights.items():
            filepath = models_dir / filename
            if not filepath.exists():
                logger.info(f"Downloading {filename}...")
                try:
                    # Note: This is a simplified download - for Google Drive, you'd need gdown
                    # pip install gdown
                    # gdown.download(url, str(filepath), quiet=False)
                    logger.warning(f"Please manually download {filename} from CRAFT GitHub repo")
                    logger.info(f"URL: https://github.com/clovaai/CRAFT-pytorch")
                except Exception as e:
                    logger.error(f"Failed to download {filename}: {e}")
            else:
                logger.info(f"✅ {filename} already exists")
    
    def setup_kaggle_dataset(self):
        """Setup Kaggle counterfeit dataset (requires Kaggle API)"""
        logger.info("Setting up Kaggle counterfeit dataset...")
        
        try:
            # Check if kaggle is installed
            import kaggle
            
            dataset_path = self.datasets['kaggle_counterfeit']['local_path']
            
            # Download using Kaggle API
            kaggle.api.dataset_download_files(
                'aimlveera/counterfeit-product-detection-dataset',
                path=str(dataset_path / 'raw'),
                unzip=True
            )
            
            logger.info("✅ Kaggle dataset downloaded successfully")
            
        except ImportError:
            logger.warning("Kaggle API not installed. Install with: pip install kaggle")
            logger.info("Manual download from: https://www.kaggle.com/datasets/aimlveera/counterfeit-product-detection-dataset")
        except Exception as e:
            logger.error(f"Failed to download Kaggle dataset: {e}")
    
    def create_dataset_manifest(self):
        """Create a manifest file with dataset information"""
        manifest = {
            'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'datasets': {}
        }
        
        for dataset_name, dataset_info in self.datasets.items():
            manifest['datasets'][dataset_name] = {
                'name': dataset_info['name'],
                'url': dataset_info['url'],
                'type': dataset_info['type'],
                'description': dataset_info['description'],
                'local_path': str(dataset_info['local_path']),
                'downloaded': dataset_info['local_path'].exists()
            }
        
        manifest_path = self.base_dir / 'dataset_manifest.json'
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"✅ Dataset manifest created: {manifest_path}")
    
    def create_data_preparation_script(self):
        """Create a script for data preprocessing"""
        script_content = '''#!/usr/bin/env python3
"""
Data Preprocessing Script for IC Verification System
Processes downloaded datasets and prepares them for training
"""

import os
import cv2
import numpy as np
from pathlib import Path
import json
import pandas as pd
from sklearn.model_selection import train_test_split

def process_ic_images(input_dir, output_dir, target_size=(768, 768)):
    """Process IC images for training"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    processed_count = 0
    
    for img_file in input_path.glob('**/*.jpg'):
        try:
            # Read image
            img = cv2.imread(str(img_file))
            if img is None:
                continue
            
            # Resize while maintaining aspect ratio
            h, w = img.shape[:2]
            scale = min(target_size[0]/w, target_size[1]/h)
            new_w, new_h = int(w*scale), int(h*scale)
            
            img_resized = cv2.resize(img, (new_w, new_h))
            
            # Pad to target size
            pad_w = (target_size[0] - new_w) // 2
            pad_h = (target_size[1] - new_h) // 2
            
            img_padded = cv2.copyMakeBorder(
                img_resized, pad_h, pad_h, pad_w, pad_w,
                cv2.BORDER_CONSTANT, value=[0,0,0]
            )
            
            # Save processed image
            output_file = output_path / f"processed_{processed_count:06d}.jpg"
            cv2.imwrite(str(output_file), img_padded)
            processed_count += 1
            
        except Exception as e:
            print(f"Error processing {img_file}: {e}")
    
    print(f"Processed {processed_count} images")

def create_training_splits(data_dir, train_ratio=0.7, val_ratio=0.2, test_ratio=0.1):
    """Create train/val/test splits"""
    data_path = Path(data_dir)
    image_files = list(data_path.glob('*.jpg'))
    
    # Split data
    train_files, temp_files = train_test_split(
        image_files, test_size=(1-train_ratio), random_state=42
    )
    val_files, test_files = train_test_split(
        temp_files, test_size=test_ratio/(val_ratio+test_ratio), random_state=42
    )
    
    # Create split directories
    for split_name, files in [('train', train_files), ('val', val_files), ('test', test_files)]:
        split_dir = data_path.parent / split_name
        split_dir.mkdir(exist_ok=True)
        
        for file in files:
            # Create symlink or copy
            target = split_dir / file.name
            if not target.exists():
                target.symlink_to(file.absolute())
    
    print(f"Created splits: train={len(train_files)}, val={len(val_files)}, test={len(test_files)}")

if __name__ == "__main__":
    # Example usage
    # process_ic_images("datasets/raw_images", "datasets/processed")
    # create_training_splits("datasets/processed")
    print("Data preprocessing script ready. Customize for your datasets.")
'''
        
        script_path = self.base_dir / 'data_preprocessing.py'
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        logger.info(f"✅ Data preprocessing script created: {script_path}")
    
    def print_dataset_info(self):
        """Print information about available datasets"""
        print("\n📊 IC Dataset Information:")
        print("=" * 80)
        
        for dataset_name, dataset_info in self.datasets.items():
            status = "✅ Downloaded" if dataset_info['local_path'].exists() else "⏳ Not downloaded"
            
            print(f"\n📁 {dataset_info['name']}")
            print(f"   Type: {dataset_info['type']}")
            print(f"   Status: {status}")
            print(f"   Description: {dataset_info['description']}")
            print(f"   URL: {dataset_info['url']}")
            print(f"   Local: {dataset_info['local_path']}")
    
    def run_setup(self):
        """Run complete dataset setup"""
        logger.info("🚀 Starting IC Dataset Setup...")
        
        # Create directories
        self.setup_directories()
        
        # Download CRAFT weights
        self.download_craft_weights()
        
        # Setup Kaggle dataset (if possible)
        self.setup_kaggle_dataset()
        
        # Create manifest and scripts
        self.create_dataset_manifest()
        self.create_data_preparation_script()
        
        # Print information
        self.print_dataset_info()
        
        logger.info("✅ Dataset setup complete!")
        
        print("\n📋 Next Steps:")
        print("1. For PhysicalDB datasets - register at their website and download manually")
        print("2. For Kaggle dataset - ensure Kaggle API is configured")
        print("3. For CRAFT weights - download from GitHub repo")
        print("4. Run data_preprocessing.py to prepare your datasets")

def main():
    """Main function"""
    # Get project root directory
    project_root = Path(__file__).parent.parent
    datasets_dir = project_root / 'datasets'
    
    # Initialize dataset manager
    manager = ICDatasetManager(str(datasets_dir))
    
    # Run setup
    manager.run_setup()

if __name__ == "__main__":
    main()
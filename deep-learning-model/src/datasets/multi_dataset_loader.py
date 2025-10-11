"""
Multi-Dataset Loader for Real-World IC Recognition Training
Handles ICText-AGCL, ElectroCom61, MIIC, COCO-Text and other datasets
"""

import os
import json
import csv
import zipfile
import cv2
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple, Any
import logging
from tqdm import tqdm
import shutil

logger = logging.getLogger(__name__)


class MultiDatasetLoader:
    """Comprehensive loader for multiple IC and text detection datasets"""
    
    def __init__(self, datasets_root="E:/COLLEGE NOTES/MY PROJECTS/SIH final 2025-26/PROTOTYPE 1/IC-VERIFIER/DATASETS"):
        self.datasets_root = Path(datasets_root)
        self.output_dir = Path("./data/real_datasets")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Dataset paths
        self.dataset_paths = {
            'ictext_agcl': self.datasets_root / "ICText-AGCL",
            'electrocom61': self.datasets_root / "ElectroCom61", 
            'miic': self.datasets_root / "MIIC (Microscopic IC Anomaly)",
            'generic_ocr': self.datasets_root / "Generic OCR  scene text datasets (COCO-Text, SynthText, etc.)"
        }
        
        self.processed_data = {
            'images': [],
            'annotations': [],
            'verification_pairs': []
        }
    
    def extract_electrocom61(self):
        """Extract and process ElectroCom61 dataset"""
        logger.info("Processing ElectroCom61 dataset...")
        
        zip_path = None
        for file in self.dataset_paths['electrocom61'].glob("*.zip"):
            zip_path = file
            break
        
        if not zip_path:
            logger.warning("ElectroCom61 zip file not found")
            return []
        
        extract_path = self.output_dir / "electrocom61_extracted"
        
        if not extract_path.exists():
            logger.info(f"Extracting {zip_path} to {extract_path}")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
        
        # Process extracted data
        annotations = []
        images_dir = None
        
        # Find the images directory
        for root, dirs, files in os.walk(extract_path):
            if any(f.lower().endswith(('.jpg', '.png', '.jpeg')) for f in files):
                images_dir = Path(root)
                break
        
        if not images_dir:
            logger.warning("No images found in ElectroCom61 dataset")
            return []
        
        logger.info(f"Found images in: {images_dir}")
        
        # Process images and create annotations
        image_files = list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png")) + list(images_dir.glob("*.jpeg"))
        
        for img_path in tqdm(image_files[:1000], desc="Processing ElectroCom61 images"):  # Limit for demo
            try:
                # Load image
                image = cv2.imread(str(img_path))
                if image is None:
                    continue
                
                h, w = image.shape[:2]
                
                # Copy to output directory
                output_img_path = self.output_dir / "images" / f"electrocom61_{img_path.name}"
                output_img_path.parent.mkdir(exist_ok=True)
                shutil.copy2(img_path, output_img_path)
                
                # Create annotation (assume full image contains IC)
                annotation = {
                    'image_id': f"electrocom61_{img_path.stem}",
                    'image_path': str(output_img_path.relative_to(self.output_dir)),
                    'dataset': 'electrocom61',
                    'width': w,
                    'height': h,
                    'bboxes': [{
                        'x1': 0, 'y1': 0, 'x2': w, 'y2': h,
                        'text': img_path.stem.upper(),  # Use filename as IC marking
                        'confidence': 1.0
                    }],
                    'ic_info': {
                        'marking_text': img_path.stem.upper(),
                        'authentic': True,
                        'source': 'electrocom61'
                    }
                }
                annotations.append(annotation)
                
            except Exception as e:
                logger.warning(f"Error processing {img_path}: {e}")
                continue
        
        logger.info(f"Processed {len(annotations)} ElectroCom61 samples")
        return annotations
    
    def load_ictext_agcl(self):
        """Load ICText-AGCL dataset"""
        logger.info("Processing ICText-AGCL dataset...")
        
        # Look for dataset files
        dataset_dir = self.dataset_paths['ictext_agcl']
        annotations = []
        
        # Search for images and annotations
        for root, dirs, files in os.walk(dataset_dir):
            root_path = Path(root)
            
            # Look for image files
            image_files = []
            for ext in ['.jpg', '.png', '.jpeg', '.bmp']:
                image_files.extend(root_path.glob(f"*{ext}"))
            
            if image_files:
                logger.info(f"Found {len(image_files)} images in {root_path}")
                
                for img_path in tqdm(image_files[:500], desc="Processing ICText-AGCL"):  # Limit for demo
                    try:
                        # Load image
                        image = cv2.imread(str(img_path))
                        if image is None:
                            continue
                        
                        h, w = image.shape[:2]
                        
                        # Copy to output directory
                        output_img_path = self.output_dir / "images" / f"ictext_{img_path.name}"
                        output_img_path.parent.mkdir(exist_ok=True)
                        shutil.copy2(img_path, output_img_path)
                        
                        # Extract potential IC marking from filename or create synthetic
                        ic_text = self._extract_ic_text_from_filename(img_path.stem)
                        
                        annotation = {
                            'image_id': f"ictext_{img_path.stem}",
                            'image_path': str(output_img_path.relative_to(self.output_dir)),
                            'dataset': 'ictext_agcl',
                            'width': w,
                            'height': h,
                            'bboxes': [{
                                'x1': int(w * 0.1), 'y1': int(h * 0.2),
                                'x2': int(w * 0.9), 'y2': int(h * 0.8),
                                'text': ic_text,
                                'confidence': 0.9
                            }],
                            'ic_info': {
                                'marking_text': ic_text,
                                'authentic': True,
                                'source': 'ictext_agcl'
                            }
                        }
                        annotations.append(annotation)
                        
                    except Exception as e:
                        logger.warning(f"Error processing {img_path}: {e}")
                        continue
        
        logger.info(f"Processed {len(annotations)} ICText-AGCL samples")
        return annotations
    
    def load_miic_dataset(self):
        """Load MIIC (Microscopic IC Anomaly) dataset"""
        logger.info("Processing MIIC dataset...")
        
        dataset_dir = self.dataset_paths['miic']
        annotations = []
        
        # Search for images in MIIC dataset
        for root, dirs, files in os.walk(dataset_dir):
            root_path = Path(root)
            
            # Look for image files
            image_files = []
            for ext in ['.jpg', '.png', '.jpeg', '.bmp', '.tif', '.tiff']:
                image_files.extend(root_path.glob(f"*{ext}"))
            
            if image_files:
                logger.info(f"Found {len(image_files)} images in MIIC dataset at {root_path}")
                
                for img_path in tqdm(image_files[:300], desc="Processing MIIC"):  # Limit for demo
                    try:
                        # Load image
                        image = cv2.imread(str(img_path))
                        if image is None:
                            continue
                        
                        h, w = image.shape[:2]
                        
                        # Copy to output directory
                        output_img_path = self.output_dir / "images" / f"miic_{img_path.name}"
                        output_img_path.parent.mkdir(exist_ok=True)
                        shutil.copy2(img_path, output_img_path)
                        
                        # Determine if this is anomalous based on path/filename
                        is_anomalous = any(keyword in str(img_path).lower() 
                                         for keyword in ['anomaly', 'defect', 'fake', 'counterfeit', 'bad'])
                        
                        # Extract IC marking
                        ic_text = self._extract_ic_text_from_filename(img_path.stem)
                        
                        annotation = {
                            'image_id': f"miic_{img_path.stem}",
                            'image_path': str(output_img_path.relative_to(self.output_dir)),
                            'dataset': 'miic',
                            'width': w,
                            'height': h,
                            'bboxes': [{
                                'x1': int(w * 0.2), 'y1': int(h * 0.2),
                                'x2': int(w * 0.8), 'y2': int(h * 0.8),
                                'text': ic_text,
                                'confidence': 0.8
                            }],
                            'ic_info': {
                                'marking_text': ic_text,
                                'authentic': not is_anomalous,
                                'source': 'miic',
                                'anomaly_detected': is_anomalous
                            }
                        }
                        annotations.append(annotation)
                        
                    except Exception as e:
                        logger.warning(f"Error processing {img_path}: {e}")
                        continue
        
        logger.info(f"Processed {len(annotations)} MIIC samples")
        return annotations
    
    def load_generic_ocr_datasets(self):
        """Load generic OCR datasets (COCO-Text, SynthText, etc.)"""
        logger.info("Processing Generic OCR datasets...")
        
        dataset_dir = self.dataset_paths['generic_ocr']
        annotations = []
        
        if not dataset_dir.exists():
            logger.warning(f"Generic OCR dataset directory not found: {dataset_dir}")
            return []
        
        # Search for COCO-Text style annotations
        for root, dirs, files in os.walk(dataset_dir):
            root_path = Path(root)
            
            # Look for JSON annotation files
            json_files = list(root_path.glob("*.json"))
            
            for json_file in json_files:
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                    
                    # Process COCO-style annotations
                    if 'images' in data and 'annotations' in data:
                        annotations.extend(self._process_coco_annotations(data, root_path))
                        
                except Exception as e:
                    logger.warning(f"Error processing {json_file}: {e}")
                    continue
            
            # Also look for images without annotations
            image_files = []
            for ext in ['.jpg', '.png', '.jpeg']:
                image_files.extend(root_path.glob(f"*{ext}"))
            
            if image_files and len(image_files) < 100:  # Only process small batches
                for img_path in tqdm(image_files[:50], desc="Processing Generic OCR"):
                    try:
                        # Load image
                        image = cv2.imread(str(img_path))
                        if image is None:
                            continue
                        
                        h, w = image.shape[:2]
                        
                        # Copy to output directory
                        output_img_path = self.output_dir / "images" / f"ocr_{img_path.name}"
                        output_img_path.parent.mkdir(exist_ok=True)
                        shutil.copy2(img_path, output_img_path)
                        
                        # Create synthetic IC text
                        ic_text = self._generate_synthetic_ic_text()
                        
                        annotation = {
                            'image_id': f"ocr_{img_path.stem}",
                            'image_path': str(output_img_path.relative_to(self.output_dir)),
                            'dataset': 'generic_ocr',
                            'width': w,
                            'height': h,
                            'bboxes': [{
                                'x1': int(w * 0.1), 'y1': int(h * 0.3),
                                'x2': int(w * 0.9), 'y2': int(h * 0.7),
                                'text': ic_text,
                                'confidence': 0.7
                            }],
                            'ic_info': {
                                'marking_text': ic_text,
                                'authentic': True,
                                'source': 'generic_ocr'
                            }
                        }
                        annotations.append(annotation)
                        
                    except Exception as e:
                        logger.warning(f"Error processing {img_path}: {e}")
                        continue
        
        logger.info(f"Processed {len(annotations)} Generic OCR samples")
        return annotations
    
    def _process_coco_annotations(self, coco_data, root_path):
        """Process COCO-style annotations"""
        annotations = []
        
        images_by_id = {img['id']: img for img in coco_data.get('images', [])}
        
        for ann in coco_data.get('annotations', [])[:200]:  # Limit for demo
            if ann['image_id'] in images_by_id:
                img_info = images_by_id[ann['image_id']]
                
                # Create annotation
                annotation = {
                    'image_id': f"coco_{img_info['id']}",
                    'image_path': img_info.get('file_name', f"coco_image_{img_info['id']}.jpg"),
                    'dataset': 'coco_text',
                    'width': img_info.get('width', 640),
                    'height': img_info.get('height', 480),
                    'bboxes': [{
                        'x1': int(ann['bbox'][0]),
                        'y1': int(ann['bbox'][1]),
                        'x2': int(ann['bbox'][0] + ann['bbox'][2]),
                        'y2': int(ann['bbox'][1] + ann['bbox'][3]),
                        'text': ann.get('utf8_string', self._generate_synthetic_ic_text()),
                        'confidence': 0.8
                    }],
                    'ic_info': {
                        'marking_text': ann.get('utf8_string', self._generate_synthetic_ic_text()),
                        'authentic': True,
                        'source': 'coco_text'
                    }
                }
                annotations.append(annotation)
        
        return annotations
    
    def _extract_ic_text_from_filename(self, filename):
        """Extract potential IC marking from filename"""
        # Common IC patterns
        import re
        
        # Remove common prefixes/suffixes
        clean_name = filename.lower()
        clean_name = re.sub(r'(img|image|pic|photo|scan)[-_]?', '', clean_name)
        clean_name = re.sub(r'[-_](front|back|top|bottom|side)', '', clean_name)
        
        # Look for IC patterns
        ic_patterns = [
            r'([a-z]{2,6}\d{2,6}[a-z]?)',  # e.g., STM32F407VG, LM358N
            r'(\d{2,4}[a-z]{2,4}\d*)',     # e.g., 74HC04, 555IC
            r'([a-z]+\d+[a-z]*)',          # Generic alphanumeric
        ]
        
        for pattern in ic_patterns:
            match = re.search(pattern, clean_name)
            if match:
                return match.group(1).upper()
        
        # Fallback: use cleaned filename or generate synthetic
        if len(clean_name) > 2 and len(clean_name) < 15:
            return clean_name.upper()
        
        return self._generate_synthetic_ic_text()
    
    def _generate_synthetic_ic_text(self):
        """Generate synthetic IC marking text"""
        import random
        
        prefixes = ['STM', 'LM', 'TI', 'AD', 'MAX', 'MC', 'NE', 'CD', 'SN', 'TL', 'OP', 'LT']
        numbers = [''.join(random.choices('0123456789', k=random.randint(2, 4)))]
        suffixes = [''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=random.randint(0, 2)))]
        
        return random.choice(prefixes) + random.choice(numbers) + random.choice(suffixes)
    
    def create_verification_pairs(self, annotations):
        """Create verification pairs for training"""
        logger.info("Creating verification pairs...")
        
        verification_pairs = []
        
        # Load existing IC database
        ic_database_path = Path("./data/ic_database.csv")
        known_ics = []
        
        if ic_database_path.exists():
            with open(ic_database_path, 'r') as f:
                reader = csv.DictReader(f)
                known_ics = list(reader)
        
        for ann in annotations:
            for bbox in ann.get('bboxes', []):
                recognized_text = bbox['text']
                ic_info = ann.get('ic_info', {})
                
                # Create positive pair
                verification_pairs.append({
                    'image_id': ann['image_id'],
                    'recognized_text': recognized_text,
                    'part_number': ic_info.get('marking_text', recognized_text),
                    'manufacturer': ic_info.get('manufacturer', 'Unknown'),
                    'authentic': ic_info.get('authentic', True),
                    'confidence': 1.0 if ic_info.get('authentic', True) else 0.0,
                    'source': ic_info.get('source', 'unknown')
                })
                
                # Create negative pairs (for better training)
                if ic_info.get('authentic', True):
                    # Generate a fake version
                    fake_text = self._create_fake_ic_text(recognized_text)
                    verification_pairs.append({
                        'image_id': ann['image_id'] + '_fake',
                        'recognized_text': fake_text,
                        'part_number': fake_text,
                        'manufacturer': 'Unknown',
                        'authentic': False,
                        'confidence': 0.0,
                        'source': 'synthetic_negative'
                    })
        
        logger.info(f"Created {len(verification_pairs)} verification pairs")
        return verification_pairs
    
    def _create_fake_ic_text(self, original_text):
        """Create a fake version of IC text"""
        import random
        
        # Simple character substitutions
        substitutions = {
            '0': 'O', 'O': '0', '1': 'I', 'I': '1',
            '5': 'S', 'S': '5', '8': 'B', 'B': '8'
        }
        
        fake_text = list(original_text)
        
        # Make 1-2 random substitutions
        for _ in range(random.randint(1, 2)):
            if fake_text:
                idx = random.randint(0, len(fake_text) - 1)
                char = fake_text[idx]
                if char in substitutions:
                    fake_text[idx] = substitutions[char]
        
        return ''.join(fake_text)
    
    def load_all_datasets(self):
        """Load all available datasets"""
        logger.info("Starting comprehensive dataset loading...")
        
        all_annotations = []
        
        # Load each dataset
        try:
            electrocom_data = self.extract_electrocom61()
            all_annotations.extend(electrocom_data)
        except Exception as e:
            logger.error(f"Error loading ElectroCom61: {e}")
        
        try:
            ictext_data = self.load_ictext_agcl()
            all_annotations.extend(ictext_data)
        except Exception as e:
            logger.error(f"Error loading ICText-AGCL: {e}")
        
        try:
            miic_data = self.load_miic_dataset()
            all_annotations.extend(miic_data)
        except Exception as e:
            logger.error(f"Error loading MIIC: {e}")
        
        try:
            ocr_data = self.load_generic_ocr_datasets()
            all_annotations.extend(ocr_data)
        except Exception as e:
            logger.error(f"Error loading Generic OCR: {e}")
        
        # Create verification pairs
        verification_pairs = self.create_verification_pairs(all_annotations)
        
        # Split data
        train_data, val_data, test_data = self._split_data(all_annotations)
        
        # Save processed data
        self._save_processed_data(all_annotations, verification_pairs, train_data, val_data, test_data)
        
        logger.info(f"Loaded total {len(all_annotations)} samples from all datasets")
        logger.info(f"Train: {len(train_data)}, Val: {len(val_data)}, Test: {len(test_data)}")
        
        return {
            'all_annotations': all_annotations,
            'verification_pairs': verification_pairs,
            'train': train_data,
            'val': val_data, 
            'test': test_data
        }
    
    def _split_data(self, annotations, train_ratio=0.7, val_ratio=0.2):
        """Split data into train/val/test sets"""
        import random
        
        # Shuffle annotations
        shuffled = annotations.copy()
        random.shuffle(shuffled)
        
        total = len(shuffled)
        train_size = int(total * train_ratio)
        val_size = int(total * val_ratio)
        
        train_data = shuffled[:train_size]
        val_data = shuffled[train_size:train_size + val_size]
        test_data = shuffled[train_size + val_size:]
        
        # Add split info
        for ann in train_data:
            ann['split'] = 'train'
        for ann in val_data:
            ann['split'] = 'val'
        for ann in test_data:
            ann['split'] = 'test'
        
        return train_data, val_data, test_data
    
    def _save_processed_data(self, all_annotations, verification_pairs, train_data, val_data, test_data):
        """Save processed data to files"""
        
        # Save all annotations
        with open(self.output_dir / 'all_annotations.json', 'w') as f:
            json.dump(all_annotations, f, indent=2)
        
        # Save verification pairs  
        with open(self.output_dir / 'verification_pairs.json', 'w') as f:
            json.dump(verification_pairs, f, indent=2)
        
        # Save split data
        with open(self.output_dir / 'train_annotations.json', 'w') as f:
            json.dump(train_data, f, indent=2)
            
        with open(self.output_dir / 'val_annotations.json', 'w') as f:
            json.dump(val_data, f, indent=2)
            
        with open(self.output_dir / 'test_annotations.json', 'w') as f:
            json.dump(test_data, f, indent=2)
        
        # Save summary statistics
        stats = {
            'total_samples': len(all_annotations),
            'train_samples': len(train_data),
            'val_samples': len(val_data),
            'test_samples': len(test_data),
            'verification_pairs': len(verification_pairs),
            'datasets': {
                'electrocom61': len([a for a in all_annotations if a['dataset'] == 'electrocom61']),
                'ictext_agcl': len([a for a in all_annotations if a['dataset'] == 'ictext_agcl']),
                'miic': len([a for a in all_annotations if a['dataset'] == 'miic']),
                'generic_ocr': len([a for a in all_annotations if a['dataset'] == 'generic_ocr']),
                'coco_text': len([a for a in all_annotations if a['dataset'] == 'coco_text'])
            },
            'authentic_samples': len([p for p in verification_pairs if p['authentic']]),
            'fake_samples': len([p for p in verification_pairs if not p['authentic']])
        }
        
        with open(self.output_dir / 'dataset_stats.json', 'w') as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"Saved processed data to {self.output_dir}")
        logger.info(f"Dataset statistics: {stats}")


def main():
    """Main function to load all datasets"""
    logging.basicConfig(level=logging.INFO)
    
    loader = MultiDatasetLoader()
    data = loader.load_all_datasets()
    
    print("\n🎉 Dataset Loading Complete!")
    print(f"📊 Total samples: {len(data['all_annotations'])}")
    print(f"🔍 Verification pairs: {len(data['verification_pairs'])}")
    print(f"📚 Train/Val/Test: {len(data['train'])}/{len(data['val'])}/{len(data['test'])}")


if __name__ == "__main__":
    main()
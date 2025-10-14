"""
IC Text Detection & Recognition - Data Preprocessing Pipeline
Handles ICText-AGCL, COCO-Text, SynthText, and custom IC datasets
"""

import os
import json
import pandas as pd
import numpy as np
import cv2
from PIL import Image
import yaml
from tqdm import tqdm
from pathlib import Path
import xml.etree.ElementTree as ET
from sklearn.model_selection import train_test_split
import shutil
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataPreprocessor:
    """
    Comprehensive data preprocessing pipeline for IC recognition datasets
    """
    
    def __init__(self, config_path='configs/data_config.yaml'):
        """
        Initialize data preprocessor with configuration
        
        Args:
            config_path: Path to YAML configuration file
        """
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.dataset_root = Path(self.config['dataset_root'])
        self.output_root = Path(self.config['output_root'])
        self.splits = self.config['splits']  # train/val/test ratios
        
        # Create output directories
        self.output_root.mkdir(exist_ok=True, parents=True)
        for split in ['train', 'val', 'test']:
            (self.output_root / split).mkdir(exist_ok=True)
            (self.output_root / split / 'images').mkdir(exist_ok=True)
            (self.output_root / split / 'annotations').mkdir(exist_ok=True)
    
    def process_ictext_agcl(self):
        """
        Process ICText-AGCL dataset with character-level annotations
        Expected structure:
        ICText-AGCL/
        ├── images/
        ├── annotations/
        │   ├── bounding_boxes.json
        │   └── character_attributes.json
        """
        logger.info("Processing ICText-AGCL dataset...")
        
        ictext_path = self.dataset_root / 'ICText-AGCL'
        images_path = ictext_path / 'images'
        annotations_path = ictext_path / 'annotations'
        
        # Load annotations
        with open(annotations_path / 'bounding_boxes.json', 'r') as f:
            bbox_annotations = json.load(f)
        
        # Load character quality attributes if available
        attr_file = annotations_path / 'character_attributes.json'
        char_attributes = {}
        if attr_file.exists():
            with open(attr_file, 'r') as f:
                char_attributes = json.load(f)
        
        # Process each image
        processed_data = []
        for img_info in tqdm(bbox_annotations['images'], desc="Processing ICText-AGCL"):
            img_path = images_path / img_info['file_name']
            if not img_path.exists():
                continue
                
            # Load image to get dimensions
            image = cv2.imread(str(img_path))
            if image is None:
                continue
                
            img_height, img_width = image.shape[:2]
            
            # Get annotations for this image
            img_id = img_info['id']
            img_annotations = [ann for ann in bbox_annotations['annotations'] 
                             if ann['image_id'] == img_id]
            
            # Process text regions
            text_regions = []
            for ann in img_annotations:
                # Convert COCO format bbox to our format
                x, y, w, h = ann['bbox']
                x2, y2 = x + w, y + h
                
                # Normalize coordinates
                x_norm = x / img_width
                y_norm = y / img_height
                x2_norm = x2 / img_width
                y2_norm = y2 / img_height
                
                # Get character attributes if available
                text = ann.get('text', '')
                quality_attrs = char_attributes.get(str(ann['id']), {})
                
                text_regions.append({
                    'bbox': [x_norm, y_norm, x2_norm, y2_norm],
                    'text': text,
                    'category': ann.get('category_id', 0),
                    'attributes': quality_attrs
                })
            
            processed_data.append({
                'image_path': str(img_path),
                'image_id': img_id,
                'width': img_width,
                'height': img_height,
                'text_regions': text_regions,
                'dataset': 'ictext_agcl'
            })
        
        logger.info(f"Processed {len(processed_data)} images from ICText-AGCL")
        return processed_data
    
    def process_coco_text(self):
        """
        Process COCO-Text dataset for pretraining
        """
        logger.info("Processing COCO-Text dataset...")
        
        coco_path = self.dataset_root / 'COCO-Text'
        
        # Load COCO-Text annotations
        with open(coco_path / 'annotations.json', 'r') as f:
            coco_data = json.load(f)
        
        processed_data = []
        images_dict = {img['id']: img for img in coco_data['images']}
        
        # Filter for legible text only (for IC domain relevance)
        valid_annotations = [ann for ann in coco_data['annotations'] 
                           if ann.get('legibility') == 'legible']
        
        # Group annotations by image
        img_annotations = {}
        for ann in valid_annotations:
            img_id = ann['image_id']
            if img_id not in img_annotations:
                img_annotations[img_id] = []
            img_annotations[img_id].append(ann)
        
        for img_id, annotations in tqdm(img_annotations.items(), desc="Processing COCO-Text"):
            if img_id not in images_dict:
                continue
                
            img_info = images_dict[img_id]
            img_path = coco_path / 'images' / img_info['file_name']
            
            if not img_path.exists():
                continue
            
            # Process text regions
            text_regions = []
            for ann in annotations:
                # COCO-Text uses polygon format
                if 'polygon' in ann:
                    polygon = ann['polygon']
                    # Convert polygon to bounding box
                    x_coords = [polygon[i] for i in range(0, len(polygon), 2)]
                    y_coords = [polygon[i] for i in range(1, len(polygon), 2)]
                    
                    x_min, x_max = min(x_coords), max(x_coords)
                    y_min, y_max = min(y_coords), max(y_coords)
                    
                    # Normalize coordinates
                    x_norm = x_min / img_info['width']
                    y_norm = y_min / img_info['height']
                    x2_norm = x_max / img_info['width']
                    y2_norm = y_max / img_info['height']
                    
                    text_regions.append({
                        'bbox': [x_norm, y_norm, x2_norm, y2_norm],
                        'text': ann.get('utf8_string', ''),
                        'category': 1,  # Generic text
                        'attributes': {'source': 'coco_text'}
                    })
            
            if text_regions:  # Only include images with text
                processed_data.append({
                    'image_path': str(img_path),
                    'image_id': img_id,
                    'width': img_info['width'],
                    'height': img_info['height'],
                    'text_regions': text_regions,
                    'dataset': 'coco_text'
                })
        
        logger.info(f"Processed {len(processed_data)} images from COCO-Text")
        return processed_data
    
    def process_custom_ic_images(self):
        """
        Process custom IC images with manual annotations
        Expected structure:
        custom_ic/
        ├── images/
        └── annotations/
            └── annotations.json
        """
        logger.info("Processing custom IC images...")
        
        custom_path = self.dataset_root / 'custom_ic'
        images_path = custom_path / 'images'
        annotations_file = custom_path / 'annotations' / 'annotations.json'
        
        if not annotations_file.exists():
            logger.warning("No custom IC annotations found")
            return []
        
        with open(annotations_file, 'r') as f:
            annotations = json.load(f)
        
        processed_data = []
        for img_name, img_data in tqdm(annotations.items(), desc="Processing custom IC"):
            img_path = images_path / img_name
            if not img_path.exists():
                continue
            
            # Load image for dimensions
            image = cv2.imread(str(img_path))
            if image is None:
                continue
                
            img_height, img_width = image.shape[:2]
            
            # Process text regions
            text_regions = []
            for region in img_data.get('regions', []):
                x1, y1, x2, y2 = region['bbox']
                
                # Normalize coordinates
                x_norm = x1 / img_width
                y_norm = y1 / img_height
                x2_norm = x2 / img_width
                y2_norm = y2 / img_height
                
                text_regions.append({
                    'bbox': [x_norm, y_norm, x2_norm, y2_norm],
                    'text': region.get('text', ''),
                    'category': region.get('category', 2),  # IC-specific
                    'attributes': {
                        'genuine': region.get('genuine', True),
                        'difficulty': region.get('difficulty', 'normal'),
                        'manufacturer': region.get('manufacturer', ''),
                        'package_type': region.get('package_type', '')
                    }
                })
            
            processed_data.append({
                'image_path': str(img_path),
                'image_id': f"custom_{img_name}",
                'width': img_width,
                'height': img_height,
                'text_regions': text_regions,
                'dataset': 'custom_ic'
            })
        
        logger.info(f"Processed {len(processed_data)} custom IC images")
        return processed_data
    
    def create_verification_dataset(self, processed_data):
        """
        Create verification dataset: (recognized_text, candidate_part_info) -> match/no_match
        """
        logger.info("Creating verification dataset...")
        
        # Load IC marking database
        db_path = Path('../ml-model/ic_dataset.csv')  # Original database
        if db_path.exists():
            ic_db = pd.read_csv(db_path)
        else:
            logger.warning("IC database not found, creating dummy database")
            ic_db = pd.DataFrame({
                'IC_Model_Number': ['ATmega328P', 'STM32F103C8T6', 'NE555P'],
                'OEM_Name': ['Microchip', 'STMicroelectronics', 'Texas Instruments'],
                'Marking_Text': ['ATmega328P', 'STM32F103', 'NE555P'],
                'Package_Type': ['DIP-28', 'LQFP-48', 'DIP-8']
            })
        
        verification_samples = []
        
        for data in processed_data:
            for region in data['text_regions']:
                text = region['text'].strip().upper()
                if len(text) < 2:  # Skip very short texts
                    continue
                
                # Create positive samples (exact matches)
                matching_ics = ic_db[ic_db['Marking_Text'].str.upper().str.contains(text, na=False)]
                for _, ic in matching_ics.iterrows():
                    verification_samples.append({
                        'recognized_text': text,
                        'candidate_marking': ic['Marking_Text'],
                        'candidate_model': ic['IC_Model_Number'],
                        'candidate_oem': ic['OEM_Name'],
                        'candidate_package': ic['Package_Type'],
                        'match_label': 1,  # Positive match
                        'source_dataset': data['dataset']
                    })
                
                # Create negative samples (random non-matches)
                non_matching = ic_db[~ic_db['Marking_Text'].str.upper().str.contains(text, na=False)]
                if len(non_matching) > 0:
                    # Sample 2-3 negative examples per positive
                    n_negative = min(3, len(non_matching))
                    negative_samples = non_matching.sample(n=n_negative)
                    
                    for _, ic in negative_samples.iterrows():
                        verification_samples.append({
                            'recognized_text': text,
                            'candidate_marking': ic['Marking_Text'],
                            'candidate_model': ic['IC_Model_Number'],
                            'candidate_oem': ic['OEM_Name'],
                            'candidate_package': ic['Package_Type'],
                            'match_label': 0,  # Negative match
                            'source_dataset': data['dataset']
                        })
        
        logger.info(f"Created {len(verification_samples)} verification samples")
        return verification_samples
    
    def split_and_save_data(self, detection_data, verification_data):
        """
        Split data into train/val/test sets and save in organized structure
        """
        logger.info("Splitting and saving data...")
        
        # Split detection data
        train_ratio, val_ratio, test_ratio = self.splits['train'], self.splits['val'], self.splits['test']
        
        # Stratify by dataset type to ensure balanced representation
        dataset_types = [item['dataset'] for item in detection_data]
        
        train_data, temp_data = train_test_split(
            detection_data, test_size=(val_ratio + test_ratio), 
            stratify=dataset_types, random_state=42
        )
        
        # Further split temp into val and test
        temp_dataset_types = [item['dataset'] for item in temp_data]
        val_size = val_ratio / (val_ratio + test_ratio)
        
        val_data, test_data = train_test_split(
            temp_data, test_size=(1 - val_size),
            stratify=temp_dataset_types, random_state=42
        )
        
        # Save detection data
        splits_data = {
            'train': train_data,
            'val': val_data,
            'test': test_data
        }
        
        for split_name, split_data in splits_data.items():
            split_dir = self.output_root / split_name
            
            # Save detection annotations
            with open(split_dir / 'detection_annotations.json', 'w') as f:
                json.dump(split_data, f, indent=2)
            
            # Copy images to split directories (optional, can use symlinks)
            logger.info(f"Saved {len(split_data)} detection samples to {split_name}")
        
        # Split and save verification data
        ver_df = pd.DataFrame(verification_data)
        if len(ver_df) > 0:
            ver_train, ver_temp = train_test_split(
                ver_df, test_size=(val_ratio + test_ratio),
                stratify=ver_df['match_label'], random_state=42
            )
            
            ver_val, ver_test = train_test_split(
                ver_temp, test_size=(1 - val_size),
                stratify=ver_temp['match_label'], random_state=42
            )
            
            # Save verification data
            ver_train.to_csv(self.output_root / 'train' / 'verification_data.csv', index=False)
            ver_val.to_csv(self.output_root / 'val' / 'verification_data.csv', index=False)
            ver_test.to_csv(self.output_root / 'test' / 'verification_data.csv', index=False)
            
            logger.info(f"Saved verification data: Train={len(ver_train)}, Val={len(ver_val)}, Test={len(ver_test)}")
        
        return splits_data
    
    def run_full_pipeline(self):
        """
        Run the complete data preprocessing pipeline
        """
        logger.info("Starting full data preprocessing pipeline...")
        
        all_detection_data = []
        
        # Process all datasets
        try:
            ictext_data = self.process_ictext_agcl()
            all_detection_data.extend(ictext_data)
        except Exception as e:
            logger.error(f"Error processing ICText-AGCL: {e}")
        
        try:
            coco_data = self.process_coco_text()
            all_detection_data.extend(coco_data)
        except Exception as e:
            logger.error(f"Error processing COCO-Text: {e}")
        
        try:
            custom_data = self.process_custom_ic_images()
            all_detection_data.extend(custom_data)
        except Exception as e:
            logger.error(f"Error processing custom IC images: {e}")
        
        # Create verification dataset
        verification_data = self.create_verification_dataset(all_detection_data)
        
        # Split and save all data
        splits_data = self.split_and_save_data(all_detection_data, verification_data)
        
        # Save summary statistics
        summary = {
            'total_images': len(all_detection_data),
            'datasets': {
                'ictext_agcl': len([d for d in all_detection_data if d['dataset'] == 'ictext_agcl']),
                'coco_text': len([d for d in all_detection_data if d['dataset'] == 'coco_text']),
                'custom_ic': len([d for d in all_detection_data if d['dataset'] == 'custom_ic'])
            },
            'splits': {
                'train': len(splits_data['train']),
                'val': len(splits_data['val']),
                'test': len(splits_data['test'])
            },
            'verification_samples': len(verification_data)
        }
        
        with open(self.output_root / 'preprocessing_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info("Data preprocessing pipeline completed!")
        logger.info(f"Summary: {summary}")
        
        return summary


if __name__ == "__main__":
    # Run preprocessing pipeline
    preprocessor = DataPreprocessor()
    summary = preprocessor.run_full_pipeline()
    print("Preprocessing completed!", summary)
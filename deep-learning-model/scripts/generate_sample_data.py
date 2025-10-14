#!/usr/bin/env python3
"""
Sample Dataset Generator for IC Recognition Training
Creates synthetic IC marking images with annotations for training
"""

import os
import json
import csv
import random
import string
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import math
from pathlib import Path
import argparse


class ICDatasetGenerator:
    """Generate synthetic IC marking dataset for training"""
    
    def __init__(self, output_dir='./data'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.output_dir / 'images').mkdir(exist_ok=True)
        (self.output_dir / 'annotations').mkdir(exist_ok=True)
        
        # IC marking patterns and manufacturers
        self.manufacturers = {
            'STMicroelectronics': ['STM32', 'STM8', 'ST', 'L78', 'LM'],
            'Texas Instruments': ['TI', 'LM', 'TL', 'CD', 'SN', 'TMS', 'MSP'],
            'Microchip': ['PIC', 'ATMEGA', 'ATTINY', 'AT', 'MCP', 'TC'],
            'Intel': ['8086', '8051', '80386', 'i7', 'XEON'],
            'AMD': ['RYZEN', 'ATHLON', 'FX'],
            'Analog Devices': ['AD', 'ADM', 'ADP', 'ADXL'],
            'Maxim': ['MAX', 'DS'],
            'NXP': ['LPC', 'MC', 'PCF'],
            'Infineon': ['IR', 'IRL', 'XMC'],
            'ON Semiconductor': ['MC', '2N', 'BC']
        }
        
        # Common IC package types
        self.package_types = ['DIP', 'SOIC', 'QFP', 'BGA', 'SSOP', 'TQFP', 'LQFP', 'MSOP', 'SOT']
        
        # Date codes and lot codes
        self.date_codes = []
        for year in range(18, 25):  # 2018-2024
            for week in range(1, 53):
                self.date_codes.append(f'{year:02d}{week:02d}')
        
        # Font variations for synthetic text
        self.font_variations = [
            {'size': 12, 'bold': False},
            {'size': 14, 'bold': True},
            {'size': 10, 'bold': False},
            {'size': 16, 'bold': True},
            {'size': 8, 'bold': False}
        ]
        
    def generate_ic_marking_text(self):
        """Generate realistic IC marking text"""
        manufacturer = random.choice(list(self.manufacturers.keys()))
        prefixes = self.manufacturers[manufacturer]
        
        # Main part number
        prefix = random.choice(prefixes)
        suffix = ''.join(random.choices(string.digits + string.ascii_uppercase, k=random.randint(3, 8)))
        part_number = f"{prefix}{suffix}"
        
        # Package type (sometimes)
        package = random.choice(self.package_types) if random.random() > 0.6 else ''
        
        # Date code
        date_code = random.choice(self.date_codes) if random.random() > 0.3 else ''
        
        # Lot code
        lot_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) if random.random() > 0.5 else ''
        
        # Assembly text lines
        lines = [part_number]
        if package:
            lines.append(package)
        if date_code:
            lines.append(date_code)
        if lot_code:
            lines.append(lot_code)
        
        # Sometimes add manufacturer logo text
        if random.random() > 0.7:
            lines.insert(0, random.choice(prefixes))
        
        return {
            'text_lines': lines,
            'manufacturer': manufacturer,
            'part_number': part_number,
            'authentic': True  # All generated are authentic
        }
    
    def generate_fake_marking_text(self):
        """Generate fake/suspicious IC marking text"""
        # Generate suspicious patterns
        patterns = [
            # Typos in known manufacturers
            'STM32F407VG'.replace('STM', 'STN'),
            'LM358N'.replace('LM', 'LN'),
            'ATMEGA328P'.replace('ATMEGA', 'ATMECA'),
            # Random gibberish
            ''.join(random.choices(string.ascii_uppercase + string.digits, k=random.randint(6, 12))),
            # Known parts with wrong suffixes
            'STM32F407XX',
            'LM358Z',
            'PIC16F84B',
            # Suspicious patterns
            'CHINA2024',
            'COPY001',
            'REV01',
        ]
        
        fake_text = random.choice(patterns)
        
        return {
            'text_lines': [fake_text],
            'manufacturer': 'Unknown',
            'part_number': fake_text,
            'authentic': False
        }
    
    def create_synthetic_image(self, text_info, width=400, height=300):
        """Create synthetic IC image with text"""
        # Create base IC package image
        image = np.ones((height, width, 3), dtype=np.uint8) * random.randint(200, 255)
        
        # Add some noise and texture
        noise = np.random.normal(0, 10, (height, width, 3)).astype(np.uint8)
        image = cv2.add(image, noise)
        
        # Add IC package outline
        package_margin = 20
        cv2.rectangle(image, 
                     (package_margin, package_margin), 
                     (width - package_margin, height - package_margin),
                     (100, 100, 100), 2)
        
        # Add pins/leads simulation
        if random.random() > 0.5:
            # DIP-style pins
            pin_count = random.choice([8, 14, 16, 20, 24, 28])
            pin_spacing = (height - 2 * package_margin) // (pin_count // 2)
            
            for i in range(pin_count // 2):
                y_pos = package_margin + i * pin_spacing + 10
                # Left pins
                cv2.rectangle(image, (5, y_pos), (package_margin, y_pos + 8), (150, 150, 150), -1)
                # Right pins
                cv2.rectangle(image, (width - package_margin, y_pos), (width - 5, y_pos + 8), (150, 150, 150), -1)
        
        # Add text using OpenCV
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = random.uniform(0.4, 0.8)
        thickness = random.randint(1, 2)
        color = (random.randint(0, 100), random.randint(0, 100), random.randint(0, 100))
        
        text_lines = text_info['text_lines']
        line_height = 25
        start_y = (height - len(text_lines) * line_height) // 2 + 30
        
        bboxes = []
        
        for i, line in enumerate(text_lines):
            # Calculate text position
            (text_width, text_height), baseline = cv2.getTextSize(line, font, font_scale, thickness)
            x = (width - text_width) // 2
            y = start_y + i * line_height
            
            # Add slight rotation sometimes
            if random.random() > 0.8:
                angle = random.uniform(-5, 5)
                center = (x + text_width // 2, y - text_height // 2)
                rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
                image = cv2.warpAffine(image, rotation_matrix, (width, height))
            
            # Draw text
            cv2.putText(image, line, (x, y), font, font_scale, color, thickness, cv2.LINE_AA)
            
            # Record bounding box
            bbox = {
                'x1': max(0, x - 5),
                'y1': max(0, y - text_height - 5),
                'x2': min(width, x + text_width + 5),
                'y2': min(height, y + baseline + 5),
                'text': line
            }
            bboxes.append(bbox)
        
        # Add some image degradation effects
        degradation_type = random.choice(['blur', 'noise', 'brightness', 'contrast', 'none'])
        
        if degradation_type == 'blur':
            kernel_size = random.choice([3, 5])
            image = cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
        elif degradation_type == 'noise':
            noise = np.random.normal(0, 15, image.shape).astype(np.uint8)
            image = cv2.add(image, noise)
        elif degradation_type == 'brightness':
            brightness = random.uniform(0.7, 1.3)
            image = cv2.convertScaleAbs(image, alpha=brightness, beta=0)
        elif degradation_type == 'contrast':
            contrast = random.uniform(0.8, 1.2)
            image = cv2.convertScaleAbs(image, alpha=contrast, beta=0)
        
        return image, bboxes
    
    def generate_dataset(self, num_samples=1000, train_ratio=0.7, val_ratio=0.2):
        """Generate complete dataset with train/val/test splits"""
        
        print(f"Generating {num_samples} samples...")
        
        # Calculate splits
        num_train = int(num_samples * train_ratio)
        num_val = int(num_samples * val_ratio)
        num_test = num_samples - num_train - num_val
        
        splits = {
            'train': num_train,
            'val': num_val,
            'test': num_test
        }
        
        all_annotations = []
        verification_pairs = []
        
        sample_id = 0
        
        for split_name, split_count in splits.items():
            print(f"Generating {split_name} set: {split_count} samples")
            
            split_dir = self.output_dir / 'images' / split_name
            split_dir.mkdir(exist_ok=True)
            
            for i in range(split_count):
                # 80% authentic, 20% fake
                is_authentic = random.random() > 0.2
                
                if is_authentic:
                    text_info = self.generate_ic_marking_text()
                else:
                    text_info = self.generate_fake_marking_text()
                
                # Generate image
                image, bboxes = self.create_synthetic_image(text_info)
                
                # Save image
                image_filename = f"ic_{sample_id:06d}.jpg"
                image_path = split_dir / image_filename
                cv2.imwrite(str(image_path), image)
                
                # Create annotation
                annotation = {
                    'image_id': sample_id,
                    'image_path': str(image_path.relative_to(self.output_dir)),
                    'split': split_name,
                    'width': image.shape[1],
                    'height': image.shape[0],
                    'text_info': text_info,
                    'bboxes': bboxes
                }
                all_annotations.append(annotation)
                
                # Create verification pair
                verification_pair = {
                    'image_id': sample_id,
                    'recognized_text': ' '.join(text_info['text_lines']),
                    'part_number': text_info['part_number'],
                    'manufacturer': text_info['manufacturer'],
                    'authentic': text_info['authentic'],
                    'confidence': 1.0 if text_info['authentic'] else 0.0
                }
                verification_pairs.append(verification_pair)
                
                sample_id += 1
                
                if (i + 1) % 100 == 0:
                    print(f"  Generated {i + 1}/{split_count} samples")
        
        # Save annotations
        annotations_file = self.output_dir / 'annotations' / 'dataset_annotations.json'
        with open(annotations_file, 'w') as f:
            json.dump(all_annotations, f, indent=2)
        
        # Save verification pairs
        verification_file = self.output_dir / 'annotations' / 'verification_pairs.json'
        with open(verification_file, 'w') as f:
            json.dump(verification_pairs, f, indent=2)
        
        # Save IC database CSV
        self._create_ic_database()
        
        # Save dataset statistics
        self._save_dataset_stats(all_annotations, verification_pairs)
        
        print(f"\nDataset generation complete!")
        print(f"Total samples: {len(all_annotations)}")
        print(f"Train: {num_train}, Val: {num_val}, Test: {num_test}")
        print(f"Authentic: {sum(1 for vp in verification_pairs if vp['authentic'])}")
        print(f"Fake: {sum(1 for vp in verification_pairs if not vp['authentic'])}")
        
        return all_annotations, verification_pairs
    
    def _create_ic_database(self):
        """Create IC database for verification"""
        ic_database = []
        
        # Add known authentic parts
        for manufacturer, prefixes in self.manufacturers.items():
            for prefix in prefixes:
                for i in range(10):  # Generate several parts per prefix
                    suffix = ''.join(random.choices(string.digits + string.ascii_uppercase, k=random.randint(3, 6)))
                    part_number = f"{prefix}{suffix}"
                    
                    ic_database.append({
                        'part_number': part_number,
                        'manufacturer': manufacturer,
                        'package': random.choice(self.package_types),
                        'description': f'{manufacturer} {random.choice(["Microcontroller", "Op-Amp", "Logic Gate", "Timer", "Regulator"])}',
                        'status': 'active'
                    })
        
        # Save as CSV
        csv_file = self.output_dir / 'ic_database.csv'
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['part_number', 'manufacturer', 'package', 'description', 'status'])
            writer.writeheader()
            writer.writerows(ic_database)
        
        print(f"Created IC database with {len(ic_database)} entries")
    
    def _save_dataset_stats(self, annotations, verification_pairs):
        """Save dataset statistics"""
        stats = {
            'total_images': len(annotations),
            'total_text_regions': sum(len(ann['bboxes']) for ann in annotations),
            'authentic_count': sum(1 for vp in verification_pairs if vp['authentic']),
            'fake_count': sum(1 for vp in verification_pairs if not vp['authentic']),
            'manufacturers': list(self.manufacturers.keys()),
            'splits': {
                split: len([ann for ann in annotations if ann['split'] == split])
                for split in ['train', 'val', 'test']
            }
        }
        
        stats_file = self.output_dir / 'dataset_stats.json'
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description='Generate IC marking dataset')
    parser.add_argument('--output-dir', default='./data', help='Output directory')
    parser.add_argument('--num-samples', type=int, default=1000, help='Number of samples to generate')
    parser.add_argument('--train-ratio', type=float, default=0.7, help='Training set ratio')
    parser.add_argument('--val-ratio', type=float, default=0.2, help='Validation set ratio')
    
    args = parser.parse_args()
    
    # Generate dataset
    generator = ICDatasetGenerator(args.output_dir)
    annotations, verification_pairs = generator.generate_dataset(
        num_samples=args.num_samples,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio
    )
    
    print(f"\n✅ Dataset generation completed successfully!")
    print(f"📁 Output directory: {args.output_dir}")
    print(f"📊 Statistics saved to: {args.output_dir}/dataset_stats.json")


if __name__ == "__main__":
    main()
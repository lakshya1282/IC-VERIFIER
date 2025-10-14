#!/usr/bin/env python3
"""
Enhanced OEM Data Fetcher with PDF Parsing Capabilities
Automatically retrieves, downloads, and parses IC datasheet PDFs to extract marking information
Uses GROBID for document structure parsing and pdfminer for text extraction
"""

import os
import re
import json
import time
import hashlib
import logging
import requests
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse
from io import BytesIO

# PDF processing imports
import pdfminer
from pdfminer.high_level import extract_text, extract_pages
from pdfminer.layout import LTTextContainer, LTTextBox, LTFigure, LTImage
import fitz  # PyMuPDF for better PDF processing

# Optional GROBID integration (requires GROBID server)
try:
    from grobid_client.grobid_client import GrobidClient
    GROBID_AVAILABLE = True
except ImportError:
    GROBID_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedOEMDataFetcher:
    """
    Enhanced OEM Data Fetcher with comprehensive PDF parsing capabilities
    """
    
    def __init__(self, cache_dir: str = "./oem_cache", grobid_server: str = None):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.cache_dir / 'pdfs').mkdir(exist_ok=True)
        (self.cache_dir / 'parsed').mkdir(exist_ok=True)
        (self.cache_dir / 'markings').mkdir(exist_ok=True)
        
        # GROBID client setup
        self.grobid_client = None
        if grobid_server and GROBID_AVAILABLE:
            try:
                self.grobid_client = GrobidClient(grobid_server=grobid_server)
                logger.info("✅ GROBID client initialized")
            except Exception as e:
                logger.warning(f"Could not initialize GROBID client: {e}")
        
        # Load enhanced datasheets database
        self.load_enhanced_database()
        
        # Marking patterns to search for in PDFs
        self.marking_patterns = {
            'top_marking': [
                r'top\s+mark(?:ing)?',
                r'part\s+mark(?:ing)?', 
                r'package\s+mark(?:ing)?',
                r'device\s+mark(?:ing)?',
                r'IC\s+mark(?:ing)?'
            ],
            'marking_table': [
                r'marking\s+information',
                r'part\s+numbering',
                r'ordering\s+information',
                r'device\s+information'
            ],
            'package_info': [
                r'package\s+type',
                r'package\s+outline',
                r'mechanical\s+data'
            ]
        }
        
        # Common IC marking format patterns
        self.ic_marking_formats = [
            r'[A-Z]{2,6}[0-9]{2,6}[A-Z]*',  # Standard IC format
            r'[0-9]{2,4}[A-Z]{2,4}',        # Date code + part
            r'[A-Z]+[0-9]+[A-Z]*[-_][A-Z0-9]+',  # Complex part numbers
        ]
    
    def load_enhanced_database(self):
        """Load the enhanced datasheets database"""
        try:
            enhanced_db_path = self.cache_dir.parent / 'data' / 'enhanced_datasheets.csv'
            if enhanced_db_path.exists():
                self.datasheets_db = pd.read_csv(enhanced_db_path)
                logger.info(f"✅ Loaded {len(self.datasheets_db)} IC records from enhanced database")
            else:
                logger.warning("Enhanced datasheets database not found, creating empty database")
                self.datasheets_db = pd.DataFrame(columns=[
                    'Part', 'Manufacturer', 'Datasheet_URL', 'Notes', 'Package_Types', 'Marking_Text'
                ])
        except Exception as e:
            logger.error(f"Error loading enhanced database: {e}")
            self.datasheets_db = pd.DataFrame()
    
    def download_datasheet_pdf(self, url: str, part_number: str) -> Optional[Path]:
        """
        Download PDF datasheet from URL
        
        Args:
            url: Datasheet PDF URL
            part_number: IC part number for filename
            
        Returns:
            Path to downloaded PDF file
        """
        try:
            # Create safe filename
            safe_filename = re.sub(r'[^\w\-_.]', '_', part_number)
            pdf_path = self.cache_dir / 'pdfs' / f"{safe_filename}.pdf"
            
            # Check if already downloaded
            if pdf_path.exists():
                logger.info(f"✅ PDF already cached: {pdf_path}")
                return pdf_path
            
            # Download PDF
            logger.info(f"📥 Downloading PDF: {url}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Verify it's a PDF
            if not response.content.startswith(b'%PDF'):
                logger.warning(f"Downloaded content is not a valid PDF: {url}")
                return None
            
            # Save PDF
            with open(pdf_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"✅ PDF downloaded: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            logger.error(f"Error downloading PDF from {url}: {e}")
            return None
    
    def parse_pdf_with_grobid(self, pdf_path: Path) -> Optional[Dict]:
        """
        Parse PDF using GROBID for structured extraction
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Parsed document structure
        """
        if not self.grobid_client:
            return None
        
        try:
            logger.info(f"🔍 Parsing PDF with GROBID: {pdf_path}")
            
            # Process with GROBID
            with open(pdf_path, 'rb') as pdf_file:
                result = self.grobid_client.process_pdf(
                    service='processFulltextDocument',
                    pdf_file=pdf_file,
                    generateIDs=True,
                    consolidate_header=True,
                    consolidate_citations=True
                )
            
            if result[0] == 200:  # Success
                # Parse the TEI XML result
                parsed_data = self.parse_grobid_xml(result[1])
                
                # Cache parsed result
                cache_path = self.cache_dir / 'parsed' / f"{pdf_path.stem}_grobid.json"
                with open(cache_path, 'w') as f:
                    json.dump(parsed_data, f, indent=2)
                
                return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing PDF with GROBID: {e}")
        
        return None
    
    def parse_pdf_with_pdfminer(self, pdf_path: Path) -> Dict:
        """
        Parse PDF using pdfminer for text extraction
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text and metadata
        """
        try:
            logger.info(f"🔍 Parsing PDF with pdfminer: {pdf_path}")
            
            # Extract full text
            full_text = extract_text(str(pdf_path))
            
            # Extract page-by-page with layout information
            pages_data = []
            for page_layout in extract_pages(str(pdf_path)):
                page_text = ""
                text_boxes = []
                
                for element in page_layout:
                    if isinstance(element, LTTextContainer):
                        text = element.get_text().strip()
                        if text:
                            page_text += text + " "
                            text_boxes.append({
                                'text': text,
                                'bbox': element.bbox,
                                'height': element.height,
                                'width': element.width
                            })
                
                pages_data.append({
                    'page_number': len(pages_data) + 1,
                    'text': page_text.strip(),
                    'text_boxes': text_boxes
                })
            
            parsed_data = {
                'full_text': full_text,
                'pages': pages_data,
                'page_count': len(pages_data),
                'extraction_method': 'pdfminer'
            }
            
            # Cache result
            cache_path = self.cache_dir / 'parsed' / f"{pdf_path.stem}_pdfminer.json"
            with open(cache_path, 'w') as f:
                json.dump(parsed_data, f, indent=2, default=str)
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing PDF with pdfminer: {e}")
            return {'full_text': '', 'pages': [], 'page_count': 0, 'error': str(e)}
    
    def parse_pdf_with_pymupdf(self, pdf_path: Path) -> Dict:
        """
        Parse PDF using PyMuPDF for enhanced text extraction
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text with position information
        """
        try:
            logger.info(f"🔍 Parsing PDF with PyMuPDF: {pdf_path}")
            
            doc = fitz.open(str(pdf_path))
            pages_data = []
            full_text = ""
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                
                # Extract text with position information
                text_dict = page.get_text("dict")
                page_text = page.get_text()
                full_text += page_text
                
                # Extract text blocks with formatting
                blocks = []
                for block in text_dict["blocks"]:
                    if "lines" in block:  # Text block
                        block_text = ""
                        for line in block["lines"]:
                            for span in line["spans"]:
                                block_text += span["text"] + " "
                        
                        if block_text.strip():
                            blocks.append({
                                'text': block_text.strip(),
                                'bbox': block["bbox"],
                                'block_type': 'text'
                            })
                
                pages_data.append({
                    'page_number': page_num + 1,
                    'text': page_text,
                    'blocks': blocks,
                    'width': page.rect.width,
                    'height': page.rect.height
                })
            
            doc.close()
            
            parsed_data = {
                'full_text': full_text,
                'pages': pages_data,
                'page_count': len(pages_data),
                'extraction_method': 'pymupdf'
            }
            
            # Cache result
            cache_path = self.cache_dir / 'parsed' / f"{pdf_path.stem}_pymupdf.json"
            with open(cache_path, 'w') as f:
                json.dump(parsed_data, f, indent=2, default=str)
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing PDF with PyMuPDF: {e}")
            return {'full_text': '', 'pages': [], 'page_count': 0, 'error': str(e)}
    
    def extract_marking_information(self, parsed_data: Dict, part_number: str) -> Dict:
        """
        Extract IC marking information from parsed PDF data
        
        Args:
            parsed_data: Parsed PDF content
            part_number: IC part number
            
        Returns:
            Extracted marking information
        """
        logger.info(f"🔍 Extracting marking information for {part_number}")
        
        full_text = parsed_data.get('full_text', '').lower()
        pages = parsed_data.get('pages', [])
        
        marking_info = {
            'part_number': part_number,
            'extraction_date': datetime.now().isoformat(),
            'found_markings': [],
            'package_info': {},
            'marking_tables': [],
            'relevant_sections': []
        }
        
        # Search for marking-related sections
        for pattern_type, patterns in self.marking_patterns.items():
            for pattern in patterns:
                matches = list(re.finditer(pattern, full_text, re.IGNORECASE))
                if matches:
                    logger.info(f"Found {pattern_type} pattern: {pattern}")
                    marking_info['relevant_sections'].append({
                        'pattern_type': pattern_type,
                        'pattern': pattern,
                        'matches': len(matches)
                    })
        
        # Extract potential IC markings using format patterns
        for format_pattern in self.ic_marking_formats:
            matches = re.findall(format_pattern, full_text.upper())
            for match in matches:
                if len(match) >= 4:  # Reasonable minimum length
                    marking_info['found_markings'].append({
                        'text': match,
                        'pattern': format_pattern,
                        'confidence': self.calculate_marking_confidence(match, part_number)
                    })
        
        # Look for package information
        package_keywords = ['dip', 'soic', 'qfp', 'bga', 'qfn', 'sot', 'tssop', 'msop']
        for keyword in package_keywords:
            if keyword in full_text:
                # Find context around package mention
                context = self.extract_context_around_keyword(full_text, keyword, 100)
                if context:
                    marking_info['package_info'][keyword] = context
        
        # Search for tabular marking information
        marking_tables = self.extract_marking_tables(pages, part_number)
        marking_info['marking_tables'] = marking_tables
        
        # Cache extracted information
        cache_path = self.cache_dir / 'markings' / f"{part_number}_markings.json"
        with open(cache_path, 'w') as f:
            json.dump(marking_info, f, indent=2, default=str)
        
        return marking_info
    
    def calculate_marking_confidence(self, marking_text: str, part_number: str) -> float:
        """Calculate confidence score for extracted marking"""
        confidence = 0.0
        
        # Higher confidence for markings similar to part number
        if part_number.upper() in marking_text.upper():
            confidence += 0.5
        
        # Check character similarity
        common_chars = set(marking_text.upper()) & set(part_number.upper())
        if common_chars:
            confidence += min(len(common_chars) / max(len(part_number), len(marking_text)), 0.3)
        
        # Reasonable length check
        if 4 <= len(marking_text) <= 20:
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def extract_context_around_keyword(self, text: str, keyword: str, context_length: int = 100) -> str:
        """Extract text context around a keyword"""
        keyword_pos = text.lower().find(keyword.lower())
        if keyword_pos == -1:
            return ""
        
        start = max(0, keyword_pos - context_length)
        end = min(len(text), keyword_pos + len(keyword) + context_length)
        
        return text[start:end].strip()
    
    def extract_marking_tables(self, pages: List[Dict], part_number: str) -> List[Dict]:
        """Extract tabular marking information from pages"""
        tables = []
        
        for page in pages:
            page_text = page.get('text', '')
            
            # Look for table-like structures
            lines = page_text.split('\n')
            potential_table_lines = []
            
            for line in lines:
                # Check if line looks like a table row
                if '|' in line or '\t' in line or re.search(r'\s{3,}', line):
                    # Contains part number or marking-related keywords
                    if (part_number.upper() in line.upper() or 
                        any(keyword in line.lower() for keyword in ['mark', 'part', 'device'])):
                        potential_table_lines.append(line.strip())
            
            if potential_table_lines:
                tables.append({
                    'page_number': page.get('page_number', 0),
                    'table_lines': potential_table_lines
                })
        
        return tables
    
    def process_datasheet_comprehensive(self, part_number: str) -> Dict:
        """
        Comprehensively process a datasheet for marking information
        
        Args:
            part_number: IC part number
            
        Returns:
            Complete marking information
        """
        logger.info(f"🚀 Starting comprehensive datasheet processing for {part_number}")
        
        result = {
            'part_number': part_number,
            'processing_date': datetime.now().isoformat(),
            'success': False,
            'datasheet_url': None,
            'pdf_path': None,
            'parsed_data': {},
            'marking_info': {},
            'errors': []
        }
        
        try:
            # 1. Find datasheet URL
            datasheet_row = self.datasheets_db[
                self.datasheets_db['Part'].str.contains(part_number, case=False, na=False)
            ]
            
            if datasheet_row.empty:
                result['errors'].append(f"No datasheet URL found for {part_number}")
                return result
            
            datasheet_url = datasheet_row.iloc[0]['Datasheet_URL']
            result['datasheet_url'] = datasheet_url
            
            # 2. Download PDF
            pdf_path = self.download_datasheet_pdf(datasheet_url, part_number)
            if not pdf_path:
                result['errors'].append("Failed to download PDF")
                return result
            
            result['pdf_path'] = str(pdf_path)
            
            # 3. Parse PDF with multiple methods
            parsing_results = {}
            
            # Try PyMuPDF first (usually best results)
            parsing_results['pymupdf'] = self.parse_pdf_with_pymupdf(pdf_path)
            
            # Try pdfminer as backup
            parsing_results['pdfminer'] = self.parse_pdf_with_pdfminer(pdf_path)
            
            # Try GROBID if available
            if self.grobid_client:
                grobid_result = self.parse_pdf_with_grobid(pdf_path)
                if grobid_result:
                    parsing_results['grobid'] = grobid_result
            
            result['parsed_data'] = parsing_results
            
            # 4. Extract marking information
            # Use the best parsing result (prefer PyMuPDF, then pdfminer)
            best_parsed_data = parsing_results.get('pymupdf', parsing_results.get('pdfminer', {}))
            
            if best_parsed_data.get('full_text'):
                marking_info = self.extract_marking_information(best_parsed_data, part_number)
                result['marking_info'] = marking_info
                result['success'] = True
            else:
                result['errors'].append("No text could be extracted from PDF")
            
        except Exception as e:
            error_msg = f"Error processing datasheet: {str(e)}"
            result['errors'].append(error_msg)
            logger.error(error_msg)
        
        # Save comprehensive result
        result_path = self.cache_dir / 'markings' / f"{part_number}_comprehensive.json"
        with open(result_path, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        logger.info(f"✅ Comprehensive processing complete for {part_number}")
        return result
    
    def batch_process_datasheets(self, part_numbers: List[str] = None) -> Dict:
        """
        Batch process multiple datasheets
        
        Args:
            part_numbers: List of part numbers to process (None = all in database)
            
        Returns:
            Batch processing results
        """
        if part_numbers is None:
            part_numbers = self.datasheets_db['Part'].tolist()
        
        logger.info(f"🚀 Starting batch processing of {len(part_numbers)} datasheets")
        
        results = {
            'processed_count': 0,
            'successful_count': 0,
            'failed_count': 0,
            'results': [],
            'start_time': datetime.now().isoformat()
        }
        
        for i, part_number in enumerate(part_numbers):
            logger.info(f"📋 Processing {i+1}/{len(part_numbers)}: {part_number}")
            
            try:
                result = self.process_datasheet_comprehensive(part_number)
                results['results'].append(result)
                results['processed_count'] += 1
                
                if result['success']:
                    results['successful_count'] += 1
                    logger.info(f"✅ Success: {part_number}")
                else:
                    results['failed_count'] += 1
                    logger.warning(f"❌ Failed: {part_number}")
                
                # Add small delay to be respectful to servers
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing {part_number}: {e}")
                results['failed_count'] += 1
        
        results['end_time'] = datetime.now().isoformat()
        
        # Save batch results
        batch_result_path = self.cache_dir / f"batch_results_{int(time.time())}.json"
        with open(batch_result_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"🎉 Batch processing complete: {results['successful_count']}/{results['processed_count']} successful")
        return results

def main():
    """Example usage of Enhanced OEM Data Fetcher"""
    
    # Initialize with GROBID server (optional)
    # fetcher = EnhancedOEMDataFetcher(grobid_server="http://localhost:8070")
    fetcher = EnhancedOEMDataFetcher()
    
    # Example: Process a single IC
    part_number = "STM32F103C8T6"
    result = fetcher.process_datasheet_comprehensive(part_number)
    
    print("\n📊 Processing Result:")
    print(f"Success: {result['success']}")
    print(f"Datasheet URL: {result['datasheet_url']}")
    print(f"Errors: {result['errors']}")
    
    if result['success']:
        marking_info = result.get('marking_info', {})
        print(f"Found markings: {len(marking_info.get('found_markings', []))}")
        print(f"Package info: {list(marking_info.get('package_info', {}).keys())}")
    
    # Example: Batch process first 5 ICs
    # batch_result = fetcher.batch_process_datasheets(part_numbers=["STM32F103C8T6", "ATmega328P", "LM358"])
    # print(f"\nBatch result: {batch_result['successful_count']}/{batch_result['processed_count']} successful")

if __name__ == "__main__":
    main()
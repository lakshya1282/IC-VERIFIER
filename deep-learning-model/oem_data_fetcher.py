"""
Advanced OEM Data Fetcher Module
Automatically retrieves and updates IC marking information from OEM websites
"""

import os
import re
import json
import time
import hashlib
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import PyPDF2
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import numpy as np
from urllib.parse import urljoin, urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OEMDataFetcher:
    """
    Intelligent OEM Data Fetcher
    Automatically retrieves IC marking information from manufacturer websites
    """
    
    def __init__(self, cache_dir: str = "./oem_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # OEM website configurations
        self.oem_sites = {
            'STMicroelectronics': {
                'base_url': 'https://www.st.com',
                'search_url': 'https://www.st.com/content/st_com/en/search.html#q={part_number}',
                'datasheet_pattern': r'\.pdf$'
            },
            'Texas Instruments': {
                'base_url': 'https://www.ti.com',
                'search_url': 'https://www.ti.com/search?q={part_number}',
                'datasheet_pattern': r'datasheet.*\.pdf'
            },
            'Microchip': {
                'base_url': 'https://www.microchip.com',
                'search_url': 'https://www.microchip.com/en-us/search?searchQuery={part_number}',
                'datasheet_pattern': r'\.pdf$'
            },
            'Analog Devices': {
                'base_url': 'https://www.analog.com',
                'search_url': 'https://www.analog.com/en/search.html?q={part_number}',
                'datasheet_pattern': r'\.pdf$'
            },
            'NXP': {
                'base_url': 'https://www.nxp.com',
                'search_url': 'https://www.nxp.com/search?keyword={part_number}',
                'datasheet_pattern': r'data.*sheet.*\.pdf'
            }
        }
        
        # Database for verified markings
        self.marking_database = self.load_marking_database()
        
        # Setup selenium driver
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Setup Chrome driver for web scraping"""
        try:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            
            # Note: Requires ChromeDriver to be installed
            # self.driver = webdriver.Chrome(options=options)
            logger.info("Web driver setup for advanced scraping (requires ChromeDriver)")
        except Exception as e:
            logger.warning(f"Could not setup Selenium driver: {e}")
            logger.info("Will use basic HTTP requests for scraping")
    
    def search_oem_datasheet(self, part_number: str, manufacturer: str = None) -> Optional[str]:
        """
        Search for datasheet URL for a given part number
        
        Args:
            part_number: IC part number to search
            manufacturer: Optional manufacturer name
            
        Returns:
            URL of the datasheet if found
        """
        # Check cache first
        cached_url = self.check_cache(part_number)
        if cached_url:
            logger.info(f"Found cached datasheet for {part_number}")
            return cached_url
        
        # Determine manufacturer if not provided
        if not manufacturer:
            manufacturer = self.identify_manufacturer(part_number)
        
        if manufacturer and manufacturer in self.oem_sites:
            config = self.oem_sites[manufacturer]
            search_url = config['search_url'].format(part_number=part_number)
            
            try:
                # Try to find datasheet URL
                datasheet_url = self.scrape_datasheet_url(search_url, config)
                if datasheet_url:
                    self.cache_datasheet_url(part_number, datasheet_url)
                    return datasheet_url
            except Exception as e:
                logger.error(f"Error searching for {part_number}: {e}")
        
        # Fallback to general search
        return self.general_datasheet_search(part_number)
    
    def identify_manufacturer(self, part_number: str) -> Optional[str]:
        """
        Identify manufacturer from part number patterns
        
        Args:
            part_number: IC part number
            
        Returns:
            Manufacturer name if identified
        """
        patterns = {
            'STMicroelectronics': [r'^STM', r'^ST[0-9]', r'^L[0-9]{3}'],
            'Texas Instruments': [r'^TL', r'^LM', r'^NE', r'^TPS', r'^MSP'],
            'Microchip': [r'^PIC', r'^AT', r'^MCP', r'^24[LC]'],
            'Analog Devices': [r'^AD[0-9]', r'^ADU', r'^ADP', r'^LT[0-9]'],
            'NXP': [r'^MC', r'^MK', r'^S9', r'^P8', r'^LPC']
        }
        
        part_upper = part_number.upper()
        for manufacturer, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.match(pattern, part_upper):
                    logger.info(f"Identified {manufacturer} for {part_number}")
                    return manufacturer
        
        return None
    
    def scrape_datasheet_url(self, search_url: str, config: dict) -> Optional[str]:
        """
        Scrape datasheet URL from search results
        
        Args:
            search_url: URL to search
            config: OEM site configuration
            
        Returns:
            Datasheet URL if found
        """
        try:
            response = requests.get(search_url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for PDF links
                pdf_links = soup.find_all('a', href=re.compile(config['datasheet_pattern'], re.I))
                
                for link in pdf_links:
                    href = link.get('href')
                    if href:
                        # Make absolute URL
                        if not href.startswith('http'):
                            href = urljoin(config['base_url'], href)
                        
                        # Verify it's a datasheet
                        if self.verify_datasheet_link(href):
                            return href
        except Exception as e:
            logger.error(f"Error scraping {search_url}: {e}")
        
        return None
    
    def verify_datasheet_link(self, url: str) -> bool:
        """
        Verify that a URL points to a valid datasheet
        
        Args:
            url: URL to verify
            
        Returns:
            True if valid datasheet
        """
        try:
            # Check if URL ends with .pdf
            if not url.lower().endswith('.pdf'):
                return False
            
            # Try HEAD request to check if exists
            response = requests.head(url, timeout=5, allow_redirects=True)
            
            # Check content type
            content_type = response.headers.get('Content-Type', '')
            if 'pdf' in content_type.lower():
                return True
                
        except Exception as e:
            logger.debug(f"Could not verify {url}: {e}")
        
        return False
    
    def general_datasheet_search(self, part_number: str) -> Optional[str]:
        """
        Perform general web search for datasheet
        
        Args:
            part_number: IC part number
            
        Returns:
            Datasheet URL if found
        """
        # Search using common datasheet repositories
        repositories = [
            f"https://www.alldatasheet.com/view.jsp?Searchword={part_number}",
            f"https://pdf1.alldatasheet.com/datasheet-pdf/view/{part_number}.html",
            f"https://www.datasheets.com/search?q={part_number}",
            f"https://octopart.com/search?q={part_number}"
        ]
        
        for repo_url in repositories:
            try:
                datasheet_url = self.scrape_datasheet_url(repo_url, {
                    'base_url': urlparse(repo_url).netloc,
                    'datasheet_pattern': r'\.pdf$'
                })
                
                if datasheet_url:
                    return datasheet_url
                    
            except Exception as e:
                logger.debug(f"Repository search failed for {repo_url}: {e}")
        
        return None
    
    def download_datasheet(self, url: str, part_number: str) -> Optional[Path]:
        """
        Download datasheet PDF
        
        Args:
            url: Datasheet URL
            part_number: IC part number for naming
            
        Returns:
            Path to downloaded file
        """
        try:
            file_name = f"{part_number}_{hashlib.md5(url.encode()).hexdigest()[:8]}.pdf"
            file_path = self.cache_dir / file_name
            
            if file_path.exists():
                logger.info(f"Datasheet already downloaded: {file_path}")
                return file_path
            
            response = requests.get(url, timeout=30, stream=True)
            if response.status_code == 200:
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                logger.info(f"Downloaded datasheet to {file_path}")
                return file_path
                
        except Exception as e:
            logger.error(f"Error downloading datasheet: {e}")
        
        return None
    
    def extract_marking_info(self, pdf_path: Path) -> Dict:
        """
        Extract marking information from datasheet PDF
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with marking information
        """
        marking_info = {
            'marking_format': None,
            'date_codes': [],
            'lot_codes': [],
            'package_markings': {},
            'laser_marking': False,
            'inkjet_marking': False,
            'additional_info': []
        }
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Search for marking information in PDF
                marking_keywords = [
                    'marking', 'part marking', 'device marking',
                    'package marking', 'top marking', 'laser marking',
                    'date code', 'lot code', 'trace code'
                ]
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text().lower()
                    
                    # Look for marking section
                    for keyword in marking_keywords:
                        if keyword in text:
                            # Extract relevant section
                            lines = text.split('\n')
                            for i, line in enumerate(lines):
                                if keyword in line:
                                    # Get context (few lines around keyword)
                                    context_start = max(0, i - 5)
                                    context_end = min(len(lines), i + 10)
                                    context = '\n'.join(lines[context_start:context_end])
                                    
                                    # Parse marking information
                                    self.parse_marking_context(context, marking_info)
                
                # Look for marking diagrams/images (advanced)
                # This would require OCR on images within PDF
                
        except Exception as e:
            logger.error(f"Error extracting from PDF: {e}")
        
        return marking_info
    
    def parse_marking_context(self, context: str, marking_info: dict):
        """
        Parse marking information from text context
        
        Args:
            context: Text context containing marking info
            marking_info: Dictionary to update with parsed info
        """
        # Extract marking format
        format_patterns = [
            r'marking\s*format[:\s]+([^\n]+)',
            r'top\s*marking[:\s]+([^\n]+)',
            r'marking\s*code[:\s]+([^\n]+)'
        ]
        
        for pattern in format_patterns:
            match = re.search(pattern, context, re.I)
            if match:
                marking_info['marking_format'] = match.group(1).strip()
                break
        
        # Extract date code format
        date_patterns = [
            r'date\s*code[:\s]+([^\n]+)',
            r'year\s*week[:\s]+([^\n]+)',
            r'yyww'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, context, re.I)
            if match:
                marking_info['date_codes'].append(match.group(1) if match.lastindex else pattern)
        
        # Detect marking type
        if 'laser' in context:
            marking_info['laser_marking'] = True
        if 'inkjet' in context or 'ink' in context:
            marking_info['inkjet_marking'] = True
    
    def validate_ic_marking(self, marking: str, part_number: str) -> Tuple[bool, float, str]:
        """
        Validate IC marking against OEM database
        
        Args:
            marking: Actual marking on IC
            part_number: Expected part number
            
        Returns:
            Tuple of (is_valid, confidence, message)
        """
        # First check local database
        if part_number in self.marking_database:
            expected_pattern = self.marking_database[part_number]
            if self.match_marking_pattern(marking, expected_pattern):
                return True, 1.0, "Marking matches OEM database"
        
        # Try to fetch from OEM website
        datasheet_url = self.search_oem_datasheet(part_number)
        
        if datasheet_url:
            # Download and extract marking info
            pdf_path = self.download_datasheet(datasheet_url, part_number)
            if pdf_path:
                marking_info = self.extract_marking_info(pdf_path)
                
                # Update database
                self.marking_database[part_number] = marking_info
                self.save_marking_database()
                
                # Validate against extracted info
                if marking_info['marking_format']:
                    if self.match_marking_pattern(marking, marking_info['marking_format']):
                        return True, 0.95, "Marking matches datasheet specification"
        
        # Fuzzy matching as fallback
        similarity = self.calculate_marking_similarity(marking, part_number)
        if similarity > 0.8:
            return True, similarity, f"High similarity ({similarity:.2%}) to expected marking"
        
        return False, similarity, "Marking does not match OEM specifications"
    
    def match_marking_pattern(self, marking: str, pattern: str) -> bool:
        """
        Match marking against pattern
        
        Args:
            marking: Actual marking
            pattern: Expected pattern
            
        Returns:
            True if matches
        """
        # Simple pattern matching (can be made more sophisticated)
        # Handle wildcards, date codes, etc.
        pattern_regex = pattern.replace('YYWW', r'\d{4}')  # Year-Week
        pattern_regex = pattern_regex.replace('XXXX', r'.{4}')  # Any 4 characters
        pattern_regex = pattern_regex.replace('*', '.*')  # Wildcard
        
        try:
            return bool(re.match(pattern_regex, marking, re.I))
        except:
            # Fallback to simple comparison
            return marking.upper() == pattern.upper()
    
    def calculate_marking_similarity(self, marking: str, expected: str) -> float:
        """
        Calculate similarity between markings
        
        Args:
            marking: Actual marking
            expected: Expected marking
            
        Returns:
            Similarity score (0-1)
        """
        from difflib import SequenceMatcher
        
        # Normalize strings
        marking = marking.upper().replace(' ', '')
        expected = expected.upper().replace(' ', '')
        
        # Calculate similarity
        similarity = SequenceMatcher(None, marking, expected).ratio()
        
        # Boost score if key parts match
        if marking[:3] == expected[:3]:  # Prefix match
            similarity = min(1.0, similarity * 1.2)
        
        return similarity
    
    def check_cache(self, part_number: str) -> Optional[str]:
        """Check if datasheet URL is cached"""
        cache_file = self.cache_dir / 'url_cache.json'
        
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                cache = json.load(f)
                
                if part_number in cache:
                    # Check if cache is not too old (30 days)
                    cached_time = datetime.fromisoformat(cache[part_number]['timestamp'])
                    if datetime.now() - cached_time < timedelta(days=30):
                        return cache[part_number]['url']
        
        return None
    
    def cache_datasheet_url(self, part_number: str, url: str):
        """Cache datasheet URL"""
        cache_file = self.cache_dir / 'url_cache.json'
        
        cache = {}
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                cache = json.load(f)
        
        cache[part_number] = {
            'url': url,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(cache_file, 'w') as f:
            json.dump(cache, f, indent=2)
    
    def load_marking_database(self) -> Dict:
        """Load marking database from file"""
        db_file = self.cache_dir / 'marking_database.json'
        
        if db_file.exists():
            with open(db_file, 'r') as f:
                return json.load(f)
        
        return {}
    
    def save_marking_database(self):
        """Save marking database to file"""
        db_file = self.cache_dir / 'marking_database.json'
        
        with open(db_file, 'w') as f:
            json.dump(self.marking_database, f, indent=2)
    
    def batch_update_database(self, part_numbers: List[str]):
        """
        Batch update marking database for multiple part numbers
        
        Args:
            part_numbers: List of part numbers to update
        """
        logger.info(f"Starting batch update for {len(part_numbers)} part numbers")
        
        updated = 0
        failed = []
        
        for part_number in part_numbers:
            try:
                if part_number not in self.marking_database:
                    datasheet_url = self.search_oem_datasheet(part_number)
                    
                    if datasheet_url:
                        pdf_path = self.download_datasheet(datasheet_url, part_number)
                        if pdf_path:
                            marking_info = self.extract_marking_info(pdf_path)
                            self.marking_database[part_number] = marking_info
                            updated += 1
                            logger.info(f"Updated marking info for {part_number}")
                    else:
                        failed.append(part_number)
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Failed to update {part_number}: {e}")
                failed.append(part_number)
        
        # Save updated database
        self.save_marking_database()
        
        logger.info(f"Batch update complete. Updated: {updated}, Failed: {len(failed)}")
        if failed:
            logger.info(f"Failed part numbers: {failed}")
    
    def get_marking_info(self, part_number: str) -> Dict:
        """
        Get marking information for a part number
        
        Args:
            part_number: IC part number
            
        Returns:
            Marking information dictionary
        """
        # Check database first
        if part_number in self.marking_database:
            return self.marking_database[part_number]
        
        # Try to fetch from OEM
        datasheet_url = self.search_oem_datasheet(part_number)
        
        if datasheet_url:
            pdf_path = self.download_datasheet(datasheet_url, part_number)
            if pdf_path:
                marking_info = self.extract_marking_info(pdf_path)
                
                # Update database
                self.marking_database[part_number] = marking_info
                self.save_marking_database()
                
                return marking_info
        
        return {
            'marking_format': None,
            'status': 'Not found in OEM database'
        }


# Example usage
if __name__ == "__main__":
    # Initialize fetcher
    fetcher = OEMDataFetcher()
    
    # Test with common ICs
    test_parts = [
        'STM32F407VG',
        'LM358N',
        'NE555P',
        'ATmega328P',
        'ESP32-WROOM-32'
    ]
    
    print("Testing OEM Data Fetcher...")
    print("="*50)
    
    for part in test_parts:
        print(f"\nSearching for {part}...")
        
        # Search for datasheet
        url = fetcher.search_oem_datasheet(part)
        if url:
            print(f"  Found datasheet: {url}")
            
            # Get marking info
            info = fetcher.get_marking_info(part)
            print(f"  Marking info: {info.get('marking_format', 'Not extracted')}")
        else:
            print(f"  No datasheet found")
    
    print("\n" + "="*50)
    print("OEM Data Fetcher test complete!")
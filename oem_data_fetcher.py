#!/usr/bin/env python3
"""
OEM Data Fetcher - Enhanced Internet Search Module
Fetches datasheet URLs, specifications, and marking information from manufacturer websites
"""

import requests
import re
import time
import json
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class OEMSearchResult:
    """Data class for OEM search results"""
    part_number: str
    datasheet_url: Optional[str] = None
    manufacturer: Optional[str] = None
    description: Optional[str] = None
    specifications: Dict = None
    marking_info: Dict = None
    pdf_path: Optional[str] = None
    success: bool = False
    errors: List[str] = None
    processing_date: str = None
    
    def __post_init__(self):
        if self.specifications is None:
            self.specifications = {}
        if self.marking_info is None:
            self.marking_info = {}
        if self.errors is None:
            self.errors = []
        if self.processing_date is None:
            self.processing_date = time.strftime('%Y-%m-%d %H:%M:%S')

class OEMDataFetcher:
    """Enhanced OEM data fetcher with manufacturer-specific search strategies"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Manufacturer-specific search URLs and patterns
        self.manufacturer_configs = {
            'stmicroelectronics': {
                'search_url': 'https://www.st.com/en/products/microcontrollers-microprocessors.html',
                'datasheet_pattern': r'resource/en/datasheet/([^"]+\.pdf)',
                'name_patterns': ['STM', 'STMicroelectronics']
            },
            'microchip': {
                'search_url': 'https://www.microchip.com/en-us/products',
                'datasheet_pattern': r'downloads/en/DeviceDoc/([^"]+\.pdf)',
                'name_patterns': ['Microchip', 'ATMEL']
            },
            'texas_instruments': {
                'search_url': 'https://www.ti.com/products',
                'datasheet_pattern': r'lit/ds/symlink/([^"]+\.pdf)',
                'name_patterns': ['Texas Instruments', 'TI']
            },
            'espressif': {
                'search_url': 'https://www.espressif.com/en/products',
                'datasheet_pattern': r'documentation/([^"]+_datasheet_en\.pdf)',
                'name_patterns': ['Espressif']
            },
            'maxim': {
                'search_url': 'https://datasheets.maximintegrated.com',
                'datasheet_pattern': r'ds/([^"]+\.pdf)',
                'name_patterns': ['Maxim', 'Analog Devices']
            },
            'nxp': {
                'search_url': 'https://www.nxp.com/products',
                'datasheet_pattern': r'docs/en/data-sheet/([^"]+\.pdf)',
                'name_patterns': ['NXP', 'Philips']
            }
        }
        
        # Generic search engines for unknown manufacturers
        self.generic_search_urls = [
            'https://www.alldatasheet.com/datasheet-pdf/',
            'https://datasheetspdf.com/',
            'https://www.datasheet4u.com/'
        ]
    
    def fetch_oem_data(self, part_number: str, manufacturer: Optional[str] = None) -> OEMSearchResult:
        """
        Main method to fetch OEM data for a given part number
        """
        logger.info(f"Fetching OEM data for {part_number} (manufacturer: {manufacturer})")
        
        result = OEMSearchResult(part_number=part_number)
        
        try:
            # Try manufacturer-specific search first
            if manufacturer:
                result = self._search_manufacturer_specific(part_number, manufacturer, result)
            
            # If no success, try generic search
            if not result.success:
                result = self._search_generic(part_number, result)
            
            # Parse datasheet if found
            if result.datasheet_url and not result.success:
                self._parse_datasheet_page(result)
            
        except Exception as e:
            logger.error(f"Error fetching OEM data for {part_number}: {str(e)}")
            result.errors.append(f"General error: {str(e)}")
        
        return result
    
    def _search_manufacturer_specific(self, part_number: str, manufacturer: str, result: OEMSearchResult) -> OEMSearchResult:
        """Search using manufacturer-specific strategies"""
        
        # Normalize manufacturer name
        mfg_key = self._normalize_manufacturer_name(manufacturer.lower())
        
        if mfg_key not in self.manufacturer_configs:
            result.errors.append(f"No specific search strategy for manufacturer: {manufacturer}")
            return result
        
        config = self.manufacturer_configs[mfg_key]
        
        try:
            # Try direct URL construction (most common pattern)
            potential_urls = self._generate_potential_urls(part_number, mfg_key, config)
            
            for url in potential_urls:
                logger.info(f"Trying URL: {url}")
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    # Check if this looks like a datasheet page
                    if self._is_datasheet_page(response.text, part_number):
                        result.datasheet_url = url
                        result.manufacturer = manufacturer
                        result.success = True
                        self._extract_page_info(response.text, result)
                        break
                        
        except Exception as e:
            result.errors.append(f"Manufacturer-specific search error: {str(e)}")
        
        return result
    
    def _search_generic(self, part_number: str, result: OEMSearchResult) -> OEMSearchResult:
        """Search using generic datasheet websites"""
        
        for search_url in self.generic_search_urls:
            try:
                # Construct search URL
                search_query = f"{search_url}{part_number}"
                logger.info(f"Generic search: {search_query}")
                
                response = self.session.get(search_query, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for PDF links
                    pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.I))
                    
                    for link in pdf_links:
                        href = link.get('href')
                        if href and part_number.lower() in href.lower():
                            result.datasheet_url = urljoin(search_url, href)
                            result.success = True
                            break
                    
                    if result.success:
                        break
                        
            except Exception as e:
                result.errors.append(f"Generic search error for {search_url}: {str(e)}")
        
        return result
    
    def _generate_potential_urls(self, part_number: str, mfg_key: str, config: Dict) -> List[str]:
        """Generate potential URLs based on manufacturer patterns"""
        
        urls = []
        
        if mfg_key == 'stmicroelectronics':
            urls.extend([
                f"https://www.st.com/resource/en/datasheet/{part_number.lower()}.pdf",
                f"https://www.st.com/en/microcontrollers-microprocessors/{part_number.lower()}.html"
            ])
        
        elif mfg_key == 'microchip':
            urls.extend([
                f"https://ww1.microchip.com/downloads/en/DeviceDoc/{part_number}.pdf",
                f"https://www.microchip.com/en-us/product/{part_number}"
            ])
        
        elif mfg_key == 'texas_instruments':
            urls.extend([
                f"https://www.ti.com/lit/ds/symlink/{part_number.lower()}.pdf",
                f"https://www.ti.com/product/{part_number}"
            ])
        
        elif mfg_key == 'espressif':
            urls.extend([
                f"https://www.espressif.com/sites/default/files/documentation/{part_number.lower()}_datasheet_en.pdf"
            ])
        
        elif mfg_key == 'maxim':
            urls.extend([
                f"https://datasheets.maximintegrated.com/en/ds/{part_number}.pdf"
            ])
        
        elif mfg_key == 'nxp':
            urls.extend([
                f"https://www.nxp.com/docs/en/data-sheet/{part_number}.pdf"
            ])
        
        return urls
    
    def _normalize_manufacturer_name(self, manufacturer: str) -> str:
        """Normalize manufacturer name to match config keys"""
        
        name_mapping = {
            'st': 'stmicroelectronics',
            'stm': 'stmicroelectronics',
            'stmicroelectronics': 'stmicroelectronics',
            'microchip': 'microchip',
            'atmel': 'microchip',
            'ti': 'texas_instruments',
            'texas instruments': 'texas_instruments',
            'espressif': 'espressif',
            'maxim': 'maxim',
            'analog devices': 'maxim',
            'nxp': 'nxp',
            'philips': 'nxp'
        }
        
        return name_mapping.get(manufacturer.lower(), manufacturer.lower())
    
    def _is_datasheet_page(self, html: str, part_number: str) -> bool:
        """Check if the HTML content looks like a datasheet page"""
        
        # Look for common datasheet indicators
        indicators = [
            'datasheet', 'pdf', 'specification', 'technical reference',
            part_number.lower(), 'download', 'document'
        ]
        
        html_lower = html.lower()
        matches = sum(1 for indicator in indicators if indicator in html_lower)
        
        return matches >= 3
    
    def _extract_page_info(self, html: str, result: OEMSearchResult):
        """Extract additional information from the page"""
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract title/description
        title = soup.find('title')
        if title:
            result.description = title.text.strip()[:200]
        
        # Look for specifications in tables or divs
        specs = {}
        
        # Common specification patterns
        spec_patterns = {
            'operating_voltage': r'(?:operating|supply).{0,20}voltage.{0,20}([\d\.-]+).{0,10}(v|volt)',
            'temperature': r'(?:operating|ambient).{0,20}temperature.{0,20}([-\d\.-]+).{0,10}[°c]',
            'package': r'package.{0,20}([\w\d-]+)',
            'pins': r'(?:pin|pins).{0,20}(\d+)'
        }
        
        for key, pattern in spec_patterns.items():
            matches = re.search(pattern, html, re.I)
            if matches:
                specs[key] = matches.group(1)
        
        result.specifications = specs
    
    def _parse_datasheet_page(self, result: OEMSearchResult):
        """Parse the datasheet page to extract additional information"""
        
        if not result.datasheet_url:
            return
        
        try:
            response = self.session.get(result.datasheet_url, timeout=10)
            
            if response.status_code == 200:
                self._extract_page_info(response.text, result)
                result.success = True
                
        except Exception as e:
            result.errors.append(f"Error parsing datasheet page: {str(e)}")

def main():
    """Test function"""
    fetcher = OEMDataFetcher()
    
    # Test with some common ICs
    test_parts = [
        ('STM32F103C8T6', 'STMicroelectronics'),
        ('ATmega328P', 'Microchip'),
        ('LM555', 'Texas Instruments')
    ]
    
    for part_number, manufacturer in test_parts:
        print(f"\n=== Testing {part_number} ===")
        result = fetcher.fetch_oem_data(part_number, manufacturer)
        
        print(f"Success: {result.success}")
        print(f"Datasheet URL: {result.datasheet_url}")
        print(f"Description: {result.description}")
        print(f"Specifications: {result.specifications}")
        print(f"Errors: {result.errors}")

if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
Web Scraping Modules for IC Manufacturer Websites
This module provides specialized scrapers for different manufacturer websites
"""

import requests
from bs4 import BeautifulSoup
import time
import re
import json
import urllib.parse
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass
from urllib.robotparser import RobotFileParser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ICDataResult:
    """Data structure for scraped IC information"""
    part_number: str
    manufacturer: str
    description: str
    datasheet_url: Optional[str] = None
    specifications: Dict[str, Any] = None
    package_info: Dict[str, str] = None
    marking_info: Dict[str, List[str]] = None
    source_url: str = ""
    confidence_score: float = 0.0

class BaseICManufacturerScraper:
    """Base class for manufacturer-specific scrapers"""
    
    def __init__(self, manufacturer_name: str):
        self.manufacturer = manufacturer_name
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.rate_limit_delay = 1.0  # seconds between requests
        
    def check_robots_txt(self, url: str) -> bool:
        """Check if scraping is allowed by robots.txt"""
        try:
            base_url = f"{urllib.parse.urlparse(url).scheme}://{urllib.parse.urlparse(url).netloc}"
            robots_url = f"{base_url}/robots.txt"
            
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            
            return rp.can_fetch('*', url)
        except:
            return True  # Allow if can't determine
    
    def safe_request(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """Make a safe HTTP request with retries"""
        if not self.check_robots_txt(url):
            logger.warning(f"Robots.txt disallows scraping {url}")
            return None
            
        for attempt in range(max_retries):
            try:
                time.sleep(self.rate_limit_delay)
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    return None
                time.sleep(2 ** attempt)  # Exponential backoff
        return None
    
    def extract_ic_data(self, part_number: str) -> Optional[ICDataResult]:
        """Override this method in manufacturer-specific scrapers"""
        raise NotImplementedError
    
    def search_part(self, part_number: str) -> List[ICDataResult]:
        """Search for a part number and return results"""
        raise NotImplementedError

class TexasInstrumentsScraper(BaseICManufacturerScraper):
    """Texas Instruments specific scraper"""
    
    def __init__(self):
        super().__init__("Texas Instruments")
        self.base_url = "https://www.ti.com"
        self.search_url = "https://www.ti.com/sitesearch/en-us/docs/universalsearch.tsp"
    
    def search_part(self, part_number: str) -> List[ICDataResult]:
        """Search TI website for IC part number"""
        results = []
        
        try:
            # TI search API endpoint
            search_params = {
                'searchTerm': part_number,
                'nr': 10,  # Number of results
                'searchType': 'products'
            }
            
            response = self.safe_request(f"{self.search_url}?{urllib.parse.urlencode(search_params)}")
            if not response:
                return results
                
            # Parse search results (TI uses JSON API)
            try:
                data = response.json()
                if 'products' in data:
                    for product in data['products'][:5]:  # Limit to top 5
                        ic_data = self._parse_ti_product(product)
                        if ic_data:
                            results.append(ic_data)
            except:
                # Fallback to HTML parsing
                soup = BeautifulSoup(response.text, 'html.parser')
                results.extend(self._parse_ti_html(soup, part_number))
                
        except Exception as e:
            logger.error(f"TI search failed for {part_number}: {e}")
        
        return results
    
    def _parse_ti_product(self, product: Dict) -> Optional[ICDataResult]:
        """Parse TI product data from API response"""
        try:
            return ICDataResult(
                part_number=product.get('partNumber', ''),
                manufacturer="Texas Instruments",
                description=product.get('description', ''),
                datasheet_url=product.get('datasheetUrl'),
                specifications={
                    'package': product.get('package'),
                    'pins': product.get('pinCount'),
                    'voltage': product.get('supplyVoltage'),
                    'temperature': product.get('operatingTemp')
                },
                source_url=product.get('productUrl', ''),
                confidence_score=0.9
            )
        except Exception as e:
            logger.error(f"Failed to parse TI product: {e}")
            return None
    
    def _parse_ti_html(self, soup: BeautifulSoup, part_number: str) -> List[ICDataResult]:
        """Parse TI HTML search results"""
        results = []
        
        # Look for product cards or links
        product_links = soup.find_all('a', href=re.compile(r'/product/'))
        
        for link in product_links[:3]:  # Top 3 results
            try:
                product_url = self.base_url + link.get('href')
                ic_data = self._scrape_ti_product_page(product_url, part_number)
                if ic_data:
                    results.append(ic_data)
            except Exception as e:
                logger.error(f"Failed to parse TI product link: {e}")
        
        return results
    
    def _scrape_ti_product_page(self, url: str, part_number: str) -> Optional[ICDataResult]:
        """Scrape individual TI product page"""
        response = self.safe_request(url)
        if not response:
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        try:
            # Extract product information
            title = soup.find('h1', class_='pdp-product-title')
            description = soup.find('div', class_='pdp-product-description')
            
            # Look for datasheet link
            datasheet_link = soup.find('a', href=re.compile(r'\.pdf$', re.I))
            
            # Extract specifications
            specs = {}
            spec_table = soup.find('table', class_='pdp-specs-table')
            if spec_table:
                for row in spec_table.find_all('tr'):
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        specs[key.lower().replace(' ', '_')] = value
            
            return ICDataResult(
                part_number=part_number,
                manufacturer="Texas Instruments",
                description=description.get_text(strip=True) if description else "",
                datasheet_url=datasheet_link.get('href') if datasheet_link else None,
                specifications=specs,
                source_url=url,
                confidence_score=0.8
            )
            
        except Exception as e:
            logger.error(f"Failed to scrape TI product page {url}: {e}")
            return None

class AnalogDevicesScraper(BaseICManufacturerScraper):
    """Analog Devices specific scraper"""
    
    def __init__(self):
        super().__init__("Analog Devices")
        self.base_url = "https://www.analog.com"
        self.search_url = "https://www.analog.com/en/search.html"
    
    def search_part(self, part_number: str) -> List[ICDataResult]:
        """Search Analog Devices website"""
        results = []
        
        try:
            search_params = {'q': part_number}
            response = self.safe_request(f"{self.search_url}?{urllib.parse.urlencode(search_params)}")
            
            if response:
                soup = BeautifulSoup(response.text, 'html.parser')
                results.extend(self._parse_adi_results(soup, part_number))
        
        except Exception as e:
            logger.error(f"ADI search failed for {part_number}: {e}")
        
        return results
    
    def _parse_adi_results(self, soup: BeautifulSoup, part_number: str) -> List[ICDataResult]:
        """Parse Analog Devices search results"""
        results = []
        
        # Look for product result divs
        product_cards = soup.find_all('div', class_='product-card')
        
        for card in product_cards[:3]:
            try:
                title_elem = card.find('h3') or card.find('a')
                description_elem = card.find('p', class_='description')
                link_elem = card.find('a', href=True)
                
                if title_elem:
                    results.append(ICDataResult(
                        part_number=part_number,
                        manufacturer="Analog Devices",
                        description=description_elem.get_text(strip=True) if description_elem else "",
                        source_url=f"{self.base_url}{link_elem.get('href')}" if link_elem else "",
                        confidence_score=0.7
                    ))
            except Exception as e:
                logger.error(f"Failed to parse ADI product card: {e}")
        
        return results

class MicrochipScraper(BaseICManufacturerScraper):
    """Microchip Technology specific scraper"""
    
    def __init__(self):
        super().__init__("Microchip")
        self.base_url = "https://www.microchip.com"
        self.search_url = "https://www.microchip.com/en-us/search"
    
    def search_part(self, part_number: str) -> List[ICDataResult]:
        """Search Microchip website"""
        results = []
        
        try:
            search_params = {'searchString': part_number}
            response = self.safe_request(f"{self.search_url}?{urllib.parse.urlencode(search_params)}")
            
            if response:
                soup = BeautifulSoup(response.text, 'html.parser')
                results.extend(self._parse_microchip_results(soup, part_number))
        
        except Exception as e:
            logger.error(f"Microchip search failed for {part_number}: {e}")
        
        return results
    
    def _parse_microchip_results(self, soup: BeautifulSoup, part_number: str) -> List[ICDataResult]:
        """Parse Microchip search results"""
        results = []
        
        # Look for search result items
        search_items = soup.find_all('div', class_='search-result-item')
        
        for item in search_items[:3]:
            try:
                title_elem = item.find('h3') or item.find('a')
                description_elem = item.find('div', class_='description')
                datasheet_link = item.find('a', href=re.compile(r'datasheet|pdf', re.I))
                
                if title_elem:
                    results.append(ICDataResult(
                        part_number=part_number,
                        manufacturer="Microchip",
                        description=description_elem.get_text(strip=True) if description_elem else "",
                        datasheet_url=datasheet_link.get('href') if datasheet_link else None,
                        source_url=item.find('a', href=True).get('href') if item.find('a', href=True) else "",
                        confidence_score=0.7
                    ))
            except Exception as e:
                logger.error(f"Failed to parse Microchip search item: {e}")
        
        return results

class GenericDatasheetScraper(BaseICManufacturerScraper):
    """Generic scraper for datasheet repository websites"""
    
    def __init__(self):
        super().__init__("Generic")
        self.datasheet_sites = [
            "https://www.alldatasheet.com",
            "https://pdf.datasheetarchive.com",
            "https://www.datasheetq.com",
            "https://components101.com"
        ]
    
    def search_part(self, part_number: str) -> List[ICDataResult]:
        """Search multiple datasheet repositories"""
        all_results = []
        
        for site in self.datasheet_sites:
            try:
                results = self._search_datasheet_site(site, part_number)
                all_results.extend(results)
                
                if len(all_results) >= 5:  # Limit total results
                    break
                    
            except Exception as e:
                logger.error(f"Failed to search {site} for {part_number}: {e}")
        
        return all_results[:5]  # Return top 5 results
    
    def _search_datasheet_site(self, base_url: str, part_number: str) -> List[ICDataResult]:
        """Search a specific datasheet repository"""
        results = []
        
        try:
            # Try common search patterns
            search_patterns = [
                f"{base_url}/search.php?skey={part_number}",
                f"{base_url}/{part_number}",
                f"{base_url}/search/{part_number}",
                f"{base_url}/?q={part_number}"
            ]
            
            for search_url in search_patterns:
                response = self.safe_request(search_url)
                if response and response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    site_results = self._parse_datasheet_results(soup, part_number, base_url)
                    if site_results:
                        results.extend(site_results)
                        break  # Found results, no need to try other patterns
                        
        except Exception as e:
            logger.error(f"Failed to search datasheet site {base_url}: {e}")
        
        return results
    
    def _parse_datasheet_results(self, soup: BeautifulSoup, part_number: str, base_url: str) -> List[ICDataResult]:
        """Parse generic datasheet search results"""
        results = []
        
        # Look for PDF links and product information
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.I))
        
        for link in pdf_links[:2]:  # Top 2 PDFs per site
            try:
                pdf_url = link.get('href')
                if not pdf_url.startswith('http'):
                    pdf_url = urllib.parse.urljoin(base_url, pdf_url)
                
                # Try to extract description from surrounding text
                description = ""
                parent = link.parent
                if parent:
                    description = parent.get_text(strip=True)[:200]
                
                results.append(ICDataResult(
                    part_number=part_number,
                    manufacturer="Unknown",
                    description=description,
                    datasheet_url=pdf_url,
                    source_url=base_url,
                    confidence_score=0.6
                ))
                
            except Exception as e:
                logger.error(f"Failed to parse datasheet link: {e}")
        
        return results

class WebScrapingManager:
    """Main manager class for coordinating all scrapers"""
    
    def __init__(self):
        self.scrapers = {
            'texas_instruments': TexasInstrumentsScraper(),
            'analog_devices': AnalogDevicesScraper(),
            'microchip': MicrochipScraper(),
            'generic': GenericDatasheetScraper()
        }
        self.cache = {}  # Simple in-memory cache
    
    def search_all_sources(self, part_number: str, max_results: int = 10) -> List[ICDataResult]:
        """Search all available sources for IC information"""
        # Check cache first
        cache_key = f"search_{part_number.lower()}"
        if cache_key in self.cache:
            logger.info(f"Returning cached results for {part_number}")
            return self.cache[cache_key]
        
        all_results = []
        
        for scraper_name, scraper in self.scrapers.items():
            try:
                logger.info(f"Searching {scraper_name} for {part_number}")
                results = scraper.search_part(part_number)
                
                # Tag results with scraper name
                for result in results:
                    result.manufacturer = result.manufacturer or scraper_name
                
                all_results.extend(results)
                
            except Exception as e:
                logger.error(f"Scraper {scraper_name} failed: {e}")
        
        # Sort by confidence score and limit results
        all_results.sort(key=lambda x: x.confidence_score, reverse=True)
        final_results = all_results[:max_results]
        
        # Cache results
        self.cache[cache_key] = final_results
        
        logger.info(f"Found {len(final_results)} results for {part_number}")
        return final_results
    
    def get_manufacturer_specific_data(self, part_number: str, manufacturer: str) -> List[ICDataResult]:
        """Get data from a specific manufacturer's website"""
        manufacturer_key = manufacturer.lower().replace(' ', '_')
        
        if manufacturer_key in self.scrapers:
            try:
                return self.scrapers[manufacturer_key].search_part(part_number)
            except Exception as e:
                logger.error(f"Failed to get data from {manufacturer}: {e}")
        
        return []
    
    def extract_marking_patterns(self, results: List[ICDataResult]) -> Dict[str, List[str]]:
        """Extract marking patterns from scraping results"""
        patterns = {
            'standard_markings': [],
            'package_markings': [],
            'date_codes': [],
            'lot_codes': []
        }
        
        for result in results:
            # Extract patterns from description and specifications
            text = f"{result.description} {json.dumps(result.specifications or {})}"
            
            # Look for common marking patterns
            if re.search(r'\b[A-Z]{2,4}\d{2,4}[A-Z]?\b', text):
                patterns['standard_markings'].extend(re.findall(r'\b[A-Z]{2,4}\d{2,4}[A-Z]?\b', text))
            
            # Date code patterns
            date_patterns = re.findall(r'\b\d{4}W?\d{2}\b|\b\d{2}W\d{2}\b', text)
            patterns['date_codes'].extend(date_patterns)
            
            # Package information
            if result.specifications:
                package_info = result.specifications.get('package', '')
                if package_info:
                    patterns['package_markings'].append(package_info)
        
        # Remove duplicates
        for key in patterns:
            patterns[key] = list(set(patterns[key]))
        
        return patterns

# Example usage and testing
if __name__ == "__main__":
    manager = WebScrapingManager()
    
    # Test with common IC part numbers
    test_parts = ["LM555", "NE555", "LM358", "CD4017"]
    
    for part in test_parts:
        print(f"\n=== Searching for {part} ===")
        results = manager.search_all_sources(part, max_results=3)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.manufacturer} - {result.part_number}")
            print(f"   Description: {result.description[:100]}...")
            print(f"   Datasheet: {result.datasheet_url}")
            print(f"   Confidence: {result.confidence_score}")
        
        # Extract marking patterns
        patterns = manager.extract_marking_patterns(results)
        if any(patterns.values()):
            print(f"\nMarking Patterns Found:")
            for pattern_type, pattern_list in patterns.items():
                if pattern_list:
                    print(f"   {pattern_type}: {pattern_list}")
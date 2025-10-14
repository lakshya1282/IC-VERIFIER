#!/usr/bin/env python3
"""
Unified Internet Search Service for IC Data Enrichment
Combines web scraping and intelligent search for comprehensive IC information gathering
"""

import os
import sys
import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import requests
from dataclasses import dataclass, asdict

# Add the backend services to path for imports
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'services')
sys.path.append(backend_path)

try:
    from web_scrapers import WebScrapingManager, ICDataResult
    from intelligent_search import IntelligentICSearch, ICDocument
    WEB_SCRAPERS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Web scrapers not available: {e}")
    WEB_SCRAPERS_AVAILABLE = False
    # Create mock classes
    @dataclass
    class ICDataResult:
        part_number: str = ""
        manufacturer: str = ""
        description: str = ""
        datasheet_url: Optional[str] = None
        confidence_score: float = 0.0
        source_url: str = ""
    
    @dataclass  
    class ICDocument:
        title: str = ""
        url: str = ""
        pdf_url: Optional[str] = None
        source: str = ""
        confidence_score: float = 0.0

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ICEnrichmentResult:
    """Comprehensive IC data enrichment result"""
    part_number: str
    search_timestamp: str
    manufacturer_info: Dict[str, Any]
    datasheet_info: Dict[str, Any]
    web_scraping_results: List[Dict[str, Any]]
    intelligent_search_results: List[Dict[str, Any]]
    consolidated_data: Dict[str, Any]
    confidence_score: float
    processing_time: float
    sources_used: List[str]

class UnifiedICSearchService:
    """Unified service combining web scraping and intelligent search for IC data enrichment"""
    
    def __init__(self, cache_dir: str = "./search_cache", max_workers: int = 4):
        self.cache_dir = cache_dir
        self.max_workers = max_workers
        os.makedirs(cache_dir, exist_ok=True)
        
        # Initialize search services
        self.web_scraper = None
        self.intelligent_searcher = None
        
        if WEB_SCRAPERS_AVAILABLE:
            try:
                self.web_scraper = WebScrapingManager()
                self.intelligent_searcher = IntelligentICSearch()
                logger.info("✅ Web scrapers initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize web scrapers: {e}")
                WEB_SCRAPERS_AVAILABLE = False
        
        # Cache for recent searches
        self.search_cache = {}
        self.cache_expiry_hours = 24
        
        # Known IC manufacturers and their patterns
        self.manufacturer_patterns = {
            'texas_instruments': ['TI', 'LM', 'TL', 'SN', 'TMS', 'MSP'],
            'stmicroelectronics': ['STM32', 'STM8', 'L6', 'L298', 'VN'],
            'microchip': ['PIC', 'dsPIC', 'ATmega', 'ATtiny', 'MCP'],
            'analog_devices': ['AD', 'ADuM', 'ADP', 'ADG', 'LT'],
            'maxim': ['MAX', 'DS', 'LTC'],
            'infineon': ['IRF', 'TLE', 'IFX', 'BSS'],
            'nxp': ['LPC', 'i.MX', 'TDA', 'TEA'],
            'intel': ['i386', 'i486', 'Pentium', '8051'],
            'xilinx': ['XC', 'Spartan', 'Virtex', 'Zynq'],
            'cypress': ['CY', 'PSoC', 'FM'],
            'espressif': ['ESP32', 'ESP8266'],
            'nordic': ['nRF'],
            'silabs': ['Si', 'EFM32'],
            'renesas': ['R7S', 'RX', 'RL78']
        }
    
    def identify_manufacturer(self, part_number: str) -> str:
        """Identify the manufacturer from part number patterns"""
        part_upper = part_number.upper().strip()
        
        for manufacturer, patterns in self.manufacturer_patterns.items():
            for pattern in patterns:
                if pattern.upper() in part_upper:
                    return manufacturer.replace('_', ' ').title()
        
        return "Unknown"
    
    def get_cache_key(self, part_number: str) -> str:
        """Generate cache key for part number"""
        return f"ic_search_{part_number.lower().strip().replace(' ', '_')}"
    
    def is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is still valid"""
        try:
            cache_time = datetime.fromisoformat(cache_entry['timestamp'])
            hours_elapsed = (datetime.now() - cache_time).total_seconds() / 3600
            return hours_elapsed < self.cache_expiry_hours
        except:
            return False
    
    def load_from_cache(self, part_number: str) -> Optional[ICEnrichmentResult]:
        """Load search results from cache"""
        cache_key = self.get_cache_key(part_number)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                
                if self.is_cache_valid(cached_data):
                    logger.info(f"📦 Using cached results for {part_number}")
                    return ICEnrichmentResult(**cached_data['result'])
        except Exception as e:
            logger.error(f"Error loading cache for {part_number}: {e}")
        
        return None
    
    def save_to_cache(self, part_number: str, result: ICEnrichmentResult):
        """Save search results to cache"""
        cache_key = self.get_cache_key(part_number)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'part_number': part_number,
                'result': asdict(result)
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
            logger.info(f"💾 Cached results for {part_number}")
        except Exception as e:
            logger.error(f"Error saving cache for {part_number}: {e}")
    
    def search_with_web_scrapers(self, part_number: str) -> List[Dict[str, Any]]:
        """Search using web scrapers"""
        results = []
        
        if not WEB_SCRAPERS_AVAILABLE or not self.web_scraper:
            logger.warning("Web scrapers not available")
            return results
        
        try:
            logger.info(f"🌐 Searching web sources for {part_number}")
            scraper_results = self.web_scraper.search_all_sources(part_number, max_results=5)
            
            for result in scraper_results:
                results.append({
                    'source': 'web_scraper',
                    'part_number': result.part_number,
                    'manufacturer': result.manufacturer,
                    'description': result.description,
                    'datasheet_url': result.datasheet_url,
                    'specifications': result.specifications,
                    'package_info': result.package_info,
                    'confidence_score': result.confidence_score,
                    'source_url': result.source_url
                })
            
            logger.info(f"✅ Found {len(results)} web scraper results for {part_number}")
            
        except Exception as e:
            logger.error(f"Error in web scraper search for {part_number}: {e}")
        
        return results
    
    def search_with_intelligent_search(self, part_number: str) -> List[Dict[str, Any]]:
        """Search using intelligent search"""
        results = []
        
        if not WEB_SCRAPERS_AVAILABLE or not self.intelligent_searcher:
            logger.warning("Intelligent search not available")
            return results
        
        try:
            logger.info(f"🧠 Intelligent search for {part_number}")
            search_results = self.intelligent_searcher.search_ic_documentation(part_number, max_results=5)
            
            for doc in search_results:
                # Download and extract if it's a PDF
                extracted_data = None
                if doc.pdf_url:
                    try:
                        downloaded_path = self.intelligent_searcher.download_document(doc)
                        if downloaded_path:
                            extracted_data = self.intelligent_searcher.extract_ic_marking_info(
                                downloaded_path, part_number
                            )
                    except Exception as e:
                        logger.warning(f"Could not process PDF for {part_number}: {e}")
                
                results.append({
                    'source': 'intelligent_search',
                    'title': doc.title,
                    'url': doc.url,
                    'pdf_url': doc.pdf_url,
                    'manufacturer': doc.manufacturer,
                    'confidence_score': doc.confidence_score,
                    'extracted_data': extracted_data
                })
            
            logger.info(f"✅ Found {len(results)} intelligent search results for {part_number}")
            
        except Exception as e:
            logger.error(f"Error in intelligent search for {part_number}: {e}")
        
        return results
    
    def search_manufacturer_specific(self, part_number: str, manufacturer: str) -> Dict[str, Any]:
        """Search manufacturer-specific databases"""
        manufacturer_data = {
            'manufacturer': manufacturer,
            'official_info': {},
            'datasheet_links': [],
            'specifications': {}
        }
        
        try:
            # Try to get manufacturer-specific data
            if WEB_SCRAPERS_AVAILABLE and self.web_scraper:
                specific_results = self.web_scraper.get_manufacturer_specific_data(
                    part_number, manufacturer
                )
                
                if specific_results:
                    manufacturer_data['official_info'] = {
                        'found_results': len(specific_results),
                        'highest_confidence': max([r.confidence_score for r in specific_results], default=0),
                        'sources': [r.source_url for r in specific_results if r.source_url]
                    }
                    
                    # Collect datasheet links
                    manufacturer_data['datasheet_links'] = [
                        r.datasheet_url for r in specific_results 
                        if r.datasheet_url
                    ]
                    
                    # Collect specifications
                    for result in specific_results:
                        if result.specifications:
                            manufacturer_data['specifications'].update(result.specifications)
            
        except Exception as e:
            logger.error(f"Error in manufacturer-specific search: {e}")
        
        return manufacturer_data
    
    def consolidate_search_results(self, part_number: str, 
                                 web_results: List[Dict], 
                                 intelligent_results: List[Dict],
                                 manufacturer_data: Dict) -> Dict[str, Any]:
        """Consolidate all search results into unified data"""
        consolidated = {
            'part_number': part_number,
            'manufacturer': self.identify_manufacturer(part_number),
            'descriptions': [],
            'datasheets': [],
            'specifications': {},
            'package_types': [],
            'marking_patterns': [],
            'sources': [],
            'confidence_scores': []
        }
        
        # Process web scraper results
        for result in web_results:
            if result.get('description'):
                consolidated['descriptions'].append(result['description'])
            if result.get('datasheet_url'):
                consolidated['datasheets'].append(result['datasheet_url'])
            if result.get('specifications'):
                consolidated['specifications'].update(result['specifications'])
            if result.get('source_url'):
                consolidated['sources'].append(result['source_url'])
            if result.get('confidence_score'):
                consolidated['confidence_scores'].append(result['confidence_score'])
        
        # Process intelligent search results
        for result in intelligent_results:
            if result.get('pdf_url'):
                consolidated['datasheets'].append(result['pdf_url'])
            if result.get('url'):
                consolidated['sources'].append(result['url'])
            if result.get('confidence_score'):
                consolidated['confidence_scores'].append(result['confidence_score'])
            
            # Process extracted data if available
            if result.get('extracted_data') and result['extracted_data'].get('marking_info'):
                marking_info = result['extracted_data']['marking_info']
                if marking_info.get('package_types'):
                    consolidated['package_types'].extend(marking_info['package_types'])
                if marking_info.get('marking_codes'):
                    consolidated['marking_patterns'].extend(marking_info['marking_codes'])
        
        # Process manufacturer data
        if manufacturer_data.get('datasheet_links'):
            consolidated['datasheets'].extend(manufacturer_data['datasheet_links'])
        if manufacturer_data.get('specifications'):
            consolidated['specifications'].update(manufacturer_data['specifications'])
        
        # Remove duplicates and clean up
        consolidated['descriptions'] = list(set(consolidated['descriptions']))
        consolidated['datasheets'] = list(set(consolidated['datasheets']))
        consolidated['package_types'] = list(set(consolidated['package_types']))
        consolidated['marking_patterns'] = list(set(consolidated['marking_patterns']))
        consolidated['sources'] = list(set(consolidated['sources']))
        
        # Calculate overall confidence
        if consolidated['confidence_scores']:
            consolidated['overall_confidence'] = sum(consolidated['confidence_scores']) / len(consolidated['confidence_scores'])
        else:
            consolidated['overall_confidence'] = 0.0
        
        return consolidated
    
    def enrich_ic_data(self, part_number: str, use_cache: bool = True) -> ICEnrichmentResult:
        """Main method to enrich IC data using all available sources"""
        start_time = time.time()
        
        # Check cache first
        if use_cache:
            cached_result = self.load_from_cache(part_number)
            if cached_result:
                return cached_result
        
        logger.info(f"🚀 Starting IC data enrichment for: {part_number}")
        
        # Initialize result containers
        web_results = []
        intelligent_results = []
        manufacturer_data = {}
        sources_used = []
        
        # Identify manufacturer
        manufacturer = self.identify_manufacturer(part_number)
        
        # Search with different services in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit search tasks
            futures = {}
            
            # Web scraper search
            if WEB_SCRAPERS_AVAILABLE and self.web_scraper:
                futures['web_scraper'] = executor.submit(self.search_with_web_scrapers, part_number)
                sources_used.append('web_scraper')
            
            # Intelligent search
            if WEB_SCRAPERS_AVAILABLE and self.intelligent_searcher:
                futures['intelligent_search'] = executor.submit(self.search_with_intelligent_search, part_number)
                sources_used.append('intelligent_search')
            
            # Manufacturer-specific search
            if manufacturer != "Unknown" and WEB_SCRAPERS_AVAILABLE:
                futures['manufacturer_specific'] = executor.submit(self.search_manufacturer_specific, part_number, manufacturer)
                sources_used.append('manufacturer_specific')
            
            # Collect results
            for future_name, future in futures.items():
                try:
                    result = future.result(timeout=30)  # 30 second timeout per search
                    
                    if future_name == 'web_scraper':
                        web_results = result
                    elif future_name == 'intelligent_search':
                        intelligent_results = result
                    elif future_name == 'manufacturer_specific':
                        manufacturer_data = result
                        
                    logger.info(f"✅ {future_name} completed for {part_number}")
                    
                except Exception as e:
                    logger.error(f"❌ {future_name} failed for {part_number}: {e}")
        
        # Consolidate all results
        consolidated_data = self.consolidate_search_results(
            part_number, web_results, intelligent_results, manufacturer_data
        )
        
        processing_time = time.time() - start_time
        
        # Create enrichment result
        enrichment_result = ICEnrichmentResult(
            part_number=part_number,
            search_timestamp=datetime.now().isoformat(),
            manufacturer_info={'identified_manufacturer': manufacturer},
            datasheet_info={'found_datasheets': len(consolidated_data['datasheets'])},
            web_scraping_results=web_results,
            intelligent_search_results=intelligent_results,
            consolidated_data=consolidated_data,
            confidence_score=consolidated_data['overall_confidence'],
            processing_time=processing_time,
            sources_used=sources_used
        )
        
        # Save to cache
        if use_cache:
            self.save_to_cache(part_number, enrichment_result)
        
        logger.info(f"✅ IC data enrichment completed for {part_number} in {processing_time:.2f}s")
        logger.info(f"📊 Found {len(consolidated_data['datasheets'])} datasheets, {len(consolidated_data['sources'])} sources")
        
        return enrichment_result
    
    def batch_enrich_ic_data(self, part_numbers: List[str], use_cache: bool = True) -> List[ICEnrichmentResult]:
        """Batch enrich multiple IC part numbers"""
        logger.info(f"🚀 Starting batch enrichment for {len(part_numbers)} parts")
        
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all enrichment tasks
            future_to_part = {
                executor.submit(self.enrich_ic_data, part, use_cache): part 
                for part in part_numbers
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_part):
                part_number = future_to_part[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.info(f"✅ Completed enrichment for {part_number}")
                except Exception as e:
                    logger.error(f"❌ Failed enrichment for {part_number}: {e}")
                    # Add error result
                    error_result = ICEnrichmentResult(
                        part_number=part_number,
                        search_timestamp=datetime.now().isoformat(),
                        manufacturer_info={'error': str(e)},
                        datasheet_info={},
                        web_scraping_results=[],
                        intelligent_search_results=[],
                        consolidated_data={'error': str(e)},
                        confidence_score=0.0,
                        processing_time=0.0,
                        sources_used=[]
                    )
                    results.append(error_result)
        
        logger.info(f"✅ Batch enrichment completed: {len(results)} results")
        return results
    
    def get_enrichment_summary(self, results: List[ICEnrichmentResult]) -> Dict[str, Any]:
        """Generate summary of enrichment results"""
        if not results:
            return {'error': 'No results to summarize'}
        
        summary = {
            'total_parts_processed': len(results),
            'successful_enrichments': len([r for r in results if r.confidence_score > 0]),
            'average_confidence': sum([r.confidence_score for r in results]) / len(results),
            'total_datasheets_found': sum([len(r.consolidated_data.get('datasheets', [])) for r in results]),
            'total_sources_used': len(set([source for r in results for source in r.sources_used])),
            'average_processing_time': sum([r.processing_time for r in results]) / len(results),
            'manufacturers_identified': list(set([
                r.consolidated_data.get('manufacturer', 'Unknown') for r in results
            ])),
            'timestamp': datetime.now().isoformat()
        }
        
        return summary

# Example usage and testing
if __name__ == "__main__":
    search_service = UnifiedICSearchService()
    
    # Test with common IC part numbers
    test_parts = ["STM32F103C8T6", "LM555", "ATmega328P", "ESP32"]
    
    print("🧪 Testing Unified IC Search Service")
    print("=" * 50)
    
    for part in test_parts:
        print(f"\n🔍 Testing: {part}")
        result = search_service.enrich_ic_data(part)
        
        print(f"✅ Status: Success" if result.confidence_score > 0 else f"❌ Status: Failed")
        print(f"📊 Confidence: {result.confidence_score:.2f}")
        print(f"⏱️  Processing Time: {result.processing_time:.2f}s")
        print(f"📚 Datasheets Found: {len(result.consolidated_data.get('datasheets', []))}")
        print(f"🌐 Sources Used: {', '.join(result.sources_used)}")
    
    # Test batch processing
    print(f"\n🚀 Testing batch processing...")
    batch_results = search_service.batch_enrich_ic_data(test_parts[:2])
    summary = search_service.get_enrichment_summary(batch_results)
    
    print(f"📋 Batch Summary:")
    for key, value in summary.items():
        if key != 'timestamp':
            print(f"   • {key.replace('_', ' ').title()}: {value}")
"""
Intelligent Internet Search System for IC Documentation
This module searches the internet for IC datasheets, downloads them, and extracts marking information.
"""

import requests
import json
import os
import re
import time
from urllib.parse import quote, urljoin, urlparse
import PyPDF2
import fitz  # PyMuPDF
from bs4 import BeautifulSoup
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ICDocument:
    """Data class for IC document information"""
    title: str
    url: str
    pdf_url: Optional[str]
    source: str
    manufacturer: str
    ic_model: str
    confidence_score: float
    extracted_text: Optional[str] = None
    marking_info: Optional[Dict] = None

class IntelligentICSearch:
    """Intelligent search system for IC documentation and datasheets"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Known IC manufacturer websites and search patterns
        self.manufacturer_sites = {
            'ti': {
                'base_url': 'https://www.ti.com',
                'search_url': 'https://www.ti.com/lit/search/',
                'patterns': [r'TI', r'Texas\s+Instruments']
            },
            'stmicroelectronics': {
                'base_url': 'https://www.st.com',
                'search_url': 'https://www.st.com/en/search.html',
                'patterns': [r'STM32', r'STM', r'ST\w+']
            },
            'microchip': {
                'base_url': 'https://www.microchip.com',
                'search_url': 'https://www.microchip.com/en-us/search',
                'patterns': [r'PIC\d+', r'ATmega', r'ATMEL']
            },
            'infineon': {
                'base_url': 'https://www.infineon.com',
                'search_url': 'https://www.infineon.com/cms/en/search/',
                'patterns': [r'IRF\d+', r'TLE\d+']
            },
            'analog': {
                'base_url': 'https://www.analog.com',
                'search_url': 'https://www.analog.com/en/search.html',
                'patterns': [r'AD\d+', r'LT\d+', r'ADP\d+']
            },
            'nxp': {
                'base_url': 'https://www.nxp.com',
                'search_url': 'https://www.nxp.com/search',
                'patterns': [r'LPC\d+', r'i\.MX', r'NXP']
            }
        }
        
        # File storage settings
        self.download_dir = os.path.join(os.getcwd(), 'downloaded_docs')
        self.cache_dir = os.path.join(os.getcwd(), 'search_cache')
        os.makedirs(self.download_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)

    def search_ic_documentation(self, ic_part_number: str, max_results: int = 10) -> List[ICDocument]:
        """
        Search for IC documentation across multiple sources
        """
        logger.info(f"🔍 Searching for IC documentation: {ic_part_number}")
        
        results = []
        
        # 1. Search general technical databases
        results.extend(self._search_general_databases(ic_part_number, max_results//2))
        
        # 2. Search manufacturer-specific sites
        results.extend(self._search_manufacturer_sites(ic_part_number, max_results//2))
        
        # 3. Search academic and technical repositories
        results.extend(self._search_technical_repositories(ic_part_number, max_results//4))
        
        # Remove duplicates and sort by confidence
        unique_results = self._deduplicate_results(results)
        return sorted(unique_results, key=lambda x: x.confidence_score, reverse=True)[:max_results]

    def _search_general_databases(self, ic_part_number: str, max_results: int) -> List[ICDocument]:
        """Search general technical databases and repositories"""
        results = []
        
        search_engines = [
            {
                'name': 'Google Scholar',
                'url': f'https://scholar.google.com/scholar?q="{ic_part_number}"+datasheet+filetype:pdf',
                'parser': self._parse_google_scholar_results
            },
            {
                'name': 'IEEE Xplore',
                'url': f'https://ieeexplore.ieee.org/search/searchresult.jsp?queryText={quote(ic_part_number)}',
                'parser': self._parse_ieee_results
            },
            {
                'name': 'ResearchGate',
                'url': f'https://www.researchgate.net/search?q={quote(ic_part_number)}',
                'parser': self._parse_researchgate_results
            }
        ]
        
        for engine in search_engines:
            try:
                engine_results = self._perform_search(engine, ic_part_number, max_results//len(search_engines))
                results.extend(engine_results)
            except Exception as e:
                logger.error(f"Error searching {engine['name']}: {e}")
        
        return results

    def _search_manufacturer_sites(self, ic_part_number: str, max_results: int) -> List[ICDocument]:
        """Search manufacturer-specific websites"""
        results = []
        
        # Determine likely manufacturer based on IC part number patterns
        likely_manufacturers = self._identify_manufacturer(ic_part_number)
        
        for manufacturer in likely_manufacturers:
            if manufacturer in self.manufacturer_sites:
                try:
                    manufacturer_results = self._search_manufacturer_site(
                        manufacturer, ic_part_number, max_results//len(likely_manufacturers)
                    )
                    results.extend(manufacturer_results)
                except Exception as e:
                    logger.error(f"Error searching {manufacturer}: {e}")
        
        return results

    def _search_technical_repositories(self, ic_part_number: str, max_results: int) -> List[ICDocument]:
        """Search technical repositories and databases"""
        results = []
        
        repositories = [
            {
                'name': 'Datasheet Archive',
                'url': f'https://www.datasheetarchive.com/search.php?q={quote(ic_part_number)}',
                'parser': self._parse_datasheet_archive
            },
            {
                'name': 'AllDataSheet',
                'url': f'https://www.alldatasheet.com/datasheet-pdf/pdf-search.jsp?sSearchword={quote(ic_part_number)}',
                'parser': self._parse_alldatasheet
            },
            {
                'name': 'DatasheetsPDF',
                'url': f'https://www.datasheetspdf.com/search/{quote(ic_part_number)}',
                'parser': self._parse_datasheetspdf
            }
        ]
        
        for repo in repositories:
            try:
                repo_results = self._perform_search(repo, ic_part_number, max_results//len(repositories))
                results.extend(repo_results)
            except Exception as e:
                logger.error(f"Error searching {repo['name']}: {e}")
        
        return results

    def _identify_manufacturer(self, ic_part_number: str) -> List[str]:
        """Identify likely manufacturer based on IC part number patterns"""
        manufacturers = []
        
        for mfg, info in self.manufacturer_sites.items():
            for pattern in info['patterns']:
                if re.search(pattern, ic_part_number, re.IGNORECASE):
                    manufacturers.append(mfg)
                    break
        
        # If no specific match, return all manufacturers for broad search
        if not manufacturers:
            manufacturers = list(self.manufacturer_sites.keys())
        
        return manufacturers

    def _perform_search(self, search_config: Dict, ic_part_number: str, max_results: int) -> List[ICDocument]:
        """Perform search using given search configuration"""
        try:
            response = self.session.get(search_config['url'], timeout=10)
            response.raise_for_status()
            
            # Parse results using the specific parser
            return search_config['parser'](response.text, ic_part_number, max_results)
        
        except Exception as e:
            logger.error(f"Search error for {search_config['name']}: {e}")
            return []

    def _parse_google_scholar_results(self, html: str, ic_part_number: str, max_results: int) -> List[ICDocument]:
        """Parse Google Scholar search results"""
        results = []
        soup = BeautifulSoup(html, 'html.parser')
        
        for article in soup.find_all('div', class_='gs_ri')[:max_results]:
            try:
                title_elem = article.find('h3', class_='gs_rt')
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                link_elem = title_elem.find('a')
                url = link_elem.get('href') if link_elem else None
                
                # Check for PDF link
                pdf_url = None
                pdf_link = article.find('a', string=re.compile(r'\[PDF\]', re.IGNORECASE))
                if pdf_link:
                    pdf_url = pdf_link.get('href')
                
                confidence = self._calculate_relevance_score(title, ic_part_number)
                
                if confidence > 0.3:  # Minimum relevance threshold
                    results.append(ICDocument(
                        title=title,
                        url=url or '',
                        pdf_url=pdf_url,
                        source='Google Scholar',
                        manufacturer=self._extract_manufacturer_from_text(title),
                        ic_model=ic_part_number,
                        confidence_score=confidence
                    ))
            
            except Exception as e:
                logger.error(f"Error parsing Google Scholar result: {e}")
                continue
        
        return results

    def _parse_ieee_results(self, html: str, ic_part_number: str, max_results: int) -> List[ICDocument]:
        """Parse IEEE Xplore search results"""
        results = []
        soup = BeautifulSoup(html, 'html.parser')
        
        for article in soup.find_all('div', class_='List-results-items')[:max_results]:
            try:
                title_elem = article.find('a', class_='fw-bold')
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                url = urljoin('https://ieeexplore.ieee.org/', title_elem.get('href'))
                
                confidence = self._calculate_relevance_score(title, ic_part_number)
                
                if confidence > 0.4:
                    results.append(ICDocument(
                        title=title,
                        url=url,
                        pdf_url=url,  # IEEE papers are typically PDFs
                        source='IEEE Xplore',
                        manufacturer=self._extract_manufacturer_from_text(title),
                        ic_model=ic_part_number,
                        confidence_score=confidence
                    ))
            
            except Exception as e:
                logger.error(f"Error parsing IEEE result: {e}")
                continue
        
        return results

    def _parse_researchgate_results(self, html: str, ic_part_number: str, max_results: int) -> List[ICDocument]:
        """Parse ResearchGate search results"""
        results = []
        soup = BeautifulSoup(html, 'html.parser')
        
        for paper in soup.find_all('div', class_='nova-legacy-e-text')[:max_results]:
            try:
                title_elem = paper.find('a')
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                url = urljoin('https://www.researchgate.net/', title_elem.get('href'))
                
                confidence = self._calculate_relevance_score(title, ic_part_number)
                
                if confidence > 0.3:
                    results.append(ICDocument(
                        title=title,
                        url=url,
                        pdf_url=None,  # Would need additional processing
                        source='ResearchGate',
                        manufacturer=self._extract_manufacturer_from_text(title),
                        ic_model=ic_part_number,
                        confidence_score=confidence
                    ))
            
            except Exception as e:
                logger.error(f"Error parsing ResearchGate result: {e}")
                continue
        
        return results

    def _parse_datasheet_archive(self, html: str, ic_part_number: str, max_results: int) -> List[ICDocument]:
        """Parse Datasheet Archive results"""
        results = []
        soup = BeautifulSoup(html, 'html.parser')
        
        for link in soup.find_all('a', href=re.compile(r'\.pdf', re.IGNORECASE))[:max_results]:
            try:
                title = link.get_text(strip=True)
                url = link.get('href')
                
                if not url.startswith('http'):
                    url = urljoin('https://www.datasheetarchive.com/', url)
                
                confidence = self._calculate_relevance_score(title, ic_part_number)
                
                if confidence > 0.5:
                    results.append(ICDocument(
                        title=title,
                        url=url,
                        pdf_url=url,
                        source='Datasheet Archive',
                        manufacturer=self._extract_manufacturer_from_text(title),
                        ic_model=ic_part_number,
                        confidence_score=confidence
                    ))
            
            except Exception as e:
                logger.error(f"Error parsing Datasheet Archive result: {e}")
                continue
        
        return results

    def _parse_alldatasheet(self, html: str, ic_part_number: str, max_results: int) -> List[ICDocument]:
        """Parse AllDataSheet results"""
        results = []
        soup = BeautifulSoup(html, 'html.parser')
        
        for row in soup.find_all('tr')[:max_results]:
            try:
                pdf_link = row.find('a', href=re.compile(r'\.pdf', re.IGNORECASE))
                if not pdf_link:
                    continue
                
                title = pdf_link.get_text(strip=True)
                url = pdf_link.get('href')
                
                if not url.startswith('http'):
                    url = urljoin('https://www.alldatasheet.com/', url)
                
                confidence = self._calculate_relevance_score(title, ic_part_number)
                
                if confidence > 0.6:
                    results.append(ICDocument(
                        title=title,
                        url=url,
                        pdf_url=url,
                        source='AllDataSheet',
                        manufacturer=self._extract_manufacturer_from_text(title),
                        ic_model=ic_part_number,
                        confidence_score=confidence
                    ))
            
            except Exception as e:
                logger.error(f"Error parsing AllDataSheet result: {e}")
                continue
        
        return results

    def _parse_datasheetspdf(self, html: str, ic_part_number: str, max_results: int) -> List[ICDocument]:
        """Parse DatasheetsPDF results"""
        results = []
        soup = BeautifulSoup(html, 'html.parser')
        
        for link in soup.find_all('a', href=re.compile(r'datasheet', re.IGNORECASE))[:max_results]:
            try:
                title = link.get_text(strip=True)
                url = link.get('href')
                
                if not url.startswith('http'):
                    url = urljoin('https://www.datasheetspdf.com/', url)
                
                confidence = self._calculate_relevance_score(title, ic_part_number)
                
                if confidence > 0.4:
                    results.append(ICDocument(
                        title=title,
                        url=url,
                        pdf_url=url,  # Assume PDF available
                        source='DatasheetsPDF',
                        manufacturer=self._extract_manufacturer_from_text(title),
                        ic_model=ic_part_number,
                        confidence_score=confidence
                    ))
            
            except Exception as e:
                logger.error(f"Error parsing DatasheetsPDF result: {e}")
                continue
        
        return results

    def _search_manufacturer_site(self, manufacturer: str, ic_part_number: str, max_results: int) -> List[ICDocument]:
        """Search specific manufacturer website"""
        results = []
        
        try:
            site_info = self.manufacturer_sites[manufacturer]
            search_url = f"{site_info['search_url']}?q={quote(ic_part_number)}"
            
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for PDF links and datasheet references
            pdf_links = soup.find_all('a', href=re.compile(r'\.pdf', re.IGNORECASE))
            datasheet_links = soup.find_all('a', string=re.compile(r'datasheet', re.IGNORECASE))
            
            all_links = pdf_links + datasheet_links
            
            for link in all_links[:max_results]:
                try:
                    title = link.get_text(strip=True) or link.get('title', '')
                    url = link.get('href')
                    
                    if not url.startswith('http'):
                        url = urljoin(site_info['base_url'], url)
                    
                    confidence = self._calculate_relevance_score(title + ' ' + url, ic_part_number)
                    confidence += 0.2  # Boost for manufacturer-specific sites
                    
                    if confidence > 0.5:
                        results.append(ICDocument(
                            title=title,
                            url=url,
                            pdf_url=url if url.endswith('.pdf') else None,
                            source=manufacturer.title(),
                            manufacturer=manufacturer.title(),
                            ic_model=ic_part_number,
                            confidence_score=min(confidence, 1.0)
                        ))
                
                except Exception as e:
                    logger.error(f"Error processing manufacturer link: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error searching {manufacturer} site: {e}")
        
        return results

    def _calculate_relevance_score(self, text: str, ic_part_number: str) -> float:
        """Calculate relevance score based on text similarity and keywords"""
        text = text.lower()
        ic_part_number = ic_part_number.lower()
        
        score = 0.0
        
        # Exact match bonus
        if ic_part_number in text:
            score += 0.6
        
        # Partial match bonus
        ic_components = re.split(r'[^a-zA-Z0-9]', ic_part_number)
        for component in ic_components:
            if len(component) > 2 and component in text:
                score += 0.1
        
        # Keyword bonuses
        keywords = ['datasheet', 'pdf', 'specification', 'manual', 'marking', 'package']
        for keyword in keywords:
            if keyword in text:
                score += 0.1
        
        # Manufacturer name bonus
        for manufacturer in self.manufacturer_sites.keys():
            if manufacturer in text:
                score += 0.15
        
        return min(score, 1.0)

    def _extract_manufacturer_from_text(self, text: str) -> str:
        """Extract manufacturer name from text"""
        text = text.lower()
        
        # Check against known manufacturer patterns
        for manufacturer, info in self.manufacturer_sites.items():
            for pattern in info['patterns']:
                if re.search(pattern.lower(), text):
                    return manufacturer.title()
        
        # Check for common manufacturer names
        common_manufacturers = [
            'texas instruments', 'ti', 'stmicroelectronics', 'st', 'microchip',
            'atmel', 'infineon', 'analog devices', 'adi', 'nxp', 'freescale',
            'maxim', 'linear technology', 'cypress', 'xilinx', 'altera', 'intel'
        ]
        
        for mfg in common_manufacturers:
            if mfg in text:
                return mfg.title()
        
        return 'Unknown'

    def _deduplicate_results(self, results: List[ICDocument]) -> List[ICDocument]:
        """Remove duplicate results based on URL similarity"""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url_hash = hashlib.md5(result.url.encode()).hexdigest()
            if url_hash not in seen_urls:
                seen_urls.add(url_hash)
                unique_results.append(result)
        
        return unique_results

    def download_document(self, document: ICDocument) -> Optional[str]:
        """Download a document and return the local file path"""
        try:
            if not document.pdf_url:
                logger.warning(f"No PDF URL available for {document.title}")
                return None
            
            # Create safe filename
            safe_filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', document.title[:50])
            file_path = os.path.join(self.download_dir, f"{safe_filename}.pdf")
            
            # Skip if already downloaded
            if os.path.exists(file_path):
                logger.info(f"Document already exists: {file_path}")
                return file_path
            
            logger.info(f"📥 Downloading: {document.title}")
            
            response = self.session.get(document.pdf_url, timeout=30, stream=True)
            response.raise_for_status()
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"✅ Downloaded: {file_path}")
            return file_path
        
        except Exception as e:
            logger.error(f"Error downloading {document.title}: {e}")
            return None

    def extract_ic_marking_info(self, pdf_path: str, ic_part_number: str) -> Dict[str, Any]:
        """Extract IC marking information from downloaded PDF"""
        try:
            logger.info(f"📄 Extracting marking info from: {os.path.basename(pdf_path)}")
            
            # Try PyMuPDF first (better text extraction)
            try:
                doc = fitz.open(pdf_path)
                text = ""
                for page in doc:
                    text += page.get_text()
                doc.close()
            except:
                # Fallback to PyPDF2
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text()
            
            # Extract marking information
            marking_info = self._parse_marking_information(text, ic_part_number)
            
            return {
                'extracted_text': text[:1000],  # First 1000 characters
                'marking_info': marking_info,
                'file_path': pdf_path,
                'extraction_date': time.strftime('%Y-%m-%d %H:%M:%S')
            }
        
        except Exception as e:
            logger.error(f"Error extracting from PDF {pdf_path}: {e}")
            return {
                'extracted_text': None,
                'marking_info': None,
                'error': str(e)
            }

    def _parse_marking_information(self, text: str, ic_part_number: str) -> Dict[str, Any]:
        """Parse marking information from extracted text"""
        marking_info = {
            'part_number': ic_part_number,
            'package_types': [],
            'marking_codes': [],
            'pin_configurations': [],
            'date_codes': [],
            'manufacturer_codes': [],
            'lot_codes': [],
            'assembly_codes': []
        }
        
        try:
            # Extract package types
            package_patterns = [
                r'(DIP-?\d+)', r'(SOIC-?\d+)', r'(QFP-?\d+)', r'(BGA-?\d+)',
                r'(QFN-?\d+)', r'(TSSOP-?\d+)', r'(MSOP-?\d+)', r'(SOT-?\d+)'
            ]
            
            for pattern in package_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                marking_info['package_types'].extend(matches)
            
            # Extract marking codes (typical patterns)
            marking_patterns = [
                r'[A-Z]{2,4}\d{3,6}[A-Z]?',  # Generic marking pattern
                r'\d{4}[A-Z]\d{2}',  # Date code pattern
                r'[A-Z]\d{3}[A-Z]',  # Lot code pattern
            ]
            
            for pattern in marking_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    marking_info['marking_codes'].extend(matches[:5])  # Limit results
            
            # Extract specific marking information from text
            marking_section = self._find_marking_section(text)
            if marking_section:
                marking_info['detailed_marking'] = marking_section[:500]
            
            # Remove duplicates and clean up
            for key in marking_info:
                if isinstance(marking_info[key], list):
                    marking_info[key] = list(set(marking_info[key]))
        
        except Exception as e:
            logger.error(f"Error parsing marking information: {e}")
        
        return marking_info

    def _find_marking_section(self, text: str) -> Optional[str]:
        """Find the marking/package information section in the text"""
        # Look for common section headers
        section_patterns = [
            r'(marking.*?information.*?)(?=\n\n|\n[A-Z]|\Z)',
            r'(package.*?marking.*?)(?=\n\n|\n[A-Z]|\Z)',
            r'(device.*?marking.*?)(?=\n\n|\n[A-Z]|\Z)',
            r'(top.*?mark.*?)(?=\n\n|\n[A-Z]|\Z)'
        ]
        
        for pattern in section_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return None

    def process_ic_search_and_extraction(self, ic_part_number: str) -> Dict[str, Any]:
        """Complete process: search, download, and extract marking information"""
        logger.info(f"🚀 Starting complete IC search and extraction for: {ic_part_number}")
        
        # Step 1: Search for documentation
        documents = self.search_ic_documentation(ic_part_number, max_results=5)
        
        if not documents:
            return {
                'status': 'no_documents_found',
                'ic_part_number': ic_part_number,
                'message': 'No relevant documentation found'
            }
        
        # Step 2: Download and process documents
        processed_docs = []
        
        for doc in documents[:3]:  # Process top 3 most relevant documents
            if doc.pdf_url:
                file_path = self.download_document(doc)
                if file_path:
                    extraction_result = self.extract_ic_marking_info(file_path, ic_part_number)
                    processed_docs.append({
                        'document': doc.__dict__,
                        'extraction': extraction_result
                    })
        
        return {
            'status': 'success',
            'ic_part_number': ic_part_number,
            'found_documents': len(documents),
            'processed_documents': len(processed_docs),
            'documents': [doc.__dict__ for doc in documents],
            'processed_docs': processed_docs,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }

# Example usage and testing
if __name__ == "__main__":
    searcher = IntelligentICSearch()
    
    # Test with a common IC
    test_ic = "STM32F103C8T6"
    result = searcher.process_ic_search_and_extraction(test_ic)
    
    print(f"Search Results for {test_ic}:")
    print(f"Status: {result['status']}")
    print(f"Documents found: {result.get('found_documents', 0)}")
    print(f"Documents processed: {result.get('processed_documents', 0)}")
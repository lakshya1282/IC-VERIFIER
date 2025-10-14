#!/usr/bin/env python3
"""
Enhanced Database Manager for Comprehensive IC Verification Storage
Stores original images, marked images, extracted text, verification results, 
manufacturer data, and scraped internet information with unique identifiers.
"""

import os
import sys
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
import base64
import hashlib
from dataclasses import dataclass, asdict
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, Column, String, Text, JSON, DateTime, Float, Integer, Boolean, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import event
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database models base
Base = declarative_base()

class ICVerificationRecord(Base):
    """Main IC verification record with comprehensive data storage"""
    __tablename__ = 'ic_verification_records'
    
    # Primary identifier
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    unique_id = Column(String, unique=True, index=True)  # Human-readable unique ID
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Original image data
    original_image_path = Column(String)
    original_image_data = Column(LargeBinary)  # Base64 encoded image
    original_image_hash = Column(String, index=True)  # SHA256 hash for deduplication
    original_image_metadata = Column(JSON)  # Image dimensions, format, etc.
    
    # Marked image data
    marked_image_path = Column(String)
    marked_image_data = Column(LargeBinary)  # Base64 encoded marked image
    thumbnail_path = Column(String)
    thumbnail_data = Column(LargeBinary)  # Base64 encoded thumbnail
    
    # OCR and extraction data
    extracted_text = Column(JSON)  # List of extracted text strings
    ocr_confidence = Column(Float)  # Overall OCR confidence score
    extraction_method = Column(String)  # OCR method used
    
    # ML verification results
    verification_result = Column(JSON)  # Complete verification pipeline result
    authenticity_status = Column(String, index=True)  # AUTHENTIC, SUSPICIOUS, FRAUD, UNKNOWN
    confidence_score = Column(Float, index=True)  # Overall confidence score
    detected_components = Column(Integer)  # Number of IC components detected
    
    # Internet search and enrichment data
    web_scraping_results = Column(JSON)  # Results from web scrapers
    intelligent_search_results = Column(JSON)  # Results from intelligent search
    manufacturer_data = Column(JSON)  # Consolidated manufacturer information
    datasheet_links = Column(JSON)  # List of found datasheet URLs
    specifications = Column(JSON)  # Technical specifications
    
    # QR code and tracking data
    qr_code_data = Column(Text)  # JSON data embedded in QR code
    tracking_url = Column(String)  # URL for verification tracking
    
    # User and request metadata
    user_agent = Column(String)
    ip_address = Column(String)
    api_version = Column(String)
    processing_time = Column(Float)  # Total processing time in seconds
    
    # Search and enrichment metadata
    sources_used = Column(JSON)  # List of sources used for enrichment
    cache_used = Column(Boolean, default=False)  # Whether cached data was used
    enrichment_timestamp = Column(DateTime)  # When enrichment was performed
    enrichment_status = Column(String)  # SUCCESS, PARTIAL, FAILED

class ICManufacturerDatabase(Base):
    """Extended manufacturer and IC database"""
    __tablename__ = 'ic_manufacturer_database'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    part_number = Column(String, index=True)
    manufacturer = Column(String, index=True)
    description = Column(Text)
    package_types = Column(JSON)
    specifications = Column(JSON)
    datasheet_urls = Column(JSON)
    marking_patterns = Column(JSON)
    release_date = Column(String)
    
    # Enrichment data
    scraped_data = Column(JSON)  # Data from web scraping
    verification_count = Column(Integer, default=0)  # How many times this IC was verified
    last_verified = Column(DateTime)
    confidence_ratings = Column(JSON)  # Historical confidence scores
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class ICSearchCache(Base):
    """Cache for internet search results"""
    __tablename__ = 'ic_search_cache'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    part_number = Column(String, index=True)
    search_hash = Column(String, unique=True, index=True)  # Hash of search parameters
    search_results = Column(JSON)  # Cached search results
    expiry_date = Column(DateTime)
    hit_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_accessed = Column(DateTime, default=lambda: datetime.now(timezone.utc))

@dataclass
class ICVerificationData:
    """Data structure for IC verification storage"""
    unique_id: str
    original_image_b64: str
    marked_image_b64: str
    thumbnail_b64: Optional[str]
    extracted_text: List[str]
    verification_result: Dict[str, Any]
    internet_enrichment: Dict[str, Any]
    file_paths: Dict[str, str]
    metadata: Dict[str, Any]

class EnhancedDatabaseManager:
    """Enhanced database manager for comprehensive IC verification storage"""
    
    def __init__(self, database_url: str = None, sqlite_file: str = "ic_verification_enhanced.db"):
        """Initialize the database manager"""
        
        # Setup database connection
        if database_url:
            self.database_url = database_url
        else:
            # Default to SQLite for development
            db_path = os.path.abspath(sqlite_file)
            self.database_url = f"sqlite:///{db_path}"
        
        logger.info(f"🗄️  Connecting to database: {self.database_url}")
        
        self.engine = create_engine(
            self.database_url, 
            echo=False,  # Set to True for SQL debugging
            pool_pre_ping=True
        )
        
        # Create all tables
        Base.metadata.create_all(self.engine)
        
        # Create session factory
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        logger.info("✅ Database initialized successfully")
    
    def get_session(self) -> Session:
        """Get a database session"""
        return self.SessionLocal()
    
    def calculate_image_hash(self, image_data: str) -> str:
        """Calculate SHA256 hash of image data"""
        return hashlib.sha256(image_data.encode()).hexdigest()
    
    def store_verification_record(self, verification_data: ICVerificationData,
                                request_metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store a complete IC verification record"""
        
        try:
            session = self.get_session()
            
            # Calculate image hash for deduplication
            image_hash = self.calculate_image_hash(verification_data.original_image_b64)
            
            # Check if this exact image was already processed
            existing_record = session.query(ICVerificationRecord).filter(
                ICVerificationRecord.original_image_hash == image_hash
            ).first()
            
            if existing_record:
                logger.info(f"🔍 Found existing record for image hash: {image_hash[:16]}...")
                session.close()
                return existing_record.unique_id
            
            # Create new verification record
            record = ICVerificationRecord(
                unique_id=verification_data.unique_id,
                
                # Image data
                original_image_path=verification_data.file_paths.get('original'),
                original_image_data=verification_data.original_image_b64.encode(),
                original_image_hash=image_hash,
                original_image_metadata=verification_data.metadata.get('image_properties', {}),
                
                marked_image_path=verification_data.file_paths.get('marked'),
                marked_image_data=verification_data.marked_image_b64.encode(),
                thumbnail_path=verification_data.file_paths.get('thumbnail'),
                thumbnail_data=verification_data.thumbnail_b64.encode() if verification_data.thumbnail_b64 else None,
                
                # OCR data
                extracted_text=verification_data.extracted_text,
                ocr_confidence=verification_data.verification_result.get('confidence_score', 0.0),
                extraction_method='enhanced_ocr_pipeline',
                
                # Verification results
                verification_result=verification_data.verification_result,
                authenticity_status=verification_data.verification_result.get('overall_authenticity', 'UNKNOWN'),
                confidence_score=verification_data.verification_result.get('confidence_score', 0.0),
                detected_components=verification_data.verification_result.get('total_detections', 0),
                
                # Internet enrichment data
                web_scraping_results=verification_data.internet_enrichment.get('web_scraping_results', []),
                intelligent_search_results=verification_data.internet_enrichment.get('intelligent_search_results', []),
                manufacturer_data=verification_data.internet_enrichment.get('consolidated_data', {}),
                datasheet_links=verification_data.internet_enrichment.get('consolidated_data', {}).get('datasheets', []),
                specifications=verification_data.internet_enrichment.get('consolidated_data', {}).get('specifications', {}),
                
                # QR and tracking
                qr_code_data=verification_data.metadata.get('qr_data', ''),
                tracking_url=f"https://ic-verify.com/track/{verification_data.unique_id}",
                
                # Request metadata
                user_agent=request_metadata.get('user_agent', '') if request_metadata else '',
                ip_address=request_metadata.get('ip_address', '') if request_metadata else '',
                api_version=request_metadata.get('api_version', '3.0') if request_metadata else '3.0',
                processing_time=verification_data.metadata.get('processing_time', 0.0),
                
                # Enrichment metadata
                sources_used=verification_data.internet_enrichment.get('sources_used', []),
                cache_used=verification_data.internet_enrichment.get('cache_used', False),
                enrichment_timestamp=datetime.now(timezone.utc),
                enrichment_status='SUCCESS' if verification_data.internet_enrichment else 'NONE'
            )
            
            session.add(record)
            session.commit()
            
            logger.info(f"💾 Stored verification record: {verification_data.unique_id}")
            session.close()
            
            # Update manufacturer database
            self._update_manufacturer_database(verification_data)
            
            return verification_data.unique_id
            
        except Exception as e:
            logger.error(f"❌ Error storing verification record: {e}")
            if 'session' in locals():
                session.rollback()
                session.close()
            raise
    
    def _update_manufacturer_database(self, verification_data: ICVerificationData):
        """Update the manufacturer database with new information"""
        
        try:
            session = self.get_session()
            
            consolidated_data = verification_data.internet_enrichment.get('consolidated_data', {})
            manufacturer = consolidated_data.get('manufacturer', 'Unknown')
            
            for part_number in verification_data.extracted_text:
                if len(part_number.strip()) < 3:  # Skip very short strings
                    continue
                
                # Check if part already exists
                existing_part = session.query(ICManufacturerDatabase).filter(
                    ICManufacturerDatabase.part_number == part_number,
                    ICManufacturerDatabase.manufacturer == manufacturer
                ).first()
                
                if existing_part:
                    # Update existing record
                    existing_part.verification_count += 1
                    existing_part.last_verified = datetime.now(timezone.utc)
                    
                    # Update confidence ratings
                    if not existing_part.confidence_ratings:
                        existing_part.confidence_ratings = []
                    existing_part.confidence_ratings.append({
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'confidence': verification_data.verification_result.get('confidence_score', 0.0)
                    })
                    
                    # Update scraped data
                    if consolidated_data:
                        existing_part.scraped_data = consolidated_data
                    
                else:
                    # Create new record
                    new_part = ICManufacturerDatabase(
                        part_number=part_number,
                        manufacturer=manufacturer,
                        description='; '.join(consolidated_data.get('descriptions', [])),
                        package_types=consolidated_data.get('package_types', []),
                        specifications=consolidated_data.get('specifications', {}),
                        datasheet_urls=consolidated_data.get('datasheets', []),
                        marking_patterns=consolidated_data.get('marking_patterns', []),
                        scraped_data=consolidated_data,
                        verification_count=1,
                        last_verified=datetime.now(timezone.utc),
                        confidence_ratings=[{
                            'timestamp': datetime.now(timezone.utc).isoformat(),
                            'confidence': verification_data.verification_result.get('confidence_score', 0.0)
                        }]
                    )
                    session.add(new_part)
            
            session.commit()
            session.close()
            logger.info("✅ Updated manufacturer database")
            
        except Exception as e:
            logger.error(f"❌ Error updating manufacturer database: {e}")
            if 'session' in locals():
                session.rollback()
                session.close()
    
    def get_verification_record(self, unique_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a verification record by unique ID"""
        
        try:
            session = self.get_session()
            
            record = session.query(ICVerificationRecord).filter(
                ICVerificationRecord.unique_id == unique_id
            ).first()
            
            if not record:
                session.close()
                return None
            
            # Convert to dictionary
            result = {
                'id': record.id,
                'unique_id': record.unique_id,
                'created_at': record.created_at.isoformat(),
                'updated_at': record.updated_at.isoformat(),
                
                # Images (decode base64)
                'original_image_b64': record.original_image_data.decode() if record.original_image_data else None,
                'marked_image_b64': record.marked_image_data.decode() if record.marked_image_data else None,
                'thumbnail_b64': record.thumbnail_data.decode() if record.thumbnail_data else None,
                
                # File paths
                'file_paths': {
                    'original': record.original_image_path,
                    'marked': record.marked_image_path,
                    'thumbnail': record.thumbnail_path
                },
                
                # OCR and verification
                'extracted_text': record.extracted_text,
                'verification_result': record.verification_result,
                'authenticity_status': record.authenticity_status,
                'confidence_score': record.confidence_score,
                
                # Internet enrichment
                'web_scraping_results': record.web_scraping_results,
                'intelligent_search_results': record.intelligent_search_results,
                'manufacturer_data': record.manufacturer_data,
                'datasheet_links': record.datasheet_links,
                'specifications': record.specifications,
                
                # Metadata
                'qr_code_data': record.qr_code_data,
                'tracking_url': record.tracking_url,
                'processing_time': record.processing_time,
                'sources_used': record.sources_used
            }
            
            session.close()
            return result
            
        except Exception as e:
            logger.error(f"❌ Error retrieving verification record {unique_id}: {e}")
            return None
    
    def search_verification_records(self, 
                                  part_number: Optional[str] = None,
                                  manufacturer: Optional[str] = None,
                                  authenticity_status: Optional[str] = None,
                                  min_confidence: Optional[float] = None,
                                  limit: int = 50) -> List[Dict[str, Any]]:
        """Search verification records with filters"""
        
        try:
            session = self.get_session()
            
            query = session.query(ICVerificationRecord)
            
            # Apply filters
            if part_number:
                query = query.filter(ICVerificationRecord.extracted_text.contains([part_number]))
            
            if manufacturer:
                query = query.filter(ICVerificationRecord.manufacturer_data.contains({'manufacturer': manufacturer}))
            
            if authenticity_status:
                query = query.filter(ICVerificationRecord.authenticity_status == authenticity_status)
            
            if min_confidence:
                query = query.filter(ICVerificationRecord.confidence_score >= min_confidence)
            
            # Order by creation date (newest first) and limit
            records = query.order_by(ICVerificationRecord.created_at.desc()).limit(limit).all()
            
            results = []
            for record in records:
                results.append({
                    'unique_id': record.unique_id,
                    'created_at': record.created_at.isoformat(),
                    'extracted_text': record.extracted_text,
                    'authenticity_status': record.authenticity_status,
                    'confidence_score': record.confidence_score,
                    'detected_components': record.detected_components,
                    'manufacturer': record.manufacturer_data.get('manufacturer', 'Unknown') if record.manufacturer_data else 'Unknown',
                    'processing_time': record.processing_time,
                    'sources_used': record.sources_used
                })
            
            session.close()
            return results
            
        except Exception as e:
            logger.error(f"❌ Error searching verification records: {e}")
            return []
    
    def get_verification_statistics(self) -> Dict[str, Any]:
        """Get comprehensive verification statistics"""
        
        try:
            session = self.get_session()
            
            # Basic counts
            total_verifications = session.query(ICVerificationRecord).count()
            authentic_count = session.query(ICVerificationRecord).filter(
                ICVerificationRecord.authenticity_status == 'AUTHENTIC'
            ).count()
            suspicious_count = session.query(ICVerificationRecord).filter(
                ICVerificationRecord.authenticity_status == 'SUSPICIOUS'
            ).count()
            fraud_count = session.query(ICVerificationRecord).filter(
                ICVerificationRecord.authenticity_status == 'FRAUD'
            ).count()
            
            # Average confidence score
            avg_confidence = session.query(ICVerificationRecord.confidence_score).all()
            avg_confidence_score = sum([c[0] for c in avg_confidence if c[0]]) / len(avg_confidence) if avg_confidence else 0
            
            # Processing time statistics
            processing_times = [p[0] for p in session.query(ICVerificationRecord.processing_time).all() if p[0]]
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
            
            # Top manufacturers
            manufacturer_counts = {}
            manufacturer_data = session.query(ICVerificationRecord.manufacturer_data).all()
            for data in manufacturer_data:
                if data[0] and isinstance(data[0], dict):
                    manufacturer = data[0].get('manufacturer', 'Unknown')
                    manufacturer_counts[manufacturer] = manufacturer_counts.get(manufacturer, 0) + 1
            
            # Recent activity (last 24 hours)
            from datetime import timedelta
            yesterday = datetime.now(timezone.utc) - timedelta(days=1)
            recent_count = session.query(ICVerificationRecord).filter(
                ICVerificationRecord.created_at >= yesterday
            ).count()
            
            statistics = {
                'total_verifications': total_verifications,
                'authenticity_breakdown': {
                    'authentic': authentic_count,
                    'suspicious': suspicious_count,
                    'fraud': fraud_count,
                    'unknown': total_verifications - authentic_count - suspicious_count - fraud_count
                },
                'success_rate': (authentic_count / total_verifications * 100) if total_verifications > 0 else 0,
                'average_confidence_score': avg_confidence_score,
                'average_processing_time': avg_processing_time,
                'top_manufacturers': dict(sorted(manufacturer_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
                'recent_activity_24h': recent_count,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            session.close()
            return statistics
            
        except Exception as e:
            logger.error(f"❌ Error getting verification statistics: {e}")
            return {'error': str(e)}
    
    def export_verification_data(self, output_file: str, format: str = 'csv') -> bool:
        """Export verification data to file"""
        
        try:
            session = self.get_session()
            
            records = session.query(ICVerificationRecord).all()
            
            # Convert to list of dictionaries
            data = []
            for record in records:
                data.append({
                    'unique_id': record.unique_id,
                    'created_at': record.created_at,
                    'extracted_text': json.dumps(record.extracted_text) if record.extracted_text else '',
                    'authenticity_status': record.authenticity_status,
                    'confidence_score': record.confidence_score,
                    'detected_components': record.detected_components,
                    'manufacturer': record.manufacturer_data.get('manufacturer', 'Unknown') if record.manufacturer_data else 'Unknown',
                    'processing_time': record.processing_time,
                    'sources_used': json.dumps(record.sources_used) if record.sources_used else '',
                    'datasheet_count': len(record.datasheet_links) if record.datasheet_links else 0
                })
            
            # Export based on format
            df = pd.DataFrame(data)
            
            if format.lower() == 'csv':
                df.to_csv(output_file, index=False)
            elif format.lower() == 'excel':
                df.to_excel(output_file, index=False)
            elif format.lower() == 'json':
                df.to_json(output_file, orient='records', date_format='iso')
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            session.close()
            logger.info(f"✅ Exported {len(data)} records to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error exporting verification data: {e}")
            return False
    
    def cleanup_old_records(self, days_old: int = 30) -> int:
        """Clean up old verification records (keeping metadata)"""
        
        try:
            session = self.get_session()
            
            from datetime import timedelta
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
            
            # Clear image data from old records but keep metadata
            old_records = session.query(ICVerificationRecord).filter(
                ICVerificationRecord.created_at < cutoff_date
            ).all()
            
            cleaned_count = 0
            for record in old_records:
                # Clear binary image data but keep paths and metadata
                if record.original_image_data:
                    record.original_image_data = None
                    cleaned_count += 1
                if record.marked_image_data:
                    record.marked_image_data = None
                if record.thumbnail_data:
                    record.thumbnail_data = None
            
            session.commit()
            session.close()
            
            logger.info(f"🧹 Cleaned up image data from {cleaned_count} old records")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up old records: {e}")
            return 0

# Example usage and testing
if __name__ == "__main__":
    db_manager = EnhancedDatabaseManager()
    
    print("🗄️  Enhanced Database Manager Test")
    print("=" * 50)
    
    # Test data creation
    test_verification_data = ICVerificationData(
        unique_id="IC_20251013_TEST001",
        original_image_b64="fake_base64_image_data_original",
        marked_image_b64="fake_base64_image_data_marked",
        thumbnail_b64="fake_base64_image_data_thumb",
        extracted_text=["STM32F103C8T6", "ARM", "LQFP48"],
        verification_result={
            "overall_authenticity": "AUTHENTIC",
            "confidence_score": 0.95,
            "total_detections": 3
        },
        internet_enrichment={
            "consolidated_data": {
                "manufacturer": "STMicroelectronics",
                "datasheets": ["http://example.com/datasheet.pdf"],
                "specifications": {"package": "LQFP48", "pins": 48}
            },
            "sources_used": ["web_scraper", "intelligent_search"]
        },
        file_paths={
            "original": "/path/to/original.jpg",
            "marked": "/path/to/marked.jpg",
            "thumbnail": "/path/to/thumb.jpg"
        },
        metadata={
            "processing_time": 2.5,
            "qr_data": '{"id": "test123"}'
        }
    )
    
    # Test storing record
    print(f"📝 Storing test verification record...")
    stored_id = db_manager.store_verification_record(test_verification_data)
    print(f"✅ Stored with ID: {stored_id}")
    
    # Test retrieving record
    print(f"🔍 Retrieving verification record...")
    retrieved_record = db_manager.get_verification_record(stored_id)
    if retrieved_record:
        print(f"✅ Retrieved record: {retrieved_record['unique_id']}")
        print(f"   Authenticity: {retrieved_record['authenticity_status']}")
        print(f"   Confidence: {retrieved_record['confidence_score']}")
    
    # Test statistics
    print(f"📊 Getting verification statistics...")
    stats = db_manager.get_verification_statistics()
    print(f"✅ Statistics:")
    for key, value in stats.items():
        if key != 'timestamp':
            print(f"   • {key}: {value}")
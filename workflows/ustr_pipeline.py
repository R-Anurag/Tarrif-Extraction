import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.connectors.ustr import USTRConnector
from src.parsers.html_parser import HTMLParser
from src.parsers.pdf_parser import PDFParser
from src.parsers.hts_extractor import HTSExtractor
from src.validators.hts_validator import HTSValidator
from src.validators.date_validator import DateValidator
from src.validators.confidence_scorer import ConfidenceScorer
from src.normalizers.field_normalizer import FieldNormalizer
from src.normalizers.cross_reference import CrossReferenceEngine
from src.deduplication.hasher import ContentHasher
from src.storage.database import Database
from src.storage.local_storage import LocalStorage
from config.settings import PARSER_VERSION, SOURCE_PRIORITIES
from datetime import datetime, timezone
from typing import Dict


class USTRPipeline:
    def __init__(self):
        self.connector = USTRConnector()
        self.html_parser = HTMLParser()
        self.pdf_parser = PDFParser()
        self.hts_extractor = HTSExtractor()
        self.hts_validator = HTSValidator()
        self.date_validator = DateValidator()
        self.normalizer = FieldNormalizer()
        self.hasher = ContentHasher()
        self.confidence_scorer = ConfidenceScorer()
        self.cross_ref = CrossReferenceEngine()
        self.db = Database()
        self.storage = LocalStorage()
    
    def run(self, days_back: int = 7, skip_duplicates: bool = True):
        print(f"Fetching USTR documents from last {days_back} days...")
        
        try:
            documents = self.connector.fetch_documents(days_back=days_back)
            print(f"Found {len(documents)} documents")
            
            # Pre-load existing hashes
            print("Loading existing hashes for deduplication...")
            existing_hashes = self.db.get_existing_hashes(source='ustr')
            print(f"Found {len(existing_hashes)} existing documents")
            
            # Build URL-based hash set for quick duplicate detection
            if skip_duplicates:
                print("Building URL index for fast duplicate detection...")
                url_hashes = set()
                for doc in documents:
                    url_hash = self.hasher.generate_hash({
                        'source': 'ustr',
                        'source_url': doc.get('url')
                    })
                    url_hashes.add(url_hash)
            
            processed = 0
            skipped = 0
            
            for doc in documents:
                result = self.process_document(doc, existing_hashes)
                if result == 'processed':
                    processed += 1
                elif result == 'duplicate':
                    skipped += 1
            
            print(f"\nProcessed: {processed}, Skipped (duplicates): {skipped}")
            
        except Exception as e:
            print(f"Pipeline error: {e}")
    
    def process_document(self, doc: dict, existing_hashes: set = None):
        print(f"\nProcessing: {doc.get('title', 'No title')[:60]}...")
        
        start_time = datetime.now(timezone.utc)
        
        try:
            # Parse basic document info
            parsed_doc = self.connector.parse_document(doc)
            
            # Generate preliminary hash to check duplicates BEFORE downloading
            preliminary_data = {
                'source': 'ustr',
                'title': parsed_doc.get('title'),
                'source_url': parsed_doc.get('source_url')
            }
            preliminary_hash = self.hasher.generate_hash(preliminary_data)
            
            # Quick duplicate check before expensive operations
            if existing_hashes is not None and preliminary_hash in existing_hashes:
                print(f"  Duplicate detected (quick check), skipping")
                return 'duplicate'
            
            # Fetch full page content
            print(f"  Downloading page...")
            if doc.get('url'):
                content = self.connector.fetch_page_content(doc['url'])
                
                # Parse HTML content
                if 'html' in content:
                    html_path = self.storage.save_html(content['html'], 'ustr', doc['url'].split('/')[-1])
                    html_data = self.html_parser.parse(content['html'])
                    parsed_doc['html_hts_codes'] = html_data['hts_codes']
                
                # Download and parse PDFs (limit to first 2 for speed)
                pdf_links = content.get('pdf_links', [])[:2]
                if pdf_links:
                    print(f"  Downloading {len(pdf_links)} PDFs...")
                    for pdf_url in pdf_links:
                        try:
                            pdf_content = self.connector._make_request(pdf_url).content
                            pdf_path = self.storage.save_pdf(pdf_content, 'ustr', pdf_url.split('/')[-1])
                            pdf_data = self.pdf_parser.extract_from_bytes(pdf_content)
                            parsed_doc.setdefault('pdf_hts_codes', []).extend(pdf_data.get('hts_codes', []))
                        except Exception as e:
                            print(f"    PDF error: {e}")
            
            # Extract and validate HTS codes
            all_hts_codes = set()
            all_hts_codes.update(parsed_doc.get('html_hts_codes', []))
            all_hts_codes.update(parsed_doc.get('pdf_hts_codes', []))
            
            validated_products = []
            for code in all_hts_codes:
                validation = self.hts_validator.validate_hts_code(code)
                validated_products.append({
                    "hts_code": code,
                    "hts_code_validated": validation['valid'],
                    "description": ""
                })
            
            # Build tariff event
            tariff_event_data = {
                **parsed_doc,
                "tariff_action": {
                    "type": "unknown",
                    "products": validated_products
                }
            }
            
            # Normalize fields
            tariff_event_data = self.normalizer.normalize_document(tariff_event_data)
            
            # Validate dates
            date_validation = self.date_validator.validate_dates(tariff_event_data)
            
            # Calculate confidence
            confidence = self.confidence_scorer.calculate_score(
                tariff_event_data,
                {'date_validation': date_validation}
            )
            
            # Generate hash
            content_hash = self.hasher.generate_hash(tariff_event_data)
            
            # Fast duplicate check
            if existing_hashes is not None and content_hash in existing_hashes:
                print(f"  Duplicate detected (final check), skipping")
                return 'duplicate'
            
            tariff_event = {
                "source": "ustr",
                "source_priority": SOURCE_PRIORITIES["ustr"],
                "parser_version": PARSER_VERSION,
                "data": tariff_event_data,
                "raw_html_path": html_path if 'html_path' in locals() else None,
                "content_hash": content_hash,
                "confidence_score": confidence,
                "validation_status": "verified" if date_validation['valid'] else "failed"
            }
            
            # Save to database
            event_id = self.db.insert_tariff_event(tariff_event)
            
            # Build relationships with existing documents
            self._build_relationships(event_id, tariff_event_data)
            
            # Add to existing hashes
            if existing_hashes is not None:
                existing_hashes.add(content_hash)
            
            # Record metrics
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            print(f"  ✓ Saved event {event_id} with {len(validated_products)} HTS codes (confidence: {confidence:.2f}) [{duration:.1f}s]")
            return 'processed'
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return 'failed'
    
    def _build_relationships(self, event_id: str, doc_data: Dict):
        """Build relationships with existing documents from other sources"""
        hts_codes = [p['hts_code'] for p in doc_data.get('tariff_action', {}).get('products', [])]
        pub_date = doc_data.get('publication_date')
        
        if not hts_codes or not pub_date:
            return
        
        related = self.db.find_related_events('ustr', hts_codes, pub_date, limit=5)
        
        for rel_event in related:
            rel_doc = {
                'id': str(rel_event['id']),
                'source': rel_event['source'],
                'title': rel_event['data'].get('title', ''),
                'publication_date': rel_event['data'].get('publication_date'),
                'identifiers': rel_event['data'].get('identifiers', {}),
                'tariff_action': rel_event['data'].get('tariff_action', {})
            }
            
            current_doc = {
                'id': event_id,
                'source': 'ustr',
                'title': doc_data.get('title', ''),
                'publication_date': pub_date,
                'identifiers': doc_data.get('identifiers', {}),
                'tariff_action': doc_data.get('tariff_action', {})
            }
            
            matches = self.cross_ref.find_related_documents(current_doc, [rel_doc])
            
            for match in matches:
                self.db.insert_relationship(
                    parent_id=event_id,
                    related_id=match['document_id'],
                    rel_type=match['relationship_type'],
                    confidence=match['confidence'],
                    factors=match['matching_factors']
                )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='USTR Pipeline')
    parser.add_argument('--days', type=int, default=7, help='Days back to fetch')
    args = parser.parse_args()
    
    pipeline = USTRPipeline()
    pipeline.run(days_back=args.days)

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Same imports as ustr_pipeline.py but with fast mode
from workflows.ustr_pipeline import USTRPipeline

class FastUSTRPipeline(USTRPipeline):
    """Fast version - skips PDF downloads"""
    
    def process_document(self, doc: dict, existing_hashes: set = None):
        print(f"\nProcessing: {doc.get('title', 'No title')[:60]}...")
        
        from datetime import datetime, timezone
        start_time = datetime.now(timezone.utc)
        
        try:
            parsed_doc = self.connector.parse_document(doc)
            
            # Quick duplicate check
            preliminary_hash = self.hasher.generate_hash({
                'source': 'ustr',
                'source_url': parsed_doc.get('source_url')
            })
            
            if existing_hashes is not None and preliminary_hash in existing_hashes:
                print(f"  Duplicate detected, skipping")
                return 'duplicate'
            
            # Fetch page content (HTML only, skip PDFs)
            print(f"  Downloading page (fast mode - no PDFs)...")
            if doc.get('url'):
                content = self.connector.fetch_page_content(doc['url'])
                
                if 'html' in content:
                    html_path = self.storage.save_html(content['html'], 'ustr', doc['url'].split('/')[-1])
                    html_data = self.html_parser.parse(content['html'])
                    parsed_doc['html_hts_codes'] = html_data['hts_codes']
            
            # Continue with rest of processing (no PDF parsing)
            all_hts_codes = set(parsed_doc.get('html_hts_codes', []))
            
            validated_products = []
            for code in all_hts_codes:
                validation = self.hts_validator.validate_hts_code(code)
                validated_products.append({
                    "hts_code": code,
                    "hts_code_validated": validation['valid'],
                    "description": ""
                })
            
            tariff_event_data = {
                **parsed_doc,
                "tariff_action": {
                    "type": "unknown",
                    "products": validated_products
                }
            }
            
            tariff_event_data = self.normalizer.normalize_document(tariff_event_data)
            date_validation = self.date_validator.validate_dates(tariff_event_data)
            confidence = self.confidence_scorer.calculate_score(
                tariff_event_data,
                {'date_validation': date_validation}
            )
            
            content_hash = self.hasher.generate_hash(tariff_event_data)
            
            if existing_hashes is not None and content_hash in existing_hashes:
                print(f"  Duplicate detected (final), skipping")
                return 'duplicate'
            
            from config.settings import SOURCE_PRIORITIES, PARSER_VERSION
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
            
            event_id = self.db.insert_tariff_event(tariff_event)
            
            if existing_hashes is not None:
                existing_hashes.add(content_hash)
            
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            print(f"  ✓ Saved event {event_id} with {len(validated_products)} HTS codes (confidence: {confidence:.2f}) [{duration:.1f}s]")
            return 'processed'
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return 'failed'


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Fast USTR Pipeline (no PDFs)')
    parser.add_argument('--days', type=int, default=7, help='Days back to fetch')
    args = parser.parse_args()
    
    print("Running FAST mode (HTML only, no PDF downloads)")
    pipeline = FastUSTRPipeline()
    pipeline.run(days_back=args.days)

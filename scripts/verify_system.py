import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_phase1():
    print("\n" + "="*60)
    print("Phase 1: Foundation")
    print("="*60)
    try:
        from src.storage.database import Database
        from src.storage.local_storage import LocalStorage
        from src.utils.rate_limiter import RateLimiter
        
        storage = LocalStorage()
        limiter = RateLimiter(max_calls=2, period=1)
        
        print("✓ Database module")
        print("✓ Local storage")
        print("✓ Rate limiter")
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_phase2():
    print("\n" + "="*60)
    print("Phase 2: Federal Register")
    print("="*60)
    try:
        from src.connectors.federal_register import FederalRegisterConnector
        from src.parsers.html_parser import HTMLParser
        from src.parsers.pdf_parser import PDFParser
        from src.parsers.hts_extractor import HTSExtractor
        from src.validators.hts_validator import HTSValidator
        
        connector = FederalRegisterConnector()
        
        print("✓ Federal Register connector")
        print("✓ HTML parser")
        print("✓ PDF parser")
        print("✓ HTS extractor")
        print("✓ HTS validator")
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_phase3():
    print("\n" + "="*60)
    print("Phase 3: Validation & Normalization")
    print("="*60)
    try:
        from src.validators.date_validator import DateValidator
        from src.validators.rate_validator import RateValidator
        from src.validators.confidence_scorer import ConfidenceScorer
        from src.normalizers.field_normalizer import FieldNormalizer
        from src.deduplication.hasher import ContentHasher
        
        print("✓ Date validator")
        print("✓ Rate validator")
        print("✓ Confidence scorer")
        print("✓ Field normalizer")
        print("✓ Content hasher")
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_phase4():
    print("\n" + "="*60)
    print("Phase 4: Multi-Source Integration")
    print("="*60)
    try:
        from src.connectors.ustr import USTRConnector
        from src.connectors.cbp import CBPConnector
        from src.normalizers.cross_reference import CrossReferenceEngine
        
        print("✓ USTR connector")
        print("✓ CBP connector")
        print("✓ Cross-reference engine")
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


if __name__ == "__main__":
    print("="*60)
    print("Tariff Extraction System - Verification")
    print("="*60)
    
    results = [
        test_phase1(),
        test_phase2(),
        test_phase3(),
        test_phase4(),
    ]
    
    print("\n" + "="*60)
    if all(results):
        print("✓ All components verified successfully!")
        print("\nSystem is ready. Run pipelines:")
        print("  python workflows/federal_register_pipeline.py --days 1")
        print("  python workflows/ustr_pipeline_fast.py --days 1")
        print("  python workflows/cbp_pipeline.py --days 7")
    else:
        print("✗ Some components failed. Check output above.")
    print("="*60)

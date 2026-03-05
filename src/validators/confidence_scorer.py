from typing import Dict, List


class ConfidenceScorer:
    def __init__(self):
        self.weights = {
            'required_fields': 0.25,
            'hts_validation': 0.25,
            'date_validation': 0.15,
            'rate_validation': 0.15,
            'extraction_quality': 0.20
        }
    
    def calculate_score(self, data: Dict, validation_results: Dict = None) -> float:
        """Calculate confidence score 0.0-1.0"""
        score = 0.0
        
        # Required fields score
        score += self._score_required_fields(data) * self.weights['required_fields']
        
        # HTS validation score
        score += self._score_hts_validation(data) * self.weights['hts_validation']
        
        # Date validation score
        if validation_results and 'date_validation' in validation_results:
            score += self._score_date_validation(validation_results['date_validation']) * self.weights['date_validation']
        else:
            score += self._score_date_validation_basic(data) * self.weights['date_validation']
        
        # Rate validation score
        score += self._score_rate_validation(data) * self.weights['rate_validation']
        
        # Extraction quality score
        score += self._score_extraction_quality(data) * self.weights['extraction_quality']
        
        return max(0.0, min(1.0, score))
    
    def _score_required_fields(self, data: Dict) -> float:
        required = [
            'source',
            'document_type',
            'title',
            'publication_date',
            'source_url'
        ]
        
        present = sum(1 for field in required if data.get(field))
        return present / len(required)
    
    def _score_hts_validation(self, data: Dict) -> float:
        products = data.get('tariff_action', {}).get('products', [])
        
        if not products:
            return 0.0
        
        valid_count = sum(1 for p in products if p.get('hts_code_validated'))
        return valid_count / len(products)
    
    def _score_date_validation(self, validation: Dict) -> float:
        if not validation.get('valid'):
            return 0.0
        
        # Deduct for warnings
        warning_penalty = len(validation.get('warnings', [])) * 0.1
        return max(0.0, 1.0 - warning_penalty)
    
    def _score_date_validation_basic(self, data: Dict) -> float:
        score = 1.0
        
        if not data.get('publication_date'):
            score -= 0.5
        
        if not data.get('effective_date'):
            score -= 0.3
        
        return max(0.0, score)
    
    def _score_rate_validation(self, data: Dict) -> float:
        action = data.get('tariff_action', {})
        
        if not action.get('rate_original'):
            return 0.0
        
        if action.get('rate_normalized') is not None:
            return 1.0
        
        return 0.5
    
    def _score_extraction_quality(self, data: Dict) -> float:
        score = 1.0
        metadata = data.get('extraction_metadata', {})
        
        # Deduct for OCR usage
        if metadata.get('ocr_used'):
            score -= 0.3
        
        # Deduct for fallback methods
        if metadata.get('table_extraction_method') == 'fallback':
            score -= 0.2
        
        # Bonus for cross-references
        if len(data.get('related_documents', [])) > 0:
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def get_quality_label(self, score: float) -> str:
        """Convert score to quality label"""
        if score >= 0.9:
            return "excellent"
        elif score >= 0.75:
            return "good"
        elif score >= 0.6:
            return "fair"
        elif score >= 0.4:
            return "poor"
        else:
            return "very_poor"

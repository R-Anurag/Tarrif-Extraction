from typing import Dict, List, Optional
from difflib import SequenceMatcher
from datetime import datetime, timedelta


class CrossReferenceEngine:
    def __init__(self):
        self.similarity_threshold = 0.7
        self.date_window_days = 30
    
    def find_related_documents(self, current_doc: Dict, existing_docs: List[Dict]) -> List[Dict]:
        """Find documents related to current document across sources"""
        matches = []
        
        for existing in existing_docs:
            # Skip same source
            if current_doc.get('source') == existing.get('source'):
                continue
            
            confidence = 0.0
            relationship_type = None
            matching_factors = []
            
            # 1. Match by document numbers
            doc_num_match = self._match_document_numbers(current_doc, existing)
            if doc_num_match:
                confidence += 0.4
                relationship_type = 'references'
                matching_factors.append('document_number')
            
            # 2. Match by HTS codes overlap
            hts_score = self._match_hts_codes(current_doc, existing)
            if hts_score > 0:
                confidence += hts_score * 0.3
                if not relationship_type:
                    relationship_type = 'related_products'
                matching_factors.append('hts_codes')
            
            # 3. Match by title similarity
            title_score = self._match_titles(current_doc, existing)
            if title_score > self.similarity_threshold:
                confidence += title_score * 0.2
                if not relationship_type:
                    relationship_type = 'similar_topic'
                matching_factors.append('title')
            
            # 4. Match by date proximity
            date_score = self._match_dates(current_doc, existing)
            if date_score > 0:
                confidence += date_score * 0.1
                matching_factors.append('date_proximity')
            
            if confidence >= 0.5:
                matches.append({
                    'document_id': existing.get('id'),
                    'source': existing.get('source'),
                    'confidence': round(confidence, 2),
                    'relationship_type': relationship_type,
                    'matching_factors': matching_factors
                })
        
        return sorted(matches, key=lambda x: x['confidence'], reverse=True)
    
    def _match_document_numbers(self, doc1: Dict, doc2: Dict) -> bool:
        """Check if documents reference each other by number"""
        # Federal Register document number
        fr_num1 = doc1.get('identifiers', {}).get('fr_document_number')
        fr_num2 = doc2.get('identifiers', {}).get('fr_document_number')
        
        if fr_num1 and fr_num2 and fr_num1 == fr_num2:
            return True
        
        # Check if one document mentions the other's number in title/abstract
        doc1_text = (doc1.get('title', '') + ' ' + doc1.get('abstract', '')).lower()
        doc2_text = (doc2.get('title', '') + ' ' + doc2.get('abstract', '')).lower()
        
        if fr_num1 and fr_num1.lower() in doc2_text:
            return True
        if fr_num2 and fr_num2.lower() in doc1_text:
            return True
        
        return False
    
    def _match_hts_codes(self, doc1: Dict, doc2: Dict) -> float:
        """Calculate HTS code overlap score"""
        products1 = doc1.get('tariff_action', {}).get('products', [])
        products2 = doc2.get('tariff_action', {}).get('products', [])
        
        if not products1 or not products2:
            return 0.0
        
        hts1 = set(p.get('hts_code') for p in products1 if p.get('hts_code'))
        hts2 = set(p.get('hts_code') for p in products2 if p.get('hts_code'))
        
        if not hts1 or not hts2:
            return 0.0
        
        overlap = len(hts1 & hts2)
        union = len(hts1 | hts2)
        
        return overlap / union if union > 0 else 0.0
    
    def _match_titles(self, doc1: Dict, doc2: Dict) -> float:
        """Calculate title similarity score"""
        title1 = doc1.get('title', '').lower()
        title2 = doc2.get('title', '').lower()
        
        if not title1 or not title2:
            return 0.0
        
        return SequenceMatcher(None, title1, title2).ratio()
    
    def _match_dates(self, doc1: Dict, doc2: Dict) -> float:
        """Calculate date proximity score"""
        date1_str = doc1.get('publication_date')
        date2_str = doc2.get('publication_date')
        
        if not date1_str or not date2_str:
            return 0.0
        
        try:
            date1 = datetime.strptime(date1_str, "%Y-%m-%d")
            date2 = datetime.strptime(date2_str, "%Y-%m-%d")
            
            days_diff = abs((date1 - date2).days)
            
            if days_diff <= self.date_window_days:
                return 1.0 - (days_diff / self.date_window_days)
        except:
            pass
        
        return 0.0
    
    def determine_relationship_type(self, doc1: Dict, doc2: Dict) -> str:
        """Determine specific relationship between documents"""
        source1 = doc1.get('source')
        source2 = doc2.get('source')
        
        # Federal Register -> USTR: USTR provides policy context
        if source1 == 'federal_register' and source2 == 'ustr':
            return 'policy_context'
        elif source1 == 'ustr' and source2 == 'federal_register':
            return 'legal_authority'
        
        # Federal Register -> CBP: CBP implements
        if source1 == 'federal_register' and source2 == 'cbp_csms':
            return 'implementation'
        elif source1 == 'cbp_csms' and source2 == 'federal_register':
            return 'implements'
        
        # USTR -> CBP: CBP implements USTR policy
        if source1 == 'ustr' and source2 == 'cbp_csms':
            return 'operational_guidance'
        elif source1 == 'cbp_csms' and source2 == 'ustr':
            return 'implements_policy'
        
        return 'related'

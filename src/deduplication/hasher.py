import hashlib
import json
from typing import Dict, List, Optional
from difflib import SequenceMatcher


class ContentHasher:
    def __init__(self):
        self.similarity_threshold = 0.85
    
    def generate_hash(self, data: Dict) -> str:
        """Generate SHA-256 hash from normalized fields"""
        normalized_fields = {
            'source': data.get('source'),
            'document_type': data.get('document_type'),
            'publication_date': data.get('publication_date'),
            'fr_document_number': data.get('identifiers', {}).get('fr_document_number'),
            'hts_codes': sorted([
                p.get('hts_code') 
                for p in data.get('tariff_action', {}).get('products', [])
                if p.get('hts_code')
            ]),
        }
        
        content = json.dumps(normalized_fields, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def generate_fuzzy_hash(self, data: Dict) -> str:
        """Generate hash for fuzzy matching (less strict)"""
        fuzzy_fields = {
            'source': data.get('source'),
            'publication_date': data.get('publication_date'),
            'hts_codes': sorted([
                p.get('hts_code')[:7]  # Only chapter and heading
                for p in data.get('tariff_action', {}).get('products', [])
                if p.get('hts_code')
            ])[:5],  # Only first 5 codes
        }
        
        content = json.dumps(fuzzy_fields, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()
    
    def calculate_similarity(self, doc1: Dict, doc2: Dict) -> float:
        """Calculate similarity score between two documents"""
        score = 0.0
        weights = {
            'document_number': 0.4,
            'hts_codes': 0.3,
            'title': 0.2,
            'date': 0.1
        }
        
        # Document number match
        doc1_num = doc1.get('identifiers', {}).get('fr_document_number')
        doc2_num = doc2.get('identifiers', {}).get('fr_document_number')
        if doc1_num and doc2_num and doc1_num == doc2_num:
            score += weights['document_number']
        
        # HTS codes overlap
        hts1 = set(p.get('hts_code') for p in doc1.get('tariff_action', {}).get('products', []))
        hts2 = set(p.get('hts_code') for p in doc2.get('tariff_action', {}).get('products', []))
        if hts1 and hts2:
            overlap = len(hts1 & hts2) / len(hts1 | hts2)
            score += weights['hts_codes'] * overlap
        
        # Title similarity
        title1 = doc1.get('title', '')
        title2 = doc2.get('title', '')
        if title1 and title2:
            title_sim = SequenceMatcher(None, title1.lower(), title2.lower()).ratio()
            score += weights['title'] * title_sim
        
        # Date proximity
        date1 = doc1.get('publication_date')
        date2 = doc2.get('publication_date')
        if date1 == date2:
            score += weights['date']
        
        return score
    
    def is_duplicate(self, doc1: Dict, doc2: Dict) -> bool:
        """Check if two documents are duplicates"""
        similarity = self.calculate_similarity(doc1, doc2)
        return similarity >= self.similarity_threshold
    
    def find_duplicates(self, new_doc: Dict, existing_docs: List[Dict]) -> List[Dict]:
        """Find potential duplicates in existing documents"""
        duplicates = []
        
        for existing in existing_docs:
            similarity = self.calculate_similarity(new_doc, existing)
            if similarity >= self.similarity_threshold:
                duplicates.append({
                    'document': existing,
                    'similarity': similarity,
                    'hash': self.generate_hash(existing)
                })
        
        return sorted(duplicates, key=lambda x: x['similarity'], reverse=True)

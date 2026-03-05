import re
from typing import Dict, List, Optional


class FieldNormalizer:
    def __init__(self):
        self.country_codes = {
            'CHINA': 'CN', 'RUSSIA': 'RU', 'CANADA': 'CA', 'MEXICO': 'MX',
            'JAPAN': 'JP', 'KOREA': 'KR', 'GERMANY': 'DE', 'FRANCE': 'FR',
            'UNITED KINGDOM': 'GB', 'ITALY': 'IT', 'INDIA': 'IN', 'BRAZIL': 'BR'
        }
    
    def normalize_hts_code(self, code: str) -> Optional[str]:
        if not code:
            return None
        
        # Remove all non-digits
        digits = re.sub(r'\D', '', code)
        
        # Must be 10 digits
        if len(digits) == 10:
            return f"{digits[:4]}.{digits[4:6]}.{digits[6:]}"
        elif len(digits) == 6:
            return f"{digits[:4]}.{digits[4:6]}.0000"
        
        return None
    
    def normalize_country_code(self, country: str) -> Optional[str]:
        if not country:
            return None
        
        country_upper = country.strip().upper()
        
        # Already a 2-letter code
        if len(country_upper) == 2 and country_upper.isalpha():
            return country_upper
        
        # Look up full name
        return self.country_codes.get(country_upper)
    
    def normalize_text(self, text: str) -> str:
        if not text:
            return ""
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\-.,;:()\[\]\/]', '', text)
        
        return text.strip()
    
    def normalize_document(self, data: Dict) -> Dict:
        normalized = data.copy()
        
        # Normalize dates
        for date_field in ['publication_date', 'effective_date', 'expiration_date']:
            if date_field in normalized:
                from src.validators.date_validator import DateValidator
                validator = DateValidator()
                normalized[date_field] = validator.normalize_date(normalized[date_field])
        
        # Normalize tariff action
        if 'tariff_action' in normalized:
            action = normalized['tariff_action']
            
            # Normalize rate
            if 'rate_original' in action:
                from src.validators.rate_validator import RateValidator
                validator = RateValidator()
                rate_info = validator.validate_rate(action['rate_original'])
                action['rate_normalized'] = rate_info.get('normalized_value')
                action['rate_type'] = rate_info.get('rate_type')
            
            # Normalize products
            if 'products' in action:
                for product in action['products']:
                    if 'hts_code' in product:
                        product['hts_code'] = self.normalize_hts_code(product['hts_code'])
                    
                    if 'description' in product:
                        product['description'] = self.normalize_text(product['description'])
                    
                    if 'country_specific' in product:
                        product['country_specific'] = [
                            self.normalize_country_code(c) 
                            for c in product['country_specific']
                            if self.normalize_country_code(c)
                        ]
        
        # Normalize title
        if 'title' in normalized:
            normalized['title'] = self.normalize_text(normalized['title'])
        
        return normalized

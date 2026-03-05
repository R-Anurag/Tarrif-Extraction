import re
from typing import List, Dict, Set


class HTSExtractor:
    def __init__(self):
        # HTS code patterns
        self.patterns = [
            re.compile(r'\b(\d{4}\.\d{2}\.\d{4})\b'),  # Standard: 1234.56.7890
            re.compile(r'\b(\d{4}\.\d{2})\b'),          # Short: 1234.56
            re.compile(r'\b(\d{10})\b'),                # No dots: 1234567890
        ]
        
        # Rate patterns
        self.rate_patterns = [
            re.compile(r'(\d+(?:\.\d+)?)\s*%'),                    # 25%
            re.compile(r'\$(\d+(?:\.\d+)?)\s*per'),                # $5 per
            re.compile(r'(\d+(?:\.\d+)?)\s*cents?\s*per'),         # 10 cents per
        ]
    
    def extract_hts_codes(self, text: str) -> List[str]:
        codes = set()
        
        for pattern in self.patterns:
            matches = pattern.findall(text)
            codes.update(matches)
        
        # Normalize codes to standard format
        normalized = []
        for code in codes:
            normalized_code = self._normalize_hts_code(code)
            if normalized_code:
                normalized.append(normalized_code)
        
        return sorted(list(set(normalized)))
    
    def _normalize_hts_code(self, code: str) -> str:
        # Remove all non-digits
        digits = re.sub(r'\D', '', code)
        
        # Must be 10 digits
        if len(digits) == 10:
            return f"{digits[:4]}.{digits[4:6]}.{digits[6:]}"
        elif len(digits) == 6:
            # Short form, pad with zeros
            return f"{digits[:4]}.{digits[4:6]}.0000"
        
        return None
    
    def extract_tariff_rates(self, text: str) -> List[Dict]:
        rates = []
        
        for pattern in self.rate_patterns:
            matches = pattern.finditer(text)
            for match in matches:
                context_start = max(0, match.start() - 100)
                context_end = min(len(text), match.end() + 100)
                context = text[context_start:context_end]
                
                rates.append({
                    "rate_text": match.group(0),
                    "value": match.group(1),
                    "context": context.strip()
                })
        
        return rates
    
    def extract_from_tables(self, tables: List[List[List[str]]]) -> List[Dict]:
        products = []
        
        for table in tables:
            for row in table:
                hts_codes = []
                description = ""
                
                for cell in row:
                    # Check if cell contains HTS code
                    codes = self.extract_hts_codes(cell)
                    if codes:
                        hts_codes.extend(codes)
                    elif len(cell) > 10:  # Likely a description
                        description = cell
                
                if hts_codes:
                    products.append({
                        "hts_codes": hts_codes,
                        "description": description
                    })
        
        return products
    
    def extract_countries(self, text: str) -> List[str]:
        # Common country code patterns
        country_pattern = re.compile(r'\b([A-Z]{2})\b')
        
        # Common country codes in trade documents
        common_codes = {'CN', 'US', 'CA', 'MX', 'JP', 'KR', 'DE', 'GB', 'FR', 'IT', 'RU', 'IN', 'BR'}
        
        matches = country_pattern.findall(text)
        countries = [code for code in matches if code in common_codes]
        
        return list(set(countries))

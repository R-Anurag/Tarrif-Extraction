import re
from typing import Dict, Optional


class RateValidator:
    def __init__(self):
        self.rate_types = ["ad_valorem", "specific", "compound"]
        self.ad_valorem_pattern = re.compile(r'^(\d+(?:\.\d+)?)\s*%$')
        self.specific_pattern = re.compile(r'^\$?(\d+(?:\.\d+)?)\s*(?:per|/)', re.IGNORECASE)
        self.cents_pattern = re.compile(r'^(\d+(?:\.\d+)?)\s*cents?\s*(?:per|/)', re.IGNORECASE)
    
    def validate_rate(self, rate_str: str, rate_type: str = None) -> Dict:
        result = {
            "valid": False,
            "rate_type": None,
            "normalized_value": None,
            "errors": []
        }
        
        if not rate_str:
            result["errors"].append("Rate string is empty")
            return result
        
        # Try ad valorem (percentage)
        match = self.ad_valorem_pattern.match(rate_str.strip())
        if match:
            result["valid"] = True
            result["rate_type"] = "ad_valorem"
            result["normalized_value"] = float(match.group(1)) / 100
            return result
        
        # Try specific (dollar amount)
        match = self.specific_pattern.match(rate_str.strip())
        if match:
            result["valid"] = True
            result["rate_type"] = "specific"
            result["normalized_value"] = float(match.group(1))
            return result
        
        # Try cents
        match = self.cents_pattern.match(rate_str.strip())
        if match:
            result["valid"] = True
            result["rate_type"] = "specific"
            result["normalized_value"] = float(match.group(1)) / 100
            return result
        
        result["errors"].append(f"Unrecognized rate format: {rate_str}")
        return result
    
    def normalize_rate(self, rate_str: str) -> Optional[float]:
        validation = self.validate_rate(rate_str)
        return validation.get("normalized_value")

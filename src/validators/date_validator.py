from datetime import datetime
from typing import Dict, Optional, List
import re


class DateValidator:
    def __init__(self):
        self.date_formats = [
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%B %d, %Y",
            "%b %d, %Y",
            "%Y%m%d"
        ]
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        if not date_str:
            return None
        
        for fmt in self.date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        return None
    
    def validate_dates(self, data: Dict) -> Dict:
        result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        pub_date = self.parse_date(data.get("publication_date"))
        eff_date = self.parse_date(data.get("effective_date"))
        exp_date = self.parse_date(data.get("expiration_date"))
        
        # Check publication date exists
        if not pub_date:
            result["errors"].append("Missing or invalid publication_date")
            result["valid"] = False
        
        # Check effective_date >= publication_date
        if pub_date and eff_date:
            if eff_date < pub_date:
                result["errors"].append(
                    f"Effective date ({eff_date.date()}) before publication date ({pub_date.date()})"
                )
                result["valid"] = False
        
        # Check expiration_date > effective_date
        if eff_date and exp_date:
            if exp_date <= eff_date:
                result["warnings"].append(
                    f"Expiration date ({exp_date.date()}) not after effective date ({eff_date.date()})"
                )
        
        return result
    
    def normalize_date(self, date_str: str) -> Optional[str]:
        parsed = self.parse_date(date_str)
        return parsed.strftime("%Y-%m-%d") if parsed else None

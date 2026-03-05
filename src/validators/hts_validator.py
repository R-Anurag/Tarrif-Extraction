import re
from typing import Dict, List


class HTSValidator:
    def __init__(self):
        self.hts_pattern = re.compile(r'^\d{4}\.\d{2}\.\d{4}$')
        self.short_pattern = re.compile(r'^\d{4}\.\d{2}$')
    
    def validate_hts_code(self, code: str) -> Dict:
        result = {
            "code": code,
            "valid": False,
            "errors": []
        }
        
        # Check format
        if not self.hts_pattern.match(code):
            result["errors"].append("Invalid format. Expected: XXXX.XX.XXXX")
            return result
        
        # Check chapter (first 2 digits)
        chapter = int(code[:2])
        if chapter < 1 or chapter > 99:
            result["errors"].append(f"Invalid chapter: {chapter}. Must be 01-99")
            return result
        
        # Basic validation passed
        result["valid"] = True
        result["chapter"] = chapter
        result["heading"] = code[:4]
        result["subheading"] = code[:7]
        
        return result
    
    def validate_batch(self, codes: List[str]) -> Dict:
        results = {
            "total": len(codes),
            "valid": 0,
            "invalid": 0,
            "details": []
        }
        
        for code in codes:
            validation = self.validate_hts_code(code)
            results["details"].append(validation)
            
            if validation["valid"]:
                results["valid"] += 1
            else:
                results["invalid"] += 1
        
        return results
    
    def extract_chapter_info(self, code: str) -> Dict:
        if not self.hts_pattern.match(code):
            return None
        
        chapter = int(code[:2])
        
        # Basic chapter descriptions (simplified)
        chapter_descriptions = {
            1: "Live animals",
            72: "Iron and steel",
            73: "Articles of iron or steel",
            84: "Machinery and mechanical appliances",
            85: "Electrical machinery and equipment",
            87: "Vehicles",
        }
        
        return {
            "chapter": chapter,
            "description": chapter_descriptions.get(chapter, "Unknown")
        }

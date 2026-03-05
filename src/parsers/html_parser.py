from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import re


class HTMLParser:
    def __init__(self):
        self.hts_pattern = re.compile(r'\b\d{4}\.\d{2}\.\d{4}\b')
    
    def parse(self, html_content: str) -> Dict:
        soup = BeautifulSoup(html_content, 'lxml')
        
        return {
            "text": self._extract_text(soup),
            "tables": self._extract_tables(soup),
            "hts_codes": self._extract_hts_codes(soup),
        }
    
    def _extract_text(self, soup: BeautifulSoup) -> str:
        # Remove script and style elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer']):
            element.decompose()
        
        text = soup.get_text(separator=' ', strip=True)
        return ' '.join(text.split())
    
    def _extract_tables(self, soup: BeautifulSoup) -> List[List[str]]:
        tables = []
        for table in soup.find_all('table'):
            rows = []
            for tr in table.find_all('tr'):
                cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                if cells:
                    rows.append(cells)
            if rows:
                tables.append(rows)
        return tables
    
    def _extract_hts_codes(self, soup: BeautifulSoup) -> List[str]:
        text = self._extract_text(soup)
        matches = self.hts_pattern.findall(text)
        return list(set(matches))
    
    def extract_effective_date(self, html_content: str) -> Optional[str]:
        soup = BeautifulSoup(html_content, 'lxml')
        text = self._extract_text(soup)
        
        # Common patterns for effective dates
        patterns = [
            r'effective\s+(?:date|on)?\s*:?\s*(\w+\s+\d{1,2},?\s+\d{4})',
            r'shall\s+(?:take\s+effect|be\s+effective)\s+(?:on\s+)?(\w+\s+\d{1,2},?\s+\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None

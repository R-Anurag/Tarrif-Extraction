from src.connectors.base import BaseConnector
from typing import List, Dict
import feedparser
from datetime import datetime
import re


class CBPConnector(BaseConnector):
    def __init__(self):
        super().__init__("cbp_csms")
        # CBP CSMS messages are available through their website
        self.csms_url = "https://www.cbp.gov/trade/cargo-security/csms"
        self.base_url = "https://www.cbp.gov"
    
    def fetch_documents(self, days_back: int = 7) -> List[Dict]:
        documents = []
        
        try:
            # Add headers to avoid 406 error
            response = self.session.get(
                self.csms_url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                },
                timeout=30
            )
            
            if response.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Find CSMS message links
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    title = link.get_text(strip=True)
                    
                    if self._is_tariff_related(title) and 'csms' in href.lower():
                        full_url = self.base_url + href if href.startswith('/') else href
                        csms_number = self._extract_csms_number(title)
                        
                        documents.append({
                            'title': title,
                            'url': full_url,
                            'publication_date': None,
                            'summary': '',
                            'csms_number': csms_number,
                            'source': 'cbp_csms'
                        })
                        
                        if len(documents) >= 20:  # Limit to recent 20
                            break
        except Exception as e:
            print(f"CBP scraping error: {e}")
        
        return documents
    
    def _is_tariff_related(self, text: str) -> bool:
        keywords = ['tariff', 'section 301', 'section 232', 'duties', 'hts', 
                   'entry', 'import', 'trade remedy', 'antidumping', 'countervailing']
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in keywords)
    
    def _extract_csms_number(self, title: str) -> str:
        # CSMS messages typically have format like "CSMS #12345678"
        match = re.search(r'CSMS\s*#?(\d+)', title, re.IGNORECASE)
        return match.group(1) if match else None
    
    def _parse_date(self, date_str: str) -> str:
        if not date_str:
            return None
        try:
            dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
            return dt.strftime("%Y-%m-%d")
        except:
            return None
    
    def fetch_message_content(self, url: str) -> Dict:
        try:
            response = self._make_request(url)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Extract message content
            content = soup.find('div', class_='bulletin-content')
            if not content:
                content = soup.find('div', id='content')
            
            text = content.get_text(separator=' ', strip=True) if content else ""
            
            # Extract effective date from content
            effective_date = self._extract_effective_date(text)
            
            return {
                'text': text,
                'effective_date': effective_date,
                'html': response.text
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _extract_effective_date(self, text: str) -> str:
        patterns = [
            r'effective\s+(?:date\s+)?(?:is\s+)?(\w+\s+\d{1,2},?\s+\d{4})',
            r'effective\s+(\d{1,2}/\d{1,2}/\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def parse_document(self, raw_data: Dict) -> Dict:
        return {
            "source": "cbp_csms",
            "document_type": "CSMS Message",
            "title": raw_data.get("title"),
            "publication_date": raw_data.get("publication_date"),
            "identifiers": {
                "cbp_csms_number": raw_data.get("csms_number")
            },
            "source_url": raw_data.get("url"),
            "abstract": raw_data.get("summary"),
        }

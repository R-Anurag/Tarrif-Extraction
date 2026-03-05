from src.connectors.base import BaseConnector
from typing import List, Dict
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime


class USTRConnector(BaseConnector):
    def __init__(self):
        super().__init__("ustr")
        self.base_url = self.config['base_url']
        # USTR doesn't have a reliable RSS feed, use web scraping instead
        self.press_releases_url = f"{self.base_url}/about-us/policy-offices/press-office/press-releases"
    
    def fetch_documents(self, days_back: int = 7) -> List[Dict]:
        documents = []
        
        # Scrape press releases page
        try:
            response = self._make_request(self.press_releases_url)
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Find press release links
            for link in soup.find_all('a', href=True):
                href = link['href']
                title = link.get_text(strip=True)
                
                if self._is_tariff_related(title) and '/press-releases/' in href:
                    full_url = self.base_url + href if href.startswith('/') else href
                    documents.append({
                        'title': title,
                        'url': full_url,
                        'publication_date': None,  # Will extract from page
                        'summary': '',
                        'source': 'ustr'
                    })
                    
                    if len(documents) >= 20:  # Limit to recent 20
                        break
        except Exception as e:
            print(f"USTR scraping error: {e}")
        
        return documents
    
    def _is_tariff_related(self, text: str) -> bool:
        keywords = ['tariff', 'section 301', 'section 232', 'trade', 'duties', 
                   'import', 'exclusion', 'annex']
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in keywords)
    
    def _parse_date(self, date_str: str) -> str:
        if not date_str:
            return None
        try:
            dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
            return dt.strftime("%Y-%m-%d")
        except:
            return None
    
    def fetch_page_content(self, url: str) -> Dict:
        try:
            response = self._make_request(url)
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Extract main content
            content = soup.find('div', class_='field-item')
            if not content:
                content = soup.find('article')
            
            text = content.get_text(separator=' ', strip=True) if content else ""
            
            # Look for PDF attachments
            pdf_links = []
            for link in soup.find_all('a', href=True):
                if link['href'].endswith('.pdf'):
                    pdf_links.append(self.base_url + link['href'] if link['href'].startswith('/') else link['href'])
            
            return {
                'text': text,
                'pdf_links': pdf_links,
                'html': response.text
            }
        except Exception as e:
            return {'error': str(e)}
    
    def parse_document(self, raw_data: Dict) -> Dict:
        return {
            "source": "ustr",
            "document_type": "Press Release",
            "title": raw_data.get("title"),
            "publication_date": raw_data.get("publication_date"),
            "identifiers": {},
            "source_url": raw_data.get("url"),
            "abstract": raw_data.get("summary"),
        }

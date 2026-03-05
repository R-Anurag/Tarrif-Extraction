from src.connectors.base import BaseConnector
from typing import List, Dict
from datetime import datetime, timedelta


class FederalRegisterConnector(BaseConnector):
    def __init__(self):
        super().__init__("federal_register")
        self.api_base = self.config['base_url']
    
    def fetch_documents(self, days_back: int = 1, keywords: List[str] = None) -> List[Dict]:
        if keywords is None:
            keywords = ["tariff", "duties", "import", "section 301", "section 232", 
                       "trade remedy", "safeguard"]
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        documents = []
        for keyword in keywords:
            params = {
                "conditions[term]": keyword,
                "conditions[publication_date][gte]": start_date.strftime("%Y-%m-%d"),
                "conditions[publication_date][lte]": end_date.strftime("%Y-%m-%d"),
                "per_page": 100,
                "fields[]": ["document_number", "title", "publication_date", 
                            "html_url", "pdf_url", "abstract", "type",
                            "executive_order_number", "proclamation_number"]
            }
            
            response = self._make_request(f"{self.api_base}/documents.json", params)
            data = response.json()
            documents.extend(data.get("results", []))
        
        # Remove duplicates by document_number
        seen = set()
        unique_docs = []
        for doc in documents:
            doc_num = doc.get("document_number")
            if doc_num and doc_num not in seen:
                seen.add(doc_num)
                unique_docs.append(doc)
        
        return unique_docs
    
    def fetch_document_details(self, document_number: str) -> Dict:
        url = f"{self.api_base}/documents/{document_number}.json"
        response = self._make_request(url)
        return response.json()
    
    def download_html(self, html_url: str) -> str:
        response = self._make_request(html_url)
        return response.text
    
    def download_pdf(self, pdf_url: str) -> bytes:
        response = self._make_request(pdf_url)
        return response.content
    
    def parse_document(self, raw_data: Dict) -> Dict:
        return {
            "source": "federal_register",
            "document_type": raw_data.get("type", "Unknown"),
            "title": raw_data.get("title"),
            "publication_date": raw_data.get("publication_date"),
            "identifiers": {
                "fr_document_number": raw_data.get("document_number"),
                "proclamation_number": raw_data.get("proclamation_number"),
                "executive_order_number": raw_data.get("executive_order_number"),
            },
            "source_url": raw_data.get("html_url"),
            "pdf_url": raw_data.get("pdf_url"),
            "abstract": raw_data.get("abstract"),
        }

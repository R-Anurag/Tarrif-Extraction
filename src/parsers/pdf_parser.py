import pdfplumber
from typing import Dict, List, Optional
from pathlib import Path
import re


class PDFParser:
    def __init__(self):
        self.hts_pattern = re.compile(r'\b\d{4}\.\d{2}\.\d{4}\b')
    
    def parse(self, pdf_path: str) -> Dict:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = self._extract_text(pdf)
                tables = self._extract_tables(pdf)
                hts_codes = self._extract_hts_codes(text)
                
                return {
                    "text": text,
                    "tables": tables,
                    "hts_codes": hts_codes,
                    "page_count": len(pdf.pages),
                    "extraction_method": "pdfplumber"
                }
        except Exception as e:
            return {
                "error": str(e),
                "extraction_method": "failed"
            }
    
    def _extract_text(self, pdf) -> str:
        text_parts = []
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        return '\n'.join(text_parts)
    
    def _extract_tables(self, pdf) -> List[List[List[str]]]:
        all_tables = []
        for page in pdf.pages:
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    # Clean table data
                    cleaned = [[cell.strip() if cell else '' for cell in row] for row in table]
                    all_tables.append(cleaned)
        return all_tables
    
    def _extract_hts_codes(self, text: str) -> List[str]:
        matches = self.hts_pattern.findall(text)
        return list(set(matches))
    
    def extract_from_bytes(self, pdf_bytes: bytes) -> Dict:
        import io
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                text = self._extract_text(pdf)
                tables = self._extract_tables(pdf)
                hts_codes = self._extract_hts_codes(text)
                
                return {
                    "text": text,
                    "tables": tables,
                    "hts_codes": hts_codes,
                    "page_count": len(pdf.pages),
                    "extraction_method": "pdfplumber"
                }
        except Exception as e:
            return {
                "error": str(e),
                "extraction_method": "failed"
            }

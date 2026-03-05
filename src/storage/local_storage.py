from pathlib import Path
from typing import Optional
import hashlib
from datetime import datetime
from config.settings import STORAGE_CONFIG


class LocalStorage:
    def __init__(self):
        self.base_path = STORAGE_CONFIG['local_path']
        self.html_dir = STORAGE_CONFIG['html_dir']
        self.pdf_dir = STORAGE_CONFIG['pdf_dir']
        self.json_dir = STORAGE_CONFIG['json_dir']
        self._ensure_dirs()
    
    def _ensure_dirs(self):
        for dir_path in [self.html_dir, self.pdf_dir, self.json_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def _generate_filename(self, source: str, doc_id: str, extension: str) -> str:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"{source}_{doc_id}_{timestamp}.{extension}"
    
    def save_html(self, content: str, source: str, doc_id: str) -> str:
        filename = self._generate_filename(source, doc_id, "html")
        filepath = self.html_dir / filename
        filepath.write_text(content, encoding='utf-8')
        return str(filepath)
    
    def save_pdf(self, content: bytes, source: str, doc_id: str) -> str:
        filename = self._generate_filename(source, doc_id, "pdf")
        filepath = self.pdf_dir / filename
        filepath.write_bytes(content)
        return str(filepath)
    
    def save_json(self, content: str, source: str, doc_id: str) -> str:
        filename = self._generate_filename(source, doc_id, "json")
        filepath = self.json_dir / filename
        filepath.write_text(content, encoding='utf-8')
        return str(filepath)
    
    def read_file(self, filepath: str) -> Optional[bytes]:
        path = Path(filepath)
        if path.exists():
            return path.read_bytes()
        return None

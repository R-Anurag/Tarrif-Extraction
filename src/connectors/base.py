from abc import ABC, abstractmethod
import requests
from typing import Dict, Optional
import yaml
from pathlib import Path
from src.utils.rate_limiter import RateLimiter
from src.utils.retry import retry


class BaseConnector(ABC):
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.config = self._load_config()
        self.rate_limiter = RateLimiter(
            max_calls=self.config['rate_limit'],
            period=3600 if self.config['rate_limit'] > 200 else 60
        )
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'TariffExtractor/1.0'})
    
    def _load_config(self) -> Dict:
        config_path = Path(__file__).parent.parent.parent / "config" / "sources.yaml"
        with open(config_path) as f:
            sources = yaml.safe_load(f)
        return sources['sources'][self.source_name]
    
    @retry(max_attempts=3, delay=2.0, exceptions=(requests.RequestException,))
    def _make_request(self, url: str, params: Optional[Dict] = None) -> requests.Response:
        self.rate_limiter.wait_if_needed()
        response = self.session.get(
            url, 
            params=params, 
            timeout=self.config['timeout']
        )
        response.raise_for_status()
        return response
    
    @abstractmethod
    def fetch_documents(self, **kwargs):
        pass
    
    @abstractmethod
    def parse_document(self, raw_data):
        pass

import httpx
from typing import Dict, Any, Optional
from config import FIRECRAWL_API_KEY, JINA_API_KEY
from utils.logger import get_logger

logger = get_logger("fetcher")

class BaseFetcher:
    def fetch(self, url: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

class JinaFetcher(BaseFetcher):
    def fetch(self, url: str) -> Optional[Dict[str, Any]]:
        target = f"https://r.jina.ai/{url}"
        headers = {}
        if JINA_API_KEY:
            headers["Authorization"] = f"Bearer {JINA_API_KEY}"
            
        try:
            with httpx.Client() as client:
                response = client.get(target, headers=headers, timeout=20.0)
                response.raise_for_status()
                # Jina returns markdown as plain text
                markdown = response.text
                return {
                    "url": url,
                    "title": f"Jina Reader: {url}", # Jina doesn't return structured title easily in text response, usually it's in the text header
                    "markdown": markdown
                }
        except Exception as e:
            logger.error(f"JinaFetcher error for {url}: {e}")
            return None

class FirecrawlFetcher(BaseFetcher):
    def fetch(self, url: str) -> Optional[Dict[str, Any]]:
        target = "https://api.firecrawl.dev/v1/scrape"
        headers = {
            "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "url": url,
            "formats": ["markdown"]
        }
        
        try:
            with httpx.Client() as client:
                response = client.post(target, headers=headers, json=payload, timeout=30.0)
                response.raise_for_status()
                data = response.json()
                if data.get("success"):
                    doc = data.get("data", {})
                    metadata = doc.get("metadata", {})
                    return {
                        "url": url,
                        "title": metadata.get("title", url),
                        "markdown": doc.get("markdown", ""),
                        "published_date": metadata.get("published_date"),
                        "author": metadata.get("author"),
                        "domain": metadata.get("sourceURL")
                    }
                else:
                    logger.error(f"Firecrawl scrape failed for {url}")
                    return None
        except Exception as e:
            logger.error(f"FirecrawlFetcher error for {url}: {e}")
            return None

def get_fetcher() -> BaseFetcher:
    if FIRECRAWL_API_KEY and FIRECRAWL_API_KEY != "your_firecrawl_api_key_here":
        return FirecrawlFetcher()
    return JinaFetcher()

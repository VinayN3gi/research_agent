import httpx
import asyncio
from typing import Dict, Any, Optional
from config import FIRECRAWL_API_KEY, JINA_API_KEY
from utils.logger import get_logger
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

logger = get_logger("fetcher")

# Semaphore to limit concurrent page fetches
fetch_semaphore = asyncio.Semaphore(10)

class BaseFetcher:
    async def fetch(self, url: str, client: httpx.AsyncClient) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

class JinaFetcher(BaseFetcher):
    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        reraise=True
    )
    async def _do_fetch(self, url: str, client: httpx.AsyncClient) -> Optional[Dict[str, Any]]:
        target = f"https://r.jina.ai/{url}"
        headers = {}
        if JINA_API_KEY:
            headers["Authorization"] = f"Bearer {JINA_API_KEY}"
            
        async with fetch_semaphore:
            response = await client.get(target, headers=headers, timeout=20.0)
            response.raise_for_status()
            markdown = response.text
            return {
                "url": url,
                "title": f"Jina Reader: {url}",
                "markdown": markdown
            }

    async def fetch(self, url: str, client: httpx.AsyncClient) -> Optional[Dict[str, Any]]:
        try:
            return await self._do_fetch(url, client)
        except Exception as e:
            logger.error(f"JinaFetcher error for {url}: {e}")
            return None

class FirecrawlFetcher(BaseFetcher):
    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        reraise=True
    )
    async def _do_fetch(self, url: str, client: httpx.AsyncClient) -> Optional[Dict[str, Any]]:
        target = "https://api.firecrawl.dev/v1/scrape"
        headers = {
            "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "url": url,
            "formats": ["markdown"]
        }
        
        async with fetch_semaphore:
            response = await client.post(target, headers=headers, json=payload, timeout=30.0)
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
                raise Exception(f"Firecrawl scrape returned failure for {url}")

    async def fetch(self, url: str, client: httpx.AsyncClient) -> Optional[Dict[str, Any]]:
        try:
            return await self._do_fetch(url, client)
        except Exception as e:
            logger.error(f"FirecrawlFetcher error for {url}: {e}")
            return None

def get_fetcher() -> BaseFetcher:
    if FIRECRAWL_API_KEY and FIRECRAWL_API_KEY != "your_firecrawl_api_key_here":
        return FirecrawlFetcher()
    return JinaFetcher()

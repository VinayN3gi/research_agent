import asyncio
import httpx
from config import TAVILY_API_KEY
from utils.logger import get_logger
from cachetools import TTLCache
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

logger = get_logger("search")

# Global cache for search queries (lives in memory, expires after 1 hour)
search_cache = TTLCache(maxsize=1000, ttl=3600)

# Limit concurrent search requests
search_semaphore = asyncio.Semaphore(5)

@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(httpx.RequestError),
    reraise=True
)
async def _fetch_search(query: str, client: httpx.AsyncClient) -> list[str]:
    if query in search_cache:
        logger.info(f"Cache hit for query: {query}")
        return search_cache[query]

    async with search_semaphore:
        logger.info(f"Executing search for query: {query}")
        response = await client.post(
            "https://api.tavily.com/search",
            json={
                "api_key": TAVILY_API_KEY,
                "query": query,
                "search_depth": "basic",
                "max_results": 5
            },
            timeout=15.0
        )
        response.raise_for_status()
        data = response.json()
        
        urls = []
        for result in data.get("results", []):
            url = result.get("url")
            if url:
                urls.append(url)
                
        search_cache[query] = urls
        return urls

async def search(queries: list[str]) -> list[str]:
    logger.info(f"Searching... using {len(queries)} queries concurrently.")
    
    if not TAVILY_API_KEY or TAVILY_API_KEY == "your_tavily_api_key_here":
        logger.warning("No TAVILY_API_KEY set. Returning dummy URLs.")
        return ["https://example.com/dummy1", "https://example.com/dummy2"]

    unique_urls = set()
    
    async with httpx.AsyncClient() as client:
        tasks = []
        for q in queries:
            tasks.append(_fetch_search(q, client))
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to fetch search results for '{queries[idx]}': {result}")
            else:
                unique_urls.update(result)
    
    # Keep up to 20 URLs
    final_urls = list(unique_urls)[:20]
    logger.info(f"Searching... Found {len(final_urls)} unique URLs.")
    return final_urls

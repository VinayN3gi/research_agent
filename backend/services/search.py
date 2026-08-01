import httpx
from typing import List
from config import TAVILY_API_KEY
from utils.logger import get_logger

logger = get_logger("search")

def search(queries: List[str]) -> List[str]:
    logger.info(f"Searching... using {len(queries)} queries.")
    
    if not TAVILY_API_KEY or TAVILY_API_KEY == "your_tavily_api_key_here":
        logger.warning("No TAVILY_API_KEY set. Returning dummy URLs.")
        return ["https://example.com/dummy1", "https://example.com/dummy2"]

    unique_urls = set()
    
    # We will use httpx synchronously for Phase 1 to keep things simple
    # But ideally this would be async. Using sync client for now.
    with httpx.Client() as client:
        for q in queries:
            logger.info(f"Executing search for query: {q}")
            try:
                response = client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": TAVILY_API_KEY,
                        "query": q,
                        "search_depth": "basic",
                        "max_results": 5
                    },
                    timeout=15.0
                )
                response.raise_for_status()
                data = response.json()
                results = data.get("results", [])
                for result in results:
                    url = result.get("url")
                    if url:
                        unique_urls.add(url)
            except Exception as e:
                logger.error(f"Error fetching search results for '{q}': {e}")
    
    # Keep up to 20 URLs
    final_urls = list(unique_urls)[:20]
    logger.info(f"Searching... Found {len(final_urls)} unique URLs out of total raw results.")
    return final_urls

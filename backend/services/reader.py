from typing import List
from models import Source
from services.fetcher import get_fetcher
from utils.logger import get_logger

logger = get_logger("reader")

def read(urls: List[str]) -> List[Source]:
    logger.info(f"Reading... fetching {len(urls)} pages.")
    fetcher = get_fetcher()
    sources = []
    
    for url in urls:
        logger.info(f"Fetching URL: {url}")
        data = fetcher.fetch(url)
        if data and data.get("markdown"):
            source = Source(
                title=data.get("title", url),
                url=url,
                markdown=data.get("markdown", ""),
                published_date=data.get("published_date"),
                author=data.get("author"),
                domain=data.get("domain")
            )
            sources.append(source)
    
    logger.info(f"Reading... successfully fetched {len(sources)} pages.")
    return sources

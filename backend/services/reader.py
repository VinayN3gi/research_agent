from typing import List
from models import Source
from services.fetcher import get_fetcher
from utils.logger import get_logger

logger = get_logger("reader")

def evaluate_quality(domain: str, title: str) -> str:
    """A simple heuristic to guess source quality."""
    domain = (domain or "").lower()
    title = (title or "").lower()
    
    if "docs" in domain or "docs" in title or "documentation" in title:
        return "Official Docs"
    if "arxiv" in domain or "research" in title or ".edu" in domain:
        return "Research Paper"
    if "news" in domain or "times" in domain or "post" in domain:
        return "News"
    if "blog" in domain or "medium" in domain or "substack" in domain:
        return "Blog"
    
    return "Unknown"

def read(urls: List[str]) -> List[Source]:
    logger.info(f"Reading... fetching {len(urls)} pages.")
    fetcher = get_fetcher()
    sources = []
    
    for url in urls:
        logger.info(f"Fetching URL: {url}")
        data = fetcher.fetch(url)
        if data and data.get("markdown"):
            domain = data.get("domain", "")
            title = data.get("title", url)
            
            source = Source(
                title=title,
                url=url,
                markdown=data.get("markdown", ""),
                published_date=data.get("published_date"),
                author=data.get("author"),
                domain=domain,
                quality_score=evaluate_quality(domain, title)
            )
            sources.append(source)
    
    logger.info(f"Reading... successfully fetched {len(sources)} pages.")
    return sources

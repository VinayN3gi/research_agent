import asyncio
import httpx
from typing import Callable, Awaitable
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

QUALITY_SCORES = {
    "Official Docs": 100,
    "Research Paper": 90,
    "News": 70,
    "Blog": 50,
    "Unknown": 30
}

async def read(urls: list[str], on_progress: Callable[[int, int, str], Awaitable[None]] = None) -> list[Source]:
    logger.info(f"Reading... fetching {len(urls)} pages concurrently.")
    fetcher = get_fetcher()
    sources = []
    
    async with httpx.AsyncClient() as client:
        completed = 0
        async def fetch_with_progress(url, client):
            nonlocal completed
            res = await fetcher.fetch(url, client)
            completed += 1
            if on_progress:
                await on_progress(completed, len(urls), url)
            return res

        tasks = [fetch_with_progress(url, client) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for url, data in zip(urls, results):
            if isinstance(data, Exception) or data is None:
                logger.error(f"Failed to fetch {url}")
                continue
                
            if data.get("markdown"):
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
    # Source Ranking: Sort by our heuristic quality score (descending)
    sources.sort(key=lambda s: QUALITY_SCORES.get(s.quality_score, 0), reverse=True)
    
    logger.info(f"Reading... successfully fetched and ranked {len(sources)} pages.")
    return sources

import asyncio
from typing import Callable, Awaitable
from models import Source, ExtractionResult
from services import gemini
from utils.logger import get_logger

logger = get_logger("extractor")

async def extract_many(sources: list[Source], on_progress: Callable[[int, int, str], Awaitable[None]] = None) -> list[ExtractionResult]:
    logger.info(f"Extracting facts from {len(sources)} sources concurrently...")
    
    completed = 0
    async def extract_with_progress(source):
        nonlocal completed
        res = await gemini.extract_evidence(source)
        completed += 1
        if on_progress:
            await on_progress(completed, len(sources), source.domain)
        return res

    tasks = [extract_with_progress(source) for source in sources]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    valid_results = []
    for source, result in zip(sources, results):
        if isinstance(result, Exception):
            logger.error(f"Failed to extract from {source.url}: {result}")
            # Return empty result so we don't crash the whole run
            valid_results.append(ExtractionResult(facts=[], statistics=[], quotes=[]))
        else:
            logger.info(f"Extracted {len(result.facts)} facts, {len(result.statistics)} stats, {len(result.quotes)} quotes from {source.domain}")
            valid_results.append(result)
            
    return valid_results

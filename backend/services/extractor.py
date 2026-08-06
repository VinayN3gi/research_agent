import asyncio
from typing import Callable, Awaitable
from models import Document, ExtractionResult
from services import gemini
from utils.logger import get_logger

logger = get_logger("extractor")

async def extract_many(docs: list[Document], on_progress: Callable[[int, int, str], Awaitable[None]] = None) -> list[ExtractionResult]:
    logger.info(f"Extracting facts from {len(docs)} docs concurrently...")
    
    completed = 0
    async def extract_with_progress(doc):
        nonlocal completed
        res = await gemini.extract_evidence(doc)
        completed += 1
        if on_progress:
            await on_progress(completed, len(docs), doc.metadata.get("domain", doc.id))
        return res

    tasks = [extract_with_progress(doc) for doc in docs]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    valid_results = []
    for doc, result in zip(docs, results):
        if isinstance(result, Exception):
            logger.error(f"Failed to extract from {doc.id}: {result}")
            # Return empty result so we don't crash the whole run
            valid_results.append(ExtractionResult(facts=[], statistics=[], quotes=[]))
        else:
            logger.info(f"Extracted {len(result.facts)} facts, {len(result.statistics)} stats, {len(result.quotes)} quotes from {doc.id}")
            valid_results.append(result)
            
    return valid_results

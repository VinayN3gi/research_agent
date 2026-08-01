from typing import List
from models import Source
from services import gemini
from utils.logger import get_logger

logger = get_logger("writer")

MAX_CHARS = 50000

def format_sources(sources: List[Source]) -> str:
    formatted = []
    for i, source in enumerate(sources):
        idx = i + 1
        block = f"=========================\n"
        block += f"Source {idx}\n"
        block += f"Title: {source.title}\n"
        block += f"URL: {source.url}\n"
        if source.published_date:
            block += f"Published Date: {source.published_date}\n"
        if source.author:
            block += f"Author: {source.author}\n"
        block += f"Content:\n{source.markdown}\n"
        block += f"=========================\n"
        formatted.append(block)
    
    # Concatenate and cap
    full_text = "\n".join(formatted)
    if len(full_text) > MAX_CHARS:
        logger.warning(f"Context too large ({len(full_text)} chars). Truncating to {MAX_CHARS}.")
        full_text = full_text[:MAX_CHARS]
        
    return full_text

def write(query: str, sources: List[Source]) -> str:
    logger.info(f"Writing... formatting {len(sources)} sources for LLM context.")
    formatted_context = format_sources(sources)
    logger.info("Writing... calling LLM to generate report.")
    report = gemini.generate_report(query, formatted_context)
    logger.info("Writing... finished generating report.")
    return report

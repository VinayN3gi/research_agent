from models import Document, ExtractionResult
from providers.registry import registry
from utils.logger import get_logger

logger = get_logger("extractor")

async def extract_evidence(doc: Document) -> ExtractionResult:
    logger.info(f"Extracting evidence from: {doc.id}")
    provider = registry.get("gemini-flash")
    
    prompt = f"""You are a research extraction agent. Extract structured evidence from the following document content.
Limit your extraction to MAXIMUM 10 facts, 5 statistics, and 3 quotes to avoid flooding the knowledge base.

Document Title: {doc.title}
Source Type: {doc.source_type}
ID/URL: {doc.id}

Content:
{doc.text[:40000]}
"""
    result = await provider.structured(prompt, ExtractionResult)
    
    for fact in result.facts:
        fact.url = doc.id
        fact.page_title = doc.title
        if not fact.source:
            fact.source = doc.metadata.get("domain", doc.source_type)
            
    return result

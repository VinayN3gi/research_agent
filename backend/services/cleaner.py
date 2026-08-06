import json
from models import Evidence
from providers.registry import registry
from utils.logger import get_logger

logger = get_logger("cleaner")

async def deduplicate_claims(claims: list[Evidence]) -> list[Evidence]:
    if len(claims) <= 1:
        return claims
        
    logger.info(f"Semantically deduplicating {len(claims)} claims via LLM")
    provider = registry.get("gemini-flash")

    prompt = "You are a data cleaning assistant. Identify which facts are semantically identical (convey the exact same core information). Return a JSON array of integers representing the indices (0-indexed) of the UNIQUE facts we should keep. For example, if fact 0 and fact 2 mean the exact same thing, only include 0 in the list.\n\nFacts:\n"
    for idx, fact in enumerate(claims):
        prompt += f"[{idx}] {fact.statement}\n"

    try:
        from pydantic import BaseModel
        class IndicesList(BaseModel):
            indices: list[int]
            
        result = await provider.structured(prompt, IndicesList)
        unique_indices = result.indices
        
        unique_claims = [claims[i] for i in unique_indices if 0 <= i < len(claims)]
        logger.info(f"Deduplication reduced {len(claims)} to {len(unique_claims)} unique claims.")
        return unique_claims
    except Exception as e:
        logger.error(f"Error in cleaner deduplicate_claims: {e}")
        return claims

from models import Evidence
from services import gemini

async def deduplicate_facts(facts: list[Evidence]) -> list[Evidence]:
    """
    Deduplicates a list of Evidence objects based on exact string match of the statement,
    followed by an LLM-based semantic deduplication.
    """
    seen = set()
    unique_facts_string = []
    
    for fact in facts:
        # Normalize slightly for better matching
        normalized = fact.statement.strip().lower()
        if normalized not in seen:
            seen.add(normalized)
            unique_facts_string.append(fact)
            
    # Then use LLM for semantic dedup
    return await gemini.deduplicate_claims(unique_facts_string)

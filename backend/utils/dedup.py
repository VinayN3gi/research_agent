from typing import List
from models import Evidence

def deduplicate_facts(facts: List[Evidence]) -> List[Evidence]:
    """
    Deduplicates a list of Evidence objects based on exact string match of the statement.
    """
    seen = set()
    unique_facts = []
    
    for fact in facts:
        # Normalize slightly for better matching
        normalized = fact.statement.strip().lower()
        if normalized not in seen:
            seen.add(normalized)
            unique_facts.append(fact)
            
    return unique_facts

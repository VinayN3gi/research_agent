from models import KnowledgeBase, ReflectionResult
from providers.registry import registry
from utils.logger import get_logger

logger = get_logger("reflector")

async def reflect(goal: str, success_criteria: list[str], kb: KnowledgeBase, iterations: int) -> ReflectionResult:
    logger.info(f"Reflecting on knowledge base (Iteration {iterations})")
    # Reflection is complex, we use gemini-pro if available, else flash
    try:
        provider = registry.get("gemini-pro")
    except ValueError:
        provider = registry.get("gemini-flash")
    
    prompt = f"""You are a research Reflection Agent. Evaluate if we have enough information to fulfill the research goal.

Goal: {goal}
Success Criteria: {success_criteria}
Iterations Completed: {iterations}

Current Knowledge Summary:
Total Sources Read: {len(kb.sources)}
Total Facts: {len(kb.claims)}
Total Statistics: {len(kb.statistics)}
Total Quotes: {len(kb.quotes)}

Evaluate if the gathered knowledge is sufficient to meet ALL success criteria.
If missing information, list specific missing topics (e.g. "Pricing details", "Performance benchmarks"). Do NOT generate search queries, just the missing topics.
"""
    return await provider.structured(prompt, ReflectionResult)

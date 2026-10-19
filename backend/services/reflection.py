from models import ReflectionResult, KnowledgeBase
from services import reflector
from utils.logger import get_logger

logger = get_logger("reflection")

async def reflect(goal: str, success_criteria: list[str], kb: KnowledgeBase, iterations: int) -> ReflectionResult:
    logger.info(f"Reflecting on gathered knowledge (Iteration {iterations}).")
    result = await reflector.reflect(goal, success_criteria, kb, iterations)
    return result


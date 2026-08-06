from models import ReflectionResult, KnowledgeBase
from services import gemini
from utils.logger import get_logger

logger = get_logger("reflection")

async def reflect(goal: str, success_criteria: list[str], kb: KnowledgeBase, iterations: int) -> ReflectionResult:
    logger.info(f"Reflecting on gathered knowledge (Iteration {iterations}).")
    result = await gemini.reflect(goal, success_criteria, kb, iterations)
    logger.info(f"Enough information? {result.enough_information}")
    if not result.enough_information:
        logger.info(f"Missing topics: {result.missing_topics}")
    return result

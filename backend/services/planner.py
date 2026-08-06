from models import ResearchPlan, PlannerTask
from services import gemini
from utils.logger import get_logger

logger = get_logger("planner")

async def create_plan(query: str, existing_kb=None) -> ResearchPlan:
    logger.info(f"Delegating plan generation to Gemini for: {query}")
    plan = await gemini.generate_plan(query, existing_kb)
    logger.info(f"Generated {len(plan.tasks)} initial tasks and {len(plan.sections)} sections.")
    return plan

async def create_followup_queries(missing_topics: list[str]) -> list[PlannerTask]:
    logger.info(f"Planning... creating followup tasks for missing topics.")
    queries = await gemini.generate_followup_plan(missing_topics)
    logger.info(f"Generated {len(queries)} followup tasks.")
    return queries

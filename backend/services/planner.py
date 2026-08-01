from models import PlannerResponse
from services import gemini
from utils.logger import get_logger

logger = get_logger("planner")

def create_plan(query: str) -> PlannerResponse:
    logger.info(f"Planning... creating plan for query: {query}")
    plan = gemini.generate_plan(query)
    logger.info(f"Generated {len(plan.queries)} queries.")
    return plan

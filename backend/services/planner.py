from typing import List
from models import ResearchPlan
from services import gemini
from utils.logger import get_logger

logger = get_logger("planner")

def create_plan(query: str) -> ResearchPlan:
    logger.info(f"Planning... creating plan for query: {query}")
    plan = gemini.generate_plan(query)
    logger.info(f"Generated {len(plan.queries)} initial queries and {len(plan.sections)} sections.")
    return plan

def create_followup_queries(missing_topics: List[str]) -> List[str]:
    logger.info(f"Planning... creating followup queries for missing topics.")
    queries = gemini.generate_followup_plan(missing_topics)
    logger.info(f"Generated {len(queries)} followup queries.")
    return queries

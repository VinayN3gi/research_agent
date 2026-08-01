from models import ResearchPlan, KnowledgeBase
from services import gemini
from utils.logger import get_logger

logger = get_logger("writer")

def write(plan: ResearchPlan, kb: KnowledgeBase) -> str:
    logger.info("Writing... formatting knowledge base for LLM.")
    # gemini.py already handles the formatting logic for the final report
    report = gemini.generate_report(plan, kb)
    logger.info("Writing... finished generating report.")
    return report

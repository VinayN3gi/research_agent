from models import ResearchPlan, KnowledgeBase
from services import gemini
from utils.logger import get_logger

logger = get_logger("writer")

async def write(plan: ResearchPlan, kb: KnowledgeBase, template_type: str = "General Report", feedback: str = None) -> str:
    logger.info("Writing... formatting knowledge base for LLM.")
    # LLM generates the report with inline [ID] citations
    report = await gemini.generate_report(plan, kb, template_type, feedback)
    
    # Inverted Citation Engine: Append markdown reference links
    logger.info("Writing... appending inverted citations.")
    references = "\n\n## References\n"
    for i, url in enumerate(kb.sources):
        # By appending [1]: url, markdown parsers automatically turn [1] into a link
        references += f"[{i+1}]: {url}\n"
        
    final_report = report + references
    logger.info("Writing... finished generating report.")
    return final_report

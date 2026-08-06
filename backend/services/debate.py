from pydantic import BaseModel
from providers.registry import registry
from models import ResearchPlan, KnowledgeBase
from utils.logger import get_logger

logger = get_logger("debate")

class DebateFeedback(BaseModel):
    pass_validation: bool
    feedback: str

async def evidence_validator(report: str, kb: KnowledgeBase) -> DebateFeedback:
    logger.info("Debate: Evidence Validator analyzing report...")
    provider = registry.get("gemini-pro")
    prompt = f"""You are the Evidence Validator.
Your job is to ensure the report ONLY uses facts that exist in the provided Knowledge Base.
Report:
{report}

Knowledge Base Facts:
{str([f.statement for f in kb.claims])[:10000]}

If the report invents facts not present in the Knowledge Base, set pass_validation to false and explain exactly what was hallucinated.
Otherwise, set pass_validation to true and feedback to "All evidence verified."
"""
    return await provider.structured(prompt, DebateFeedback)

async def critic(report: str, plan: ResearchPlan) -> DebateFeedback:
    logger.info("Debate: Critic analyzing report...")
    provider = registry.get("gemini-pro")
    prompt = f"""You are the Critic.
Evaluate if this report strictly answers the goal: {plan.goal}
Report:
{report}

Be extremely harsh. If it deviates, is fluffy, or misses key sections ({plan.sections}), set pass_validation to false and provide feedback.
Otherwise, pass_validation=true.
"""
    return await provider.structured(prompt, DebateFeedback)

async def fact_checker(report: str) -> DebateFeedback:
    logger.info("Debate: Fact Checker analyzing report...")
    provider = registry.get("gemini-flash")
    prompt = f"""You are the Fact Checker.
Check the internal logic and math in this report.
Report:
{report}

If there are logical contradictions or obvious mathematical errors, set pass_validation to false and explain.
Otherwise, pass_validation=true.
"""
    return await provider.structured(prompt, DebateFeedback)

async def editor(report: str, feedback_history: list[str]) -> str:
    logger.info("Debate: Editor rewriting report based on feedback...")
    provider = registry.get("gemini-pro")
    
    feedback_str = "\n".join(feedback_history)
    prompt = f"""You are the Final Editor.
You must rewrite the following report to fix ALL the listed feedback from the Review Board.
Maintain the original Markdown structure and citations, just fix the errors.

Original Report:
{report}

Critical Feedback to Fix:
{feedback_str}

Return ONLY the rewritten Markdown report.
"""
    return await provider.generate(prompt)

from pydantic import BaseModel
from models import ResearchPlan, PlannerTask
from providers.registry import registry
from memory.agent_memory import memory
from utils.logger import get_logger

logger = get_logger("planner")

async def create_plan(query: str, existing_kb=None) -> ResearchPlan:
    logger.info(f"Delegating plan generation to LLM for: {query}")
    
    # Use flash model for fast planning
    provider = registry.get("gemini-flash")
    
    context_addon = ""
    if existing_kb and existing_kb.claims:
        context_addon = "You are continuing a research project. The following facts are already known, DO NOT plan tasks to search for this information again:\n"
        for idx, claim in enumerate(existing_kb.claims[:50]):
            context_addon += f"- {claim.statement}\n"
            
    # Pull Agent Memory for this topic
    recommended_tools = memory.get_recommended_tools(query)
    memory_addon = f"\nSystem Memory implies these tools are most effective for this topic domain (ranked best to worst): {recommended_tools}\n"

    prompt = f"""Generate a deep research plan for this topic: '{query}'. Provide a clear goal, a list of target sections for the final report, exactly 5 distinct tasks to begin with, and a list of success criteria.
Each task must specify a 'tool' (e.g., 'web_search') and a 'query' for that tool.
{memory_addon}
{context_addon}"""

    plan = await provider.structured(prompt, ResearchPlan)
    logger.info(f"Generated {len(plan.tasks)} initial tasks and {len(plan.sections)} sections.")
    return plan

async def create_followup_queries(missing_topics: list[str]) -> list[PlannerTask]:
    logger.info(f"Planning... creating followup tasks for missing topics.")
    
    provider = registry.get("gemini-flash")
    
    prompt = f"""Based on these missing research topics: {missing_topics}, generate exactly 3-5 highly targeted tasks to find this specific information. Each task must have a 'tool' (e.g., 'web_search') and a 'query'.
Return a JSON array of these task objects."""

    class FollowupPlan(BaseModel):
        tasks: list[PlannerTask]

    plan = await provider.structured(prompt, FollowupPlan)
    logger.info(f"Generated {len(plan.tasks)} followup tasks.")
    return plan.tasks

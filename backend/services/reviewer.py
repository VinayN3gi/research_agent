from pydantic import BaseModel
from models import ResearchPlan
from services.gemini import get_client, MODEL_NAME, gemini_semaphore
from utils.logger import get_logger
from tenacity import retry, wait_exponential, stop_after_attempt
from google.genai import types

logger = get_logger("reviewer")

class ReviewResult(BaseModel):
    pass_review: bool
    feedback: str

@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3), reraise=True)
async def review_report(report: str, plan: ResearchPlan) -> ReviewResult:
    logger.info("Reviewing report...")
    client = get_client()
    if not client:
        return ReviewResult(pass_review=True, feedback="Missing API key.")
        
    prompt = f"""You are an expert AI Report Reviewer.
Evaluate the following draft report against the original research goal and target sections.

Goal: {plan.goal}
Target Sections: {plan.sections}
Success Criteria: {plan.success_criteria}

Draft Report:
{report}

Does the report fully address the goal, cover all target sections, and cite its claims?
If it does, set pass_review to true.
If it is missing critical information, lacks depth, or fails to cover a required section, set pass_review to false and provide specific feedback on what must be improved in the rewrite.
"""
    async with gemini_semaphore:
        try:
            response = await client.aio.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ReviewResult,
                    temperature=0.1
                ),
            )
            return ReviewResult.model_validate_json(response.text)
        except Exception as e:
            logger.error(f"Error in review_report: {e}")
            raise

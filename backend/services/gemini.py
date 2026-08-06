import os
import json
import asyncio
from google import genai
from google.genai import types
from models import ResearchPlan, ExtractionResult, ReflectionResult, KnowledgeBase, Document, Evidence, PlannerTask
from config import GEMINI_API_KEY
from utils.logger import get_logger
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

logger = get_logger("gemini")

# Fast and reliable model
MODEL_NAME = 'gemini-3.1-flash-lite'

# Semaphore to limit concurrent Gemini API calls
gemini_semaphore = asyncio.Semaphore(10)

def get_client():
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        logger.error("GEMINI_API_KEY is not set or is dummy.")
        return None
    return genai.Client(api_key=GEMINI_API_KEY)

@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3), reraise=True)
async def generate_plan(query: str, existing_kb: KnowledgeBase = None) -> ResearchPlan:
    logger.info(f"Generating plan for query: {query}")
    client = get_client()
    
    if not client:
        return ResearchPlan(
            goal=f"Research about {query}",
            sections=["Introduction", "Details"],
            tasks=[PlannerTask(tool="web_search", query=f"{query} details")],
            success_criteria=["Find basic info"]
        )

    context_addon = ""
    if existing_kb and existing_kb.claims:
        context_addon = "You are continuing a research project. The following facts are already known, DO NOT plan tasks to search for this information again:\n"
        for idx, claim in enumerate(existing_kb.claims[:50]):
            context_addon += f"- {claim.statement}\n"

    prompt = f"""Generate a deep research plan for this topic: '{query}'. Provide a clear goal, a list of target sections for the final report, exactly 5 distinct tasks to begin with, and a list of success criteria.
Each task must specify a 'tool' (e.g., 'web_search') and a 'query' for that tool.

{context_addon}"""

    async with gemini_semaphore:
        try:
            response = await client.aio.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ResearchPlan,
                    temperature=0.7
                ),
            )
            return ResearchPlan.model_validate_json(response.text)
        except Exception as e:
            logger.error(f"Error in Gemini generate_plan: {e}")
            raise

@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3), reraise=True)
async def generate_followup_plan(missing_topics: list[str]) -> list[PlannerTask]:
    logger.info(f"Generating followup queries for missing topics: {missing_topics}")
    client = get_client()
    if not client:
        return [PlannerTask(tool="web_search", query=topic) for topic in missing_topics]

    prompt = f"""Based on these missing research topics: {missing_topics}, generate exactly 3-5 highly targeted tasks to find this specific information. Each task must have a 'tool' (e.g., 'web_search') and a 'query'.
Return a JSON array of these task objects."""

    from pydantic import BaseModel
    class FollowupPlan(BaseModel):
        tasks: list[PlannerTask]

    async with gemini_semaphore:
        try:
            response = await client.aio.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=FollowupPlan,
                    temperature=0.7
                ),
            )
            data = FollowupPlan.model_validate_json(response.text)
            return data.tasks
        except Exception as e:
            logger.error(f"Error in Gemini generate_followup_plan: {e}")
            raise

@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3), reraise=True)
async def extract_evidence(doc: Document) -> ExtractionResult:
    logger.info(f"Extracting evidence from: {doc.id}")
    client = get_client()
    
    if not client:
        return ExtractionResult(facts=[], statistics=[], quotes=[])

    prompt = f"""You are a research extraction agent. Extract structured evidence from the following document content.
Limit your extraction to MAXIMUM 10 facts, 5 statistics, and 3 quotes to avoid flooding the knowledge base.

Document Title: {doc.title}
Source Type: {doc.source_type}
ID/URL: {doc.id}

Content:
{doc.text[:40000]} # Cap text to avoid extreme context sizes on a single page
"""
    async with gemini_semaphore:
        try:
            response = await client.aio.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ExtractionResult,
                    temperature=0.1
                ),
            )
            result = ExtractionResult.model_validate_json(response.text)
            for fact in result.facts:
                fact.url = doc.id
                fact.page_title = doc.title
                if not fact.source:
                    fact.source = doc.metadata.get("domain", doc.source_type)
            return result
        except Exception as e:
            logger.error(f"Error in Gemini extract_evidence for {doc.id}: {e}")
            raise

@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3), reraise=True)
async def reflect(goal: str, success_criteria: list[str], kb: KnowledgeBase, iterations: int) -> ReflectionResult:
    logger.info(f"Reflecting on knowledge base (Iteration {iterations})")
    client = get_client()
    
    if not client:
        return ReflectionResult(enough_information=True, missing_topics=[])

    prompt = f"""You are a research Reflection Agent. Evaluate if we have enough information to fulfill the research goal.

Goal: {goal}
Success Criteria: {success_criteria}
Iterations Completed: {iterations}

Current Knowledge Summary:
Total Sources Read: {len(kb.sources)}
Total Facts: {len(kb.claims)}
Total Statistics: {len(kb.statistics)}
Total Quotes: {len(kb.quotes)}

Evaluate if the gathered knowledge is sufficient to meet ALL success criteria.
If missing information, list specific missing topics (e.g. "Pricing details", "Performance benchmarks"). Do NOT generate search queries, just the missing topics.
"""
    async with gemini_semaphore:
        try:
            response = await client.aio.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ReflectionResult,
                    temperature=0.3
                ),
            )
            return ReflectionResult.model_validate_json(response.text)
        except Exception as e:
            logger.error(f"Error in Gemini reflect: {e}")
            raise

@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3), reraise=True)
async def generate_report(plan: ResearchPlan, kb: KnowledgeBase, template_type: str = "General Report", feedback: str = None) -> str:
    logger.info("Generating final report from Knowledge Base")
    client = get_client()
    
    if not client:
        return f"# Dummy Report for {plan.goal}\n\nMissing API key."

    source_map = {url: i+1 for i, url in enumerate(kb.sources)}

    formatted_claims = "\n".join([f"- {f.statement} (Source ID: [{source_map.get(f.url, 0)}])" for f in kb.claims])
    formatted_stats = "\n".join([f"- {s}" for s in kb.statistics])
    formatted_quotes = "\n".join([f"- {q}" for q in kb.quotes])

    prompt = f"""You are a deep research expert. Write a detailed, comprehensive report.
Template Style: {template_type}

Goal: {plan.goal}
Target Sections: {plan.sections}

Use ONLY the following structured evidence to write the report. NEVER invent information.
Mention conflicting evidence if any exists. Mention missing information if relevant.
Cite your sources clearly using the provided Source IDs like this: [1] or [2, 3].

=== FACTS & CLAIMS ===
{formatted_claims}

=== STATISTICS ===
{formatted_stats}

=== QUOTES ===
{formatted_quotes}

Return ONLY Markdown text. Do NOT add a References or Bibliography section yourself, it will be generated automatically.

If you are presenting comparisons, trends, or structured numeric data, you MUST include a JSON chart representation wrapped in triple backticks with the language "chart".
Format exactly like this:
```chart
{
  "chart": {
    "type": "bar",
    "title": "Chart Title",
    "labels": ["Item A", "Item B"],
    "values": [10, 20]
  }
}
```
Supported types are: "bar", "line", "pie".
"""
    if feedback:
        prompt += f"\n\nPREVIOUS REVIEW FEEDBACK TO FIX IN THIS REWRITE:\n{feedback}\n"

    async with gemini_semaphore:
        try:
            response = await client.aio.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2
                )
            )
            return response.text
        except Exception as e:
            logger.error(f"Error in Gemini generate_report: {e}")
            raise

@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3), reraise=True)
async def deduplicate_claims(claims: list[Evidence]) -> list[Evidence]:
    if len(claims) <= 1:
        return claims
        
    logger.info(f"Semantically deduplicating {len(claims)} claims via Gemini")
    client = get_client()
    if not client:
        return claims

    prompt = "You are a data cleaning assistant. Identify which facts are semantically identical (convey the exact same core information). Return a JSON array of integers representing the indices (0-indexed) of the UNIQUE facts we should keep. For example, if fact 0 and fact 2 mean the exact same thing, only include 0 in the list.\n\nFacts:\n"
    for idx, fact in enumerate(claims):
        prompt += f"[{idx}] {fact.statement}\n"

    async with gemini_semaphore:
        try:
            response = await client.aio.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                ),
            )
            unique_indices = json.loads(response.text)
            if isinstance(unique_indices, list) and all(isinstance(x, int) for x in unique_indices):
                unique_claims = [claims[i] for i in unique_indices if 0 <= i < len(claims)]
                logger.info(f"Deduplication reduced {len(claims)} to {len(unique_claims)} unique claims.")
                return unique_claims
            return claims
        except Exception as e:
            logger.error(f"Error in Gemini deduplicate_claims: {e}")
            return claims


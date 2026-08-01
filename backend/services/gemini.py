import os
import json
from google import genai
from google.genai import types
from models import ResearchPlan, ExtractionResult, ReflectionResult, KnowledgeBase, Source
from config import GEMINI_API_KEY
from utils.logger import get_logger

logger = get_logger("gemini")

# Fast and reliable model
MODEL_NAME = 'gemini-3.1-flash-lite'

def get_client():
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        logger.error("GEMINI_API_KEY is not set or is dummy.")
        return None
    return genai.Client(api_key=GEMINI_API_KEY)

def generate_plan(query: str) -> ResearchPlan:
    logger.info(f"Generating plan for query: {query}")
    client = get_client()
    
    if not client:
        return ResearchPlan(
            goal=f"Research about {query}",
            sections=["Introduction", "Details"],
            queries=[f"{query} details"],
            success_criteria=["Find basic info"]
        )

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=f"Generate a deep research plan for this topic: '{query}'. Provide a clear goal, a list of target sections for the final report, exactly 5 distinct search queries to begin with, and a list of success criteria.",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ResearchPlan,
                temperature=0.7
            ),
        )
        return ResearchPlan.model_validate_json(response.text)
    except Exception as e:
        logger.error(f"Error in Gemini generate_plan: {e}")
        return ResearchPlan(goal=query, sections=[], queries=[query], success_criteria=[])

def generate_followup_plan(missing_topics: list[str]) -> list[str]:
    logger.info(f"Generating followup queries for missing topics: {missing_topics}")
    client = get_client()
    if not client:
        return missing_topics

    try:
        # Prompt LLM to return list of strings
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=f"Based on these missing research topics: {missing_topics}, generate exactly 3-5 highly targeted web search queries to find this specific information. Return a JSON array of strings.",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                # The SDK expects a schema, we can just define a list of strings
                temperature=0.7
            ),
        )
        # Parse JSON array manually since we didn't pass a Pydantic schema
        queries = json.loads(response.text)
        if isinstance(queries, list):
            return queries
        return missing_topics
    except Exception as e:
        logger.error(f"Error in Gemini generate_followup_plan: {e}")
        return missing_topics

def extract_evidence(source: Source) -> ExtractionResult:
    logger.info(f"Extracting evidence from: {source.url}")
    client = get_client()
    
    if not client:
        return ExtractionResult(facts=[], statistics=[], quotes=[])

    prompt = f"""You are a research extraction agent. Extract structured evidence from the following webpage content.
Limit your extraction to MAXIMUM 10 facts, 5 statistics, and 3 quotes to avoid flooding the knowledge base.

Page Title: {source.title}
URL: {source.url}
Domain: {source.domain}

Content:
{source.markdown[:40000]} # Cap text to avoid extreme context sizes on a single page
"""
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ExtractionResult,
                temperature=0.1
            ),
        )
        result = ExtractionResult.model_validate_json(response.text)
        # Inject source metadata into Evidence objects (since LLM might miss it)
        for fact in result.facts:
            fact.url = source.url
            fact.page_title = source.title
            if not fact.source:
                fact.source = source.domain or source.url
        return result
    except Exception as e:
        logger.error(f"Error in Gemini extract_evidence for {source.url}: {e}")
        return ExtractionResult(facts=[], statistics=[], quotes=[])

def reflect(goal: str, success_criteria: list[str], kb: KnowledgeBase, iterations: int) -> ReflectionResult:
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
    try:
        response = client.models.generate_content(
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
        return ReflectionResult(enough_information=True, missing_topics=[])

def generate_report(plan: ResearchPlan, kb: KnowledgeBase) -> str:
    logger.info("Generating final report from Knowledge Base")
    client = get_client()
    
    if not client:
        return f"# Dummy Report for {plan.goal}\n\nMissing API key."

    # Format KB claims
    formatted_claims = "\n".join([f"- {f.statement} (Source: {f.page_title} - {f.url})" for f in kb.claims])
    formatted_stats = "\n".join([f"- {s}" for s in kb.statistics])
    formatted_quotes = "\n".join([f"- {q}" for q in kb.quotes])

    prompt = f"""You are a deep research expert. Write a detailed, comprehensive report.

Goal: {plan.goal}
Target Sections: {plan.sections}

Use ONLY the following structured evidence to write the report. NEVER invent information.
Mention conflicting evidence if any exists. Mention missing information if relevant.
Cite your sources clearly using the provided Source Titles and URLs.

=== FACTS & CLAIMS ===
{formatted_claims}

=== STATISTICS ===
{formatted_stats}

=== QUOTES ===
{formatted_quotes}

Return ONLY Markdown text.
"""
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2
            )
        )
        return response.text
    except Exception as e:
        logger.error(f"Error in Gemini generate_report: {e}")
        return f"# Error Generating Report\n\n{e}"

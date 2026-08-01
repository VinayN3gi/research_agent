import os
from google import genai
from google.genai import types
from models import PlannerResponse
from config import GEMINI_API_KEY
from utils.logger import get_logger

logger = get_logger("gemini")

def get_client():
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        logger.error("GEMINI_API_KEY is not set or is dummy.")
        # Returning None so the caller can mock if needed, or error out
        return None
    return genai.Client(api_key=GEMINI_API_KEY)

def generate_plan(query: str) -> PlannerResponse:
    logger.info(f"Generating plan for query: {query}")
    client = get_client()
    
    if not client:
        # Fallback to dummy data for Phase 1 testing
        logger.warning("No Gemini Client, returning dummy plan")
        return PlannerResponse(
            goal=f"Research about {query}",
            queries=[f"{query} features", f"{query} comparisons", f"{query} documentation"]
        )

    # Note: Using gemini-3.1-flash-lite as the fast reliable model
    try:
        response = client.models.generate_content(
            model='gemini-3.1-flash-lite',
            contents=f"Generate a research goal and exactly 5 distinct search queries for this topic: {query}",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=PlannerResponse,
                temperature=0.7
            ),
        )
        return PlannerResponse.model_validate_json(response.text)
    except Exception as e:
        logger.error(f"Error in Gemini generate_plan: {e}")
        return PlannerResponse(
            goal=f"Fallback plan for {query}",
            queries=[f"{query} general info"]
        )

def generate_report(query: str, formatted_context: str) -> str:
    logger.info(f"Generating report for query: {query}")
    client = get_client()
    
    if not client:
        # Fallback dummy report
        logger.warning("No Gemini Client, returning dummy report")
        return f"# Dummy Report for {query}\n\nThis is a generated dummy report because API key is missing."

    prompt = f"""You are a deep research expert. Write a detailed, comprehensive report on the topic: '{query}'.

Use ONLY the following sources to write the report.
Mention every source provided. Cite them clearly.

Sources:
{formatted_context}

Return ONLY Markdown text.
"""
    try:
        response = client.models.generate_content(
            model='gemini-3.1-flash-lite',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2
            )
        )
        return response.text
    except Exception as e:
        logger.error(f"Error in Gemini generate_report: {e}")
        return f"# Error Generating Report\n\nThere was an error communicating with the LLM: {e}"

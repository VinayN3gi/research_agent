from database.connection import get_db
from repositories.evidence_repository import EvidenceRepository
from services.gemini import get_client, MODEL_NAME, gemini_semaphore
from google.genai import types
from utils.logger import get_logger

logger = get_logger("chat")

async def get_chat_response(project_id: str, message: str) -> str:
    db = next(get_db())
    evidence_repo = EvidenceRepository(db)
    
    # Gather all evidence for project
    all_evidence = evidence_repo.get_by_project(project_id)
    if not all_evidence:
        return "I don't have any evidence extracted for this project yet."
        
    # Gather unique categories and topics
    categories = list(set([e.category for e in all_evidence if e.category]))
    
    # Step 1: Query Router / Classifier
    client = get_client()
    if not client:
        return "API Key missing."
        
    router_prompt = f"""You are a query router. The user asked: "{message}"
Available evidence categories in the knowledge base: {categories}
Return a comma-separated list of the 3 most relevant categories to this query. If none match, return 'All'."""

    async with gemini_semaphore:
        try:
            router_res = await client.aio.models.generate_content(
                model=MODEL_NAME,
                contents=router_prompt,
                config=types.GenerateContentConfig(temperature=0.1)
            )
            selected_cats = router_res.text.strip().lower()
        except Exception as e:
            logger.error(f"Router error: {e}")
            selected_cats = "all"

    filtered_evidence = []
    if "all" in selected_cats:
        filtered_evidence = all_evidence
    else:
        for e in all_evidence:
            if any(c.lower() in selected_cats for c in [e.category]):
                filtered_evidence.append(e)
                
    if not filtered_evidence:
        filtered_evidence = all_evidence # Fallback

    # Sort by confidence or limit to top 100 to avoid context limits
    filtered_evidence = sorted(filtered_evidence, key=lambda x: x.confidence, reverse=True)[:100]

    # Step 2: RAG Answer
    evidence_text = "\n".join([f"- {e.statement} (Source: {e.page_title})" for e in filtered_evidence])
    
    answer_prompt = f"""You are a research assistant answering questions about a generated report.
Use the following evidence from the project's knowledge base to answer the user's question. 
If the answer is not in the evidence, say you don't know based on the current research.

Evidence:
{evidence_text}

User Question: {message}
"""
    async with gemini_semaphore:
        try:
            answer_res = await client.aio.models.generate_content(
                model=MODEL_NAME,
                contents=answer_prompt,
                config=types.GenerateContentConfig(temperature=0.3)
            )
            return answer_res.text
        except Exception as e:
            logger.error(f"Chat answer error: {e}")
            return "I encountered an error trying to process your request."

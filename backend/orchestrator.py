import asyncio
import json
from typing import Dict, Any

from models import KnowledgeBase, SourceDisplay
from services import planner, search, reader, extractor, reflection, writer
from utils.dedup import deduplicate_facts
from utils.logger import get_logger

logger = get_logger("orchestrator")

MAX_ITERATIONS = 3

# Simple in-memory event queues for SSE
# job_id -> asyncio.Queue
job_queues: Dict[str, asyncio.Queue] = {}

async def emit_event(job_id: str, event_type: str, data: Any):
    if job_id in job_queues:
        event = {
            "type": event_type,
            "data": data
        }
        await job_queues[job_id].put(json.dumps(event))

async def end_stream(job_id: str):
    if job_id in job_queues:
        await job_queues[job_id].put(None) # Sentinel to close stream

async def run_research(job_id: str, query: str):
    logger.info(f"[{job_id}] Starting research orchestration for query: {query}")
    await emit_event(job_id, "status", {"stage": "planning", "message": "Creating research plan..."})
    
    try:
        # 1. Planner
        plan = planner.create_plan(query)
        await emit_event(job_id, "plan", plan.model_dump())
        
        kb = KnowledgeBase()
        current_queries = plan.queries[:5]
        
        for iteration in range(1, MAX_ITERATIONS + 1):
            await emit_event(job_id, "status", {"stage": "searching", "iteration": iteration, "message": f"Searching {len(current_queries)} queries..."})
            
            # 2. Search
            urls = search.search(current_queries)
            # Remove URLs already in search history
            new_urls = [u for u in urls if u not in kb.research_history]
            kb.research_history.extend(new_urls)
            
            if not new_urls:
                logger.warning(f"[{job_id}] No new URLs found in iteration {iteration}.")
                break
                
            # 3. Read
            await emit_event(job_id, "status", {"stage": "reading", "iteration": iteration, "current": 0, "total": len(new_urls), "message": "Fetching webpages..."})
            sources = reader.read(new_urls)
            kb.sources.extend([s.url for s in sources])
            
            # 4. Extract
            await emit_event(job_id, "status", {"stage": "extracting", "iteration": iteration, "current": 0, "total": len(sources), "message": "Extracting facts..."})
            
            new_facts = []
            for idx, src in enumerate(sources):
                ext_result = extractor.extract(src)
                new_facts.extend(ext_result.facts)
                kb.statistics.extend(ext_result.statistics)
                kb.quotes.extend(ext_result.quotes)
                # Emit progress for each source extracted
                await emit_event(job_id, "status", {"stage": "extracting", "iteration": iteration, "current": idx + 1, "total": len(sources), "message": f"Extracting from {src.domain}..."})
            
            # 5. Deduplicate
            logger.info(f"[{job_id}] Deduplicating {len(new_facts)} facts")
            kb.claims.extend(new_facts)
            kb.claims = deduplicate_facts(kb.claims)
            
            # 6. Reflect
            await emit_event(job_id, "status", {"stage": "reflecting", "iteration": iteration, "message": "Reflecting on gathered knowledge..."})
            ref_result = reflection.reflect(plan.goal, plan.success_criteria, kb, iteration)
            await emit_event(job_id, "reflection", ref_result.model_dump())
            
            if ref_result.enough_information or iteration == MAX_ITERATIONS:
                logger.info(f"[{job_id}] Research complete after {iteration} iterations.")
                break
                
            # 7. Follow-up plan if not enough info
            await emit_event(job_id, "status", {"stage": "planning", "iteration": iteration, "message": "Generating follow-up queries..."})
            current_queries = planner.create_followup_queries(ref_result.missing_topics)[:5]

        # 8. Write
        await emit_event(job_id, "status", {"stage": "writing", "message": "Writing final report..."})
        report = writer.write(plan, kb)
        
        sources_display = [SourceDisplay(title=s, url=s).model_dump() for s in kb.sources]
        
        await emit_event(job_id, "complete", {"report": report, "sources": sources_display})
        
    except Exception as e:
        logger.error(f"[{job_id}] Orchestration failed: {e}")
        await emit_event(job_id, "error", {"message": str(e)})
    finally:
        await end_stream(job_id)

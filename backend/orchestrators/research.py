import asyncio
import json
import time
from typing import Dict, Any, Optional

from models import KnowledgeBase, SourceDisplay
from services import planner, search, reader, extractor, reflection, writer
from utils.dedup import deduplicate_facts
from utils.logger import get_logger

from database.connection import SessionLocal
from repositories import (
    ProjectRepository,
    ResearchRunRepository,
    SourceRepository,
    EvidenceRepository,
    ReportRepository
)

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

async def run_research(job_id: str, query: str, project_id: Optional[str] = None, project_name: str = "New Research Project"):
    logger.info(f"[{job_id}] Starting research orchestration for query: {query}")
    await emit_event(job_id, "status", {"stage": "planning", "message": "Creating research plan..."})
    
    start_time = time.time()
    pages_read_count = 0
    evidence_extracted_count = 0
    tokens_used = 0
    
    db = SessionLocal()
    try:
        project_repo = ProjectRepository(db)
        run_repo = ResearchRunRepository(db)
        source_repo = SourceRepository(db)
        evidence_repo = EvidenceRepository(db)
        report_repo = ReportRepository(db)
        
        # 0. Setup Project and Run
        if project_id:
            project = project_repo.get_by_id(project_id)
            if not project:
                project = project_repo.create(name=project_name)
        else:
            project = project_repo.create(name=project_name)
            
        run = run_repo.create(project_id=project.id, query=query)
        
        # We'll emit the project and run IDs to the frontend so it knows where to look
        await emit_event(job_id, "meta", {"project_id": project.id, "run_id": run.id})

        # 1. Planner
        plan = await planner.create_plan(query)
        tokens_used += 1500 # Rough estimate
        await emit_event(job_id, "plan", plan.model_dump())
        
        kb = KnowledgeBase()
        current_queries = plan.queries[:5]
        
        actual_iterations = 0
        
        for iteration in range(1, MAX_ITERATIONS + 1):
            actual_iterations = iteration
            await emit_event(job_id, "status", {"stage": "searching", "iteration": iteration, "message": f"Searching {len(current_queries)} queries..."})
            
            # 2. Search
            urls = await search.search(current_queries)
            # Remove URLs already in search history
            new_urls = [u for u in urls if u not in kb.research_history]
            kb.research_history.extend(new_urls)
            
            if not new_urls:
                logger.warning(f"[{job_id}] No new URLs found in iteration {iteration}.")
                break
                
            # 3. Read
            async def read_progress(current, total, url):
                await emit_event(job_id, "status", {"stage": "reading", "iteration": iteration, "current": current, "total": total, "message": f"Fetched {url[:50]}..."})
                
            sources = await reader.read(new_urls, on_progress=read_progress)
            pages_read_count += len(sources)
            kb.sources.extend([s.url for s in sources])
            
            # Save Sources to DB
            db_sources = {}
            for s in sources:
                db_s = source_repo.create(run_id=run.id, title=s.title, url=s.url, domain=s.domain, markdown=s.markdown)
                db_sources[s.url] = db_s
            
            # 4. Extract
            await emit_event(job_id, "status", {"stage": "extracting", "iteration": iteration, "current": 0, "total": len(sources), "message": "Extracting facts concurrently..."})
            
            async def extract_progress(current, total, domain):
                await emit_event(job_id, "status", {"stage": "extracting", "iteration": iteration, "current": current, "total": total, "message": f"Extracting from {domain}..."})
            
            new_facts = []
            extraction_results = await extractor.extract_many(sources, on_progress=extract_progress)
            
            for idx, ext_result in enumerate(extraction_results):
                src = sources[idx]
                tokens_used += len(src.markdown) // 4  # rough estimation
                tokens_used += 1000 # output estimation
                
                db_src = db_sources.get(src.url)
                
                # Save Evidence to DB
                if db_src:
                    for fact in ext_result.facts:
                        evidence_repo.create(
                            source_id=db_src.id,
                            statement=fact.statement,
                            confidence=fact.confidence,
                            category=fact.category,
                            supporting_text=fact.supporting_text
                        )
                        evidence_extracted_count += 1
                        
                new_facts.extend(ext_result.facts)
                kb.statistics.extend(ext_result.statistics)
                kb.quotes.extend(ext_result.quotes)
            
            # 5. Deduplicate
            logger.info(f"[{job_id}] Deduplicating {len(new_facts)} facts")
            kb.claims.extend(new_facts)
            kb.claims = await deduplicate_facts(kb.claims)
            
            # 6. Reflect
            await emit_event(job_id, "status", {"stage": "reflecting", "iteration": iteration, "message": "Reflecting on gathered knowledge..."})
            ref_result = await reflection.reflect(plan.goal, plan.success_criteria, kb, iteration)
            tokens_used += 2000
            await emit_event(job_id, "reflection", ref_result.model_dump())
            
            # Update run metrics intermittently
            run_repo.update_metrics(
                run_id=run.id,
                pages_read=pages_read_count,
                evidence_extracted=evidence_extracted_count,
                iterations=actual_iterations,
                tokens_used=tokens_used,
                estimated_cost=tokens_used * 0.000001
            )
            
            if ref_result.enough_information or iteration == MAX_ITERATIONS:
                logger.info(f"[{job_id}] Research complete after {iteration} iterations.")
                break
                
            # 7. Follow-up plan if not enough info
            await emit_event(job_id, "status", {"stage": "planning", "iteration": iteration, "message": "Generating follow-up queries..."})
            followup_queries = await planner.create_followup_queries(ref_result.missing_topics)
            current_queries = followup_queries[:5]

        # 8. Write
        await emit_event(job_id, "status", {"stage": "writing", "message": "Writing final report..."})
        report_content = await writer.write(plan, kb)
        tokens_used += 3000
        
        # Save Report
        report_repo.create(project_id=project.id, run_id=run.id, content=report_content)
        
        # Final Run metrics
        time_taken = int(time.time() - start_time)
        run.time_taken_seconds = time_taken
        run_repo.update_metrics(
            run_id=run.id,
            pages_read=pages_read_count,
            evidence_extracted=evidence_extracted_count,
            iterations=actual_iterations,
            tokens_used=tokens_used,
            estimated_cost=tokens_used * 0.000001
        )
        run_repo.complete(run.id, status="completed")
        
        sources_display = [SourceDisplay(title=s, url=s).model_dump() for s in kb.sources]
        
        await emit_event(job_id, "complete", {"report": report_content, "sources": sources_display})
        
    except Exception as e:
        logger.error(f"[{job_id}] Orchestration failed: {e}")
        try:
            if 'run' in locals():
                run_repo.complete(run.id, status="failed")
        except:
            pass
        await emit_event(job_id, "error", {"message": str(e)})
    finally:
        db.close()
        await end_stream(job_id)

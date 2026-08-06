import asyncio
import json
import time
from typing import Dict, Any, Optional

from models import KnowledgeBase, SourceDisplay
from services import search, reader, extractor, reflector, writer, reviewer, cleaner
from planner import core as planner
from evaluation import evaluator
from models import CostMetrics
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

async def run_research(job_id: str, query: str, project_id: Optional[str] = None, project_name: str = "New Research Project", template_type: str = "General Report", file_paths: list[str] = None, existing_kb: KnowledgeBase = None):
    logger.info(f"[{job_id}] Starting research orchestration for query: {query}")
    await emit_event(job_id, "status", {"stage": "planning", "message": "Creating research plan..."})
    file_paths = file_paths or []
    
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
        if existing_kb:
            plan = await planner.create_plan(query, existing_kb)
            kb = existing_kb
        else:
            plan = await planner.create_plan(query)
            kb = KnowledgeBase()
        tokens_used += 1500 # Rough estimate
        await emit_event(job_id, "plan", plan.model_dump())
        
        current_queries = plan.tasks[:5]
        
        actual_iterations = 0
        
        for iteration in range(1, MAX_ITERATIONS + 1):
            actual_iterations = iteration
            
            # 2. Search (Task Graph Routing)
            new_urls = []
            mcp_docs = []
            
            from services.mcp_client import mcp_client
            
            for tsk in current_queries:
                await emit_event(job_id, "status", {"stage": "search", "iteration": iteration, "message": f"Executing task: {tsk.tool} -> {tsk.query}"})
                try:
                    if tsk.tool == "web_search":
                        urls = await search.search_duckduckgo(tsk.query)
                        new_urls.extend([u for u in urls if u not in kb.sources])
                    elif tsk.tool == "github":
                        urls = await search.search_duckduckgo(f"site:github.com {tsk.query}")
                        new_urls.extend([u for u in urls if u not in kb.sources])
                    elif tsk.tool == "reddit":
                        urls = await search.search_duckduckgo(f"site:reddit.com {tsk.query}")
                        new_urls.extend([u for u in urls if u not in kb.sources])
                    else:
                        # Route unrecognized tools to External MCP Servers
                        docs = await mcp_client.execute_tool(tsk.tool, {"query": tsk.query})
                        mcp_docs.extend(docs)
                except Exception as e:
                    logger.error(f"[{job_id}] Search task {tsk.tool} failed: {e}")
            
            # Deduplicate URLs already in search history
            new_urls = [u for u in new_urls if u not in kb.research_history]
            kb.research_history.extend(new_urls)
            
            if not new_urls:
                logger.warning(f"[{job_id}] No new URLs found in iteration {iteration}.")
                break
                
            # 3. Read
            async def read_progress(current, total, url):
                await emit_event(job_id, "status", {"stage": "reading", "iteration": iteration, "current": current, "total": total, "message": f"Fetched {url[:50]}..."})
                
            sources = await reader.read(new_urls, on_progress=read_progress)
            
            # Append documents fetched dynamically from MCP Integrations
            sources.extend(mcp_docs)
            
            # PHASE 4A: Parse local documents if provided (only in first iteration)
            if iteration == 1 and file_paths:
                from services.parser import get_parser
                import os
                parser = get_parser()
                for fpath in file_paths:
                    if os.path.exists(fpath):
                        await emit_event(job_id, "status", {"stage": "reading", "iteration": iteration, "current": 0, "total": 0, "message": f"Parsing local document {os.path.basename(fpath)}..."})
                        try:
                            doc = await parser.parse(fpath)
                            sources.append(doc)
                        except Exception as e:
                            logger.error(f"[{job_id}] Failed to parse {fpath}: {e}")

            pages_read_count += len(sources)
            kb.sources.extend([s.url for s in sources])
            
            # Save Sources to DB
            from services.reader import QUALITY_SCORES
            db_sources = {}
            for src in sources:
                qs_str = src.metadata.get("quality_score", "Unknown")
                qs_val = QUALITY_SCORES.get(qs_str, 0.0)
                
                db_source = source_repo.create(
                    run_id=run.id,
                    title=src.title,
                    url=src.id,
                    domain=src.metadata.get("domain", src.source_type),
                    markdown=src.text,
                    quality_score=qs_val
                )
                db_sources[src.id] = db_source
            
            # 4. Extract
            await emit_event(job_id, "status", {"stage": "extracting", "iteration": iteration, "current": 0, "total": len(sources), "message": "Extracting facts concurrently..."})
            
            for doc in sources:
                await emit_event(job_id, "status", {"stage": "extracting", "iteration": iteration, "message": f"Extracting insights from: {doc.title}"})
                extraction = await extractor.extract_evidence(doc)
                
                # Save Evidence to DB
                db_src = db_sources.get(doc.id)
                if db_src:
                    for fact in extraction.facts:
                        evidence_repo.create(
                            source_id=db_src.id,
                            statement=fact.statement,
                            confidence=fact.confidence,
                            category=fact.category,
                            supporting_text=fact.supporting_text
                        )
                        evidence_extracted_count += 1
                
                kb.claims.extend(extraction.facts)
                kb.statistics.extend(extraction.statistics)
                kb.quotes.extend(extraction.quotes)
            
            # 5. Deduplicate
            kb.claims = await cleaner.deduplicate_claims(kb.claims)
            
            # 6. Reflect
            await emit_event(job_id, "status", {"stage": "reflecting", "iteration": iteration, "message": "Evaluating research coverage..."})
            ref_result = await reflector.reflect(plan.goal, plan.success_criteria, kb, iteration)
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

        # 8. Write and Review Loop
        feedback = None
        for write_attempt in range(1, 3):
            await emit_event(job_id, "status", {"stage": "writing", "message": f"Writing final report (Attempt {write_attempt})..."})
            report_content = await writer.generate_report(plan, kb, template_type, feedback=feedback)
            
            await emit_event(job_id, "status", {"stage": "writing", "iteration": actual_iterations, "message": "AI Reviewer evaluating report quality..."})
            review = await reviewer.review_report(report_content, plan)
            
            if review.pass_review or write_attempt == 2:
                if write_attempt == 2 and not review.pass_review:
                    logger.warning(f"[{job_id}] Max rewrites reached. Accepting report despite failing review.")
                break
                
            feedback = review.feedback
            logger.info(f"[{job_id}] Report failed review. Feedback: {feedback}")
            
        tokens_used += 3000 * write_attempt
        
        # 9. Evaluate Report
        await emit_event(job_id, "status", {"stage": "evaluating", "message": "EvaluationAgent scoring report quality..."})
        eval_metrics = await evaluator.evaluate_report(report_content, plan)
        
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
        
        cost_metrics = CostMetrics(
            total_tokens=tokens_used,
            estimated_cost_usd=tokens_used * 0.000001,
            duration_seconds=time_taken,
            total_llm_calls=0 # Can be tracked later
        )
        
        await emit_event(job_id, "complete", {
            "report": report_content, 
            "sources": sources_display,
            "evaluation": eval_metrics.model_dump(),
            "cost": cost_metrics.model_dump()
        })
        
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

import uuid
import asyncio
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from models import ResearchRequest
from orchestrators import research as orchestrator
from utils.logger import get_logger
from api.projects import router as projects_router

logger = get_logger("app")

app = FastAPI(title="Deep Research API - Phase 3")

app.include_router(projects_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class JobResponse(BaseModel):
    job_id: str

@app.post("/api/research", response_model=JobResponse)
def start_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    logger.info(f"Received research request: '{request.query}'. Assigned job_id: {job_id}")
    
    # Initialize event queue for this job
    orchestrator.job_queues[job_id] = asyncio.Queue()
    
    # Run the orchestrator in the background
    background_tasks.add_task(orchestrator.run_research, job_id, request.query, request.project_id, request.project_name)
    
    return JobResponse(job_id=job_id)

@app.get("/api/research/{job_id}/events")
async def research_events(job_id: str):
    if job_id not in orchestrator.job_queues:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_generator():
        queue = orchestrator.job_queues[job_id]
        try:
            while True:
                event = await queue.get()
                if event is None:
                    # End of stream
                    break
                yield f"data: {event}\n\n"
        except asyncio.CancelledError:
            logger.info(f"Client disconnected from SSE for job_id: {job_id}")
        finally:
            # Clean up queue
            if job_id in orchestrator.job_queues:
                del orchestrator.job_queues[job_id]

    return StreamingResponse(event_generator(), media_type="text/event-stream")

import uuid
import asyncio
import os
import shutil
from fastapi import FastAPI, BackgroundTasks, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from database import engine, get_db, Base
from models import ResearchRequest
from orchestrators import research as orchestrator
from providers import init_providers
from utils.logger import get_logger
from api.projects import router as projects_router

# Initialize database
Base.metadata.create_all(bind=engine)

# Initialize global LLM provider registry
init_providers()

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

# Ensure upload directory exists
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class JobResponse(BaseModel):
    job_id: str

class ChatRequest(BaseModel):
    message: str

@app.post("/api/research", response_model=JobResponse)
def start_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    logger.info(f"Received research request: '{request.query}'. Assigned job_id: {job_id}")
    
    # Initialize event queue for this job
    orchestrator.job_queues[job_id] = asyncio.Queue()
    
    # Run the orchestrator in the background
    background_tasks.add_task(
        orchestrator.run_research, 
        job_id, 
        request.query, 
        request.project_id, 
        request.project_name,
        request.template_type,
        request.file_paths
    )
    
    return JobResponse(job_id=job_id)

@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"file_path": file_path, "filename": file.filename}

@app.post("/api/projects/{project_id}/continue", response_model=JobResponse)
def continue_research(project_id: str, request: ResearchRequest, background_tasks: BackgroundTasks):
    db = next(get_db())
    from repositories.evidence_repository import EvidenceRepository
    from models import KnowledgeBase, Evidence as PydanticEvidence
    
    evidence_repo = EvidenceRepository(db)
    existing_evidence = evidence_repo.get_by_project(project_id)
    
    kb = KnowledgeBase()
    for e in existing_evidence:
        kb.claims.append(PydanticEvidence(
            statement=e.statement,
            source=e.source_id,
            url=e.source.url if hasattr(e, 'source') and e.source else "",
            page_title=e.source.title if hasattr(e, 'source') and e.source else "",
            confidence=e.confidence,
            category=e.category,
            supporting_text=e.supporting_text or ""
        ))
    
    job_id = str(uuid.uuid4())
    orchestrator.job_queues[job_id] = asyncio.Queue()
    
    background_tasks.add_task(
        orchestrator.run_research, 
        job_id, 
        request.query, 
        project_id, 
        request.project_name,
        request.template_type,
        request.file_paths,
        kb
    )
    
    return JobResponse(job_id=job_id)

@app.post("/api/projects/{project_id}/chat")
async def chat_with_project(project_id: str, request: ChatRequest):
    from services.chat import get_chat_response
    answer = await get_chat_response(project_id, request.message)
    return {"answer": answer}

@app.get("/api/projects/{project_id}/export")
def export_report(project_id: str, format: str = "markdown"):
    db = next(get_db())
    report_repo = ReportRepository(db)
    report = report_repo.get_by_project(project_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    content = report.content
    
    if format == "markdown":
        return StreamingResponse(
            iter([content.encode()]), 
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=report_{project_id}.md"}
        )
    elif format == "html" or format == "pdf":
        import markdown
        html = markdown.markdown(content)
        if format == "html":
            return StreamingResponse(
                iter([html.encode()]), 
                media_type="text/html",
                headers={"Content-Disposition": f"attachment; filename=report_{project_id}.html"}
            )
        else:
            # PDF Generation
            from xhtml2pdf import pisa
            import io
            full_html = f"<html><head><meta charset='utf-8'></head><body>{html}</body></html>"
            pdf_file = io.BytesIO()
            pisa_status = pisa.CreatePDF(full_html, dest=pdf_file)
            if pisa_status.err:
                raise HTTPException(status_code=500, detail="PDF generation failed")
                
            pdf_file.seek(0)
            return StreamingResponse(
                pdf_file, 
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=report_{project_id}.pdf"}
            )
    else:
        raise HTTPException(status_code=400, detail="Unsupported format")

@app.get("/api/projects/{project_id}/evidence")
def get_project_evidence(project_id: str):
    db = next(get_db())
    from repositories.evidence_repository import EvidenceRepository
    evidence_repo = EvidenceRepository(db)
    
    evidence = evidence_repo.get_by_project(project_id)
    # Return mapping of Source URL -> List of Evidence
    result = {}
    for e in evidence:
        if e.source_id not in result:
            result[e.source_id] = []
        result[e.source_id].append({
            "statement": e.statement,
            "category": e.category,
            "confidence": e.confidence
        })
    return result

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

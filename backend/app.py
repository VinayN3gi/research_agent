from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

from models import ResearchRequest, ResearchResponse, SourceDisplay
from services import planner, search, reader, writer
from utils.logger import get_logger

logger = get_logger("app")

app = FastAPI(title="Deep Research API - Phase 1")

# Allow frontend to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev, allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/api/research", response_model=ResearchResponse)
def run_research(request: ResearchRequest):
    logger.info(f"--- Started research for: '{request.query}' ---")
    
    try:
        # 1. Planner
        plan = planner.create_plan(request.query)
        # Cap queries to 5 as requested
        queries_to_search = plan.queries[:5]
        
        # 2. Search
        urls = search.search(queries_to_search)
        
        # 3. Reader
        sources = reader.read(urls)
        
        if not sources:
            logger.warning("No sources were fetched successfully.")
            return ResearchResponse(
                report="# No sources found\n\nCould not fetch any websites for this topic.",
                sources=[]
            )
            
        # 4. Writer
        report = writer.write(request.query, sources)
        
        logger.info(f"--- Finished research for: '{request.query}' ---")
        
        return ResearchResponse(
            report=report,
            sources=[SourceDisplay(title=s.title, url=s.url) for s in sources]
        )
        
    except Exception as e:
        logger.error(f"Research pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

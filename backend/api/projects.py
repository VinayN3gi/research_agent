from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from repositories import ProjectRepository, ResearchRunRepository

router = APIRouter(prefix="/api/projects", tags=["projects"])

@router.get("/")
def get_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    repo = ProjectRepository(db)
    projects = repo.get_all(skip=skip, limit=limit)
    return [{"id": p.id, "name": p.name, "created_at": p.created_at} for p in projects]

@router.get("/{project_id}")
def get_project(project_id: str, db: Session = Depends(get_db)):
    repo = ProjectRepository(db)
    project = repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    return {
        "id": project.id,
        "name": project.name,
        "created_at": project.created_at,
        "runs": [{"id": r.id, "query": r.query, "status": r.status, "created_at": r.created_at} for r in project.runs],
        "reports": [{"id": r.id, "version": r.version, "content": r.content, "created_at": r.created_at} for r in project.reports]
    }

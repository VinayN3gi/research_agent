from sqlalchemy.orm import Session
from database.models.project import Project
from typing import List, Optional

class ProjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, project_id: str) -> Optional[Project]:
        return self.db.query(Project).filter(Project.id == project_id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Project]:
        return self.db.query(Project).order_by(Project.created_at.desc()).offset(skip).limit(limit).all()

    def create(self, name: str, description: Optional[str] = None) -> Project:
        project = Project(name=name, description=description)
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

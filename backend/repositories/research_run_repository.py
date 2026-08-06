from sqlalchemy.orm import Session
from database.models.research_run import ResearchRun
from typing import Optional

class ResearchRunRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, run_id: str) -> Optional[ResearchRun]:
        return self.db.query(ResearchRun).filter(ResearchRun.id == run_id).first()

    def create(self, project_id: str, query: str) -> ResearchRun:
        run = ResearchRun(project_id=project_id, query=query)
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def update_metrics(self, run_id: str, pages_read: int = 0, evidence_extracted: int = 0, iterations: int = 0, tokens_used: int = 0, estimated_cost: float = 0.0) -> Optional[ResearchRun]:
        run = self.get_by_id(run_id)
        if run:
            run.pages_read = pages_read
            run.evidence_extracted = evidence_extracted
            run.iterations = iterations
            run.tokens_used = tokens_used
            run.estimated_cost = estimated_cost
            self.db.commit()
            self.db.refresh(run)
        return run

    def complete(self, run_id: str, status: str = "completed") -> Optional[ResearchRun]:
        run = self.get_by_id(run_id)
        if run:
            run.status = status
            from sqlalchemy.sql import func
            run.completed_at = func.now()
            self.db.commit()
            self.db.refresh(run)
        return run

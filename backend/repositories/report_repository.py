from sqlalchemy.orm import Session
from database.models.report import Report
from typing import Optional

class ReportRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_project(self, project_id: str) -> Optional[Report]:
        return self.db.query(Report).filter(Report.project_id == project_id).order_by(Report.version.desc()).first()

    def create(self, project_id: str, run_id: str, content: str, version: int = 1) -> Report:
        report = Report(project_id=project_id, run_id=run_id, content=content, version=version)
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

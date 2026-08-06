from sqlalchemy.orm import Session
from database.models.evidence import Evidence
from database.models.source import Source
from database.models.research_run import ResearchRun
from typing import List, Optional

class EvidenceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, evidence_id: str) -> Optional[Evidence]:
        return self.db.query(Evidence).filter(Evidence.id == evidence_id).first()

    def get_by_source(self, source_id: str) -> List[Evidence]:
        return self.db.query(Evidence).filter(Evidence.source_id == source_id).all()

    def get_by_project(self, project_id: str) -> List[Evidence]:
        return self.db.query(Evidence).join(Source).join(ResearchRun).filter(ResearchRun.project_id == project_id).all()

    def create(self, source_id: str, statement: str, confidence: float = 0.0, category: str = "fact", supporting_text: Optional[str] = None) -> Evidence:
        evidence = Evidence(source_id=source_id, statement=statement, confidence=confidence, category=category, supporting_text=supporting_text)
        self.db.add(evidence)
        self.db.commit()
        self.db.refresh(evidence)
        return evidence

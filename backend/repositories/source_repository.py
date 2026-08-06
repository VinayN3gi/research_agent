from sqlalchemy.orm import Session
from database.models.source import Source
from typing import List, Optional

class SourceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, source_id: str) -> Optional[Source]:
        return self.db.query(Source).filter(Source.id == source_id).first()

    def get_by_run(self, run_id: str) -> List[Source]:
        return self.db.query(Source).filter(Source.run_id == run_id).all()

    def create(self, run_id: str, title: str, url: str, domain: Optional[str] = None, markdown: Optional[str] = None, quality_score: float = 0.0) -> Source:
        source = Source(run_id=run_id, title=title, url=url, domain=domain, markdown=markdown, quality_score=quality_score)
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)
        return source

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from database.connection import Base

class Source(Base):
    __tablename__ = "sources"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String, ForeignKey("research_runs.id"), nullable=False)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    domain = Column(String, nullable=True)
    markdown = Column(Text, nullable=True)
    
    # Source Ranking (Phase 3C)
    quality_score = Column(Float, default=0.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    run = relationship("ResearchRun", back_populates="sources")
    evidence = relationship("Evidence", back_populates="source", cascade="all, delete-orphan")

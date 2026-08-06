from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from database.connection import Base

class ResearchRun(Base):
    __tablename__ = "research_runs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    query = Column(String, nullable=False)
    status = Column(String, default="running") # running, completed, failed
    
    # Observability Metrics
    time_taken_seconds = Column(Integer, default=0)
    pages_read = Column(Integer, default=0)
    evidence_extracted = Column(Integer, default=0)
    iterations = Column(Integer, default=0)
    tokens_used = Column(Integer, default=0)
    estimated_cost = Column(Float, default=0.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="runs")
    sources = relationship("Source", back_populates="run", cascade="all, delete-orphan")

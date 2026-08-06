from pydantic import BaseModel
from typing import List, Optional

class ResearchRequest(BaseModel):
    query: str
    project_id: Optional[str] = None
    project_name: Optional[str] = "New Research Project"
    template_type: Optional[str] = "General Report"
    file_paths: List[str] = []
    
class Document(BaseModel):
    id: str
    title: str
    source_type: str  # e.g., "pdf", "docx", "web", "csv", "image"
    text: str
    images: List[str] = [] # list of image descriptors or paths
    tables: List[str] = []
    metadata: dict = {}

class ResearchPlan(BaseModel):
    goal: str
    sections: List[str]
    queries: List[str]
    success_criteria: List[str]

class Source(BaseModel):
    title: str
    url: str
    markdown: str
    published_date: Optional[str] = None
    author: Optional[str] = None
    domain: Optional[str] = None
    quality_score: str = "Unknown"  # Official Docs, Research Paper, News, Blog, Unknown

class Evidence(BaseModel):
    statement: str
    source: str
    url: str
    page_title: str
    confidence: float
    category: str
    supporting_text: str

class ExtractionResult(BaseModel):
    facts: List[Evidence]
    statistics: List[str]
    quotes: List[str]

class ReflectionResult(BaseModel):
    enough_information: bool
    missing_topics: List[str]

class KnowledgeBase(BaseModel):
    sources: List[str] = []
    claims: List[Evidence] = []
    statistics: List[str] = []
    quotes: List[str] = []
    contradictions: List[str] = []
    missing_topics: List[str] = []
    research_history: List[str] = []

class SourceDisplay(BaseModel):
    title: str
    url: str

class ResearchResponse(BaseModel):
    report: str
    sources: List[SourceDisplay]

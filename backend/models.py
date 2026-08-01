from pydantic import BaseModel
from typing import List, Optional

class PlannerResponse(BaseModel):
    goal: str
    queries: List[str]

class Source(BaseModel):
    title: str
    url: str
    markdown: str
    published_date: Optional[str] = None
    author: Optional[str] = None
    domain: Optional[str] = None

class ResearchRequest(BaseModel):
    query: str

class SourceDisplay(BaseModel):
    title: str
    url: str

class ResearchResponse(BaseModel):
    report: str
    sources: List[SourceDisplay]

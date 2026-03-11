import json
from datetime import datetime
from typing import List, Optional

from sqlmodel import Field, SQLModel


class Division(SQLModel, table=True):
    code: str = Field(primary_key=True)
    name: str
    parent_code: Optional[str] = Field(default=None, foreign_key=None)
    paper_count: int = 0
    url: str


class Subject(SQLModel, table=True):
    code: str = Field(primary_key=True)
    name: str
    paper_count: int = 0
    url: str


class Author(SQLModel, table=True):
    slug: str = Field(primary_key=True)
    name: str
    paper_count: int = 0
    url: str


class Paper(SQLModel, table=True):
    id: int = Field(primary_key=True)
    title: str
    author: str
    author_slug: Optional[str] = None
    year: Optional[int] = None
    degree_type: Optional[str] = None
    abstract_id: Optional[str] = None
    abstract_en: Optional[str] = None
    division_code: Optional[str] = None
    subject_codes: Optional[str] = None   # JSON array
    pdf_urls: Optional[str] = None        # JSON array
    eprint_url: str
    scraped_at: datetime = Field(default_factory=datetime.utcnow)

    def subject_codes_list(self) -> List[str]:
        return json.loads(self.subject_codes) if self.subject_codes else []

    def pdf_urls_list(self) -> List[str]:
        return json.loads(self.pdf_urls) if self.pdf_urls else []

import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func

from app.database import get_session
from app.models import Paper

router = APIRouter(prefix="/papers", tags=["papers"])


def _paper_to_dict(p: Paper) -> dict:
    return {
        "id": p.id,
        "title": p.title,
        "author": p.author,
        "year": p.year,
        "degree_type": p.degree_type,
        "division_code": p.division_code,
        "subject_codes": json.loads(p.subject_codes) if p.subject_codes else [],
        "pdf_urls": json.loads(p.pdf_urls) if p.pdf_urls else [],
        "abstract_id": p.abstract_id,
        "abstract_en": p.abstract_en,
        "eprint_url": p.eprint_url,
        "scraped_at": p.scraped_at.isoformat() if p.scraped_at else None,
    }


@router.get("")
def list_papers(
    year: Optional[int] = None,
    division: Optional[str] = None,
    subject: Optional[str] = None,
    degree_type: Optional[str] = None,
    author_slug: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    """List papers with optional filters. Paginated."""
    stmt = select(Paper)
    if year:
        stmt = stmt.where(Paper.year == year)
    if division:
        stmt = stmt.where(Paper.division_code == division)
    if subject:
        stmt = stmt.where(Paper.subject_codes.contains(subject))
    if degree_type:
        stmt = stmt.where(Paper.degree_type == degree_type)
    if author_slug:
        stmt = stmt.where(Paper.author_slug == author_slug)

    total = session.exec(select(func.count()).select_from(stmt.subquery())).one()
    papers = session.exec(stmt.offset((page - 1) * limit).limit(limit)).all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "results": [_paper_to_dict(p) for p in papers],
    }


@router.get("/search")
def search_papers(
    q: str = Query(..., min_length=2),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    """Full-text search over title and abstracts."""
    from sqlmodel import text
    offset = (page - 1) * limit
    rows = session.exec(text(f"""
        SELECT p.* FROM paper p
        JOIN paper_fts f ON p.id = f.rowid
        WHERE paper_fts MATCH :q
        ORDER BY rank
        LIMIT :limit OFFSET :offset
    """), {"q": q, "limit": limit, "offset": offset}).mappings().all()

    count_row = session.exec(text("""
        SELECT COUNT(*) FROM paper p
        JOIN paper_fts f ON p.id = f.rowid
        WHERE paper_fts MATCH :q
    """), {"q": q}).one()

    papers = [dict(r) for r in rows]
    return {"total": count_row[0], "page": page, "limit": limit, "results": papers}


@router.get("/{paper_id}")
def get_paper(paper_id: int, session: Session = Depends(get_session)):
    """Get full detail for a single paper by eprint ID."""
    paper = session.get(Paper, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail=f"Paper {paper_id} not found")
    return _paper_to_dict(paper)

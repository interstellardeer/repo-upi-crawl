from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func

from app.database import get_session
from app.models import Author, Paper

router = APIRouter(prefix="/authors", tags=["authors"])


@router.get("")
def list_authors(
    q: str = Query(None, description="Filter by name (ILIKE)"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    session: Session = Depends(get_session),
):
    """List all authors, with optional name search."""
    stmt = select(Author)
    if q:
        stmt = stmt.where(Author.name.ilike(f"%{q}%"))
    total = session.exec(select(func.count()).select_from(stmt.subquery())).one()
    authors = session.exec(stmt.offset((page - 1) * limit).limit(limit)).all()
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "results": [a.model_dump() for a in authors],
    }


@router.get("/{slug}")
def get_author(slug: str, session: Session = Depends(get_session)):
    author = session.get(Author, slug)
    if not author:
        raise HTTPException(status_code=404, detail=f"Author '{slug}' not found")
    return author.model_dump()


@router.get("/{slug}/papers")
def author_papers(
    slug: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    author = session.get(Author, slug)
    if not author:
        raise HTTPException(status_code=404, detail=f"Author '{slug}' not found")

    stmt = select(Paper).where(Paper.author_slug == slug)
    total = session.exec(select(func.count()).select_from(stmt.subquery())).one()
    papers = session.exec(stmt.offset((page - 1) * limit).limit(limit)).all()
    return {
        "author": author.model_dump(),
        "total": total,
        "page": page,
        "limit": limit,
        "results": [
            {"id": p.id, "title": p.title, "year": p.year, "degree_type": p.degree_type, "eprint_url": p.eprint_url}
            for p in papers
        ],
    }

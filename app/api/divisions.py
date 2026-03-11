from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.database import get_session
from app.models import Division, Paper

router = APIRouter(prefix="/divisions", tags=["divisions"])


@router.get("")
def list_divisions(session: Session = Depends(get_session)):
    """Return the full division tree."""
    divisions = session.exec(select(Division)).all()
    return [d.model_dump() for d in divisions]


@router.get("/{code}")
def get_division(code: str, session: Session = Depends(get_session)):
    div = session.get(Division, code)
    if not div:
        raise HTTPException(status_code=404, detail=f"Division '{code}' not found")
    return div.model_dump()


@router.get("/{code}/papers")
def division_papers(
    code: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    """List papers in a specific division."""
    from sqlmodel import func
    stmt = select(Paper).where(Paper.division_code == code)
    total = session.exec(select(func.count()).select_from(stmt.subquery())).one()
    papers = session.exec(stmt.offset((page - 1) * limit).limit(limit)).all()
    import json
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "results": [
            {
                "id": p.id, "title": p.title, "author": p.author,
                "year": p.year, "degree_type": p.degree_type,
                "eprint_url": p.eprint_url,
            }
            for p in papers
        ],
    }

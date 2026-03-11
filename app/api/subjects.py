from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func

from app.database import get_session
from app.models import Subject, Paper

router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.get("")
def list_subjects(session: Session = Depends(get_session)):
    subjects = session.exec(select(Subject)).all()
    return [s.model_dump() for s in subjects]


@router.get("/{code}")
def get_subject(code: str, session: Session = Depends(get_session)):
    subj = session.get(Subject, code)
    if not subj:
        raise HTTPException(status_code=404, detail=f"Subject '{code}' not found")
    return subj.model_dump()


@router.get("/{code}/papers")
def subject_papers(
    code: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    stmt = select(Paper).where(Paper.subject_codes.contains(code))
    total = session.exec(select(func.count()).select_from(stmt.subquery())).one()
    papers = session.exec(stmt.offset((page - 1) * limit).limit(limit)).all()
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "results": [
            {"id": p.id, "title": p.title, "author": p.author, "year": p.year, "eprint_url": p.eprint_url}
            for p in papers
        ],
    }

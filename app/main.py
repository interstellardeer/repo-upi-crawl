import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select, func, text

from app.database import init_db, get_session, engine
from app.models import Paper, Division, Subject, Author
from app.api import papers, divisions, subjects, authors

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="UPI Repository API",
    description=(
        "Programmatic access to ~90,000 academic papers from "
        "Universitas Pendidikan Indonesia (repository.upi.edu)."
    ),
    version="1.0.0",
    contact={"name": "UPI Repository Crawler", "url": "https://github.com/interstellardeer"},
    license_info={"name": "MIT"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(papers.router)
app.include_router(divisions.router)
app.include_router(subjects.router)
app.include_router(authors.router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/", tags=["meta"])
def root():
    return {
        "name": "UPI Repository API",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": ["/papers", "/divisions", "/subjects", "/authors", "/stats"],
    }


@app.get("/stats", tags=["meta"])
def stats():
    """Return counts and last crawl timestamp."""
    with Session(engine) as session:
        paper_count = session.exec(select(func.count(Paper.id))).one()
        author_count = session.exec(select(func.count(Author.slug))).one()
        division_count = session.exec(select(func.count(Division.code))).one()
        subject_count = session.exec(select(func.count(Subject.code))).one()
        latest = session.exec(
            select(Paper.scraped_at).order_by(Paper.scraped_at.desc()).limit(1)
        ).first()
    return {
        "papers": paper_count,
        "authors": author_count,
        "divisions": division_count,
        "subjects": subject_count,
        "last_scraped_at": latest.isoformat() if latest else None,
    }


@app.post("/crawl/trigger", tags=["meta"])
async def trigger_crawl(
    mode: str = "incremental",
    year: int = None,
    division: str = None,
    author: str = None,
    api_key: str = "",
):
    """
    Trigger a background crawl. Protected by API key (set CRAWL_API_KEY in .env).

    Modes: `incremental` (default), `all`, `year`, `division`, `author`
    """
    from app.config import settings
    if api_key != settings.CRAWL_API_KEY:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Invalid API key")

    import asyncio
    from app.crawlers import orchestrator

    async def _run():
        if mode == "all":
            await orchestrator.crawl_all()
        elif mode == "year" and year:
            await orchestrator.crawl_year(year)
        elif mode == "division" and division:
            await orchestrator.crawl_division(division)
        elif mode == "author" and author:
            await orchestrator.crawl_author(author)
        else:
            await orchestrator.crawl_incremental()

    asyncio.create_task(_run())
    return {"status": "crawl started", "mode": mode}

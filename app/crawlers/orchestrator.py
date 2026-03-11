import asyncio
import json
import logging
from datetime import datetime
from typing import Optional

from sqlmodel import Session, select, func

from app.config import settings
from app.database import engine
from app.models import Author, Division, Paper, Subject
from app.scrapers.base import PageNotFoundError, ScraperError
from app.scrapers.creators import scrape_creators
from app.scrapers.divisions import scrape_divisions
from app.scrapers.listing import scrape_listing
from app.scrapers.paper import scrape_paper
from app.scrapers.subjects import scrape_subjects
from app.scrapers.years import scrape_years

log = logging.getLogger(__name__)

NUM_WORKERS = settings.CONCURRENCY


def _paper_exists(session: Session, eprint_id: int) -> bool:
    return session.get(Paper, eprint_id) is not None


def _upsert_paper(session: Session, detail) -> None:
    """Write a PaperDetail to the database."""
    paper = Paper(
        id=detail.eprint_id,
        title=detail.title,
        author=detail.author,
        year=detail.year,
        degree_type=detail.degree_type,
        abstract_id=detail.abstract_id,
        abstract_en=detail.abstract_en,
        division_code=detail.division_code,
        subject_codes=json.dumps(detail.subject_codes, ensure_ascii=False),
        pdf_urls=json.dumps(detail.pdf_urls, ensure_ascii=False),
        eprint_url=detail.eprint_url,
        scraped_at=datetime.utcnow(),
    )
    session.merge(paper)
    session.commit()


async def _worker(queue: asyncio.Queue, results: dict) -> None:
    """Async worker: pops eprint IDs from queue and scrapes detail pages."""
    while True:
        eprint_id = await queue.get()
        if eprint_id is None:  # poison pill
            queue.task_done()
            break
        try:
            with Session(engine) as session:
                if _paper_exists(session, eprint_id):
                    log.debug(f"Skip {eprint_id} (already in DB)")
                    results["skipped"] = results.get("skipped", 0) + 1
                    queue.task_done()
                    continue
            detail = await scrape_paper(eprint_id)
            with Session(engine) as session:
                _upsert_paper(session, detail)
            results["saved"] = results.get("saved", 0) + 1
            log.info(f"Saved eprint {eprint_id}: {detail.title[:60]}")
        except PageNotFoundError:
            log.warning(f"404 for eprint {eprint_id}, skipping")
            results["errors"] = results.get("errors", 0) + 1
        except ScraperError as e:
            log.warning(f"Scraper error for {eprint_id}: {e}")
            results["errors"] = results.get("errors", 0) + 1
        except Exception as e:
            log.error(f"Unexpected error for {eprint_id}: {e}")
            results["errors"] = results.get("errors", 0) + 1
        finally:
            queue.task_done()


async def _run_worker_pool(eprint_ids: list[int]) -> dict:
    """Run a pool of async workers over a list of eprint IDs."""
    queue: asyncio.Queue = asyncio.Queue()
    results: dict = {}

    for eid in eprint_ids:
        await queue.put(eid)
    for _ in range(NUM_WORKERS):
        await queue.put(None)  # poison pills

    workers = [asyncio.create_task(_worker(queue, results)) for _ in range(NUM_WORKERS)]
    await queue.join()
    await asyncio.gather(*workers)
    return results


# ---------------------------------------------------------------------------
# Public crawl functions
# ---------------------------------------------------------------------------

async def bootstrap() -> None:
    """Populate Division, Subject, Author reference tables from browse indexes."""
    log.info("Bootstrapping divisions...")
    divisions = await scrape_divisions(settings.BASE_URL)
    with Session(engine) as session:
        for d in divisions:
            session.merge(Division(
                code=d.code, name=d.name, paper_count=d.paper_count,
                url=d.url, parent_code=d.parent_code,
            ))
        session.commit()
    log.info(f"  → {len(divisions)} divisions saved")

    log.info("Bootstrapping subjects...")
    subjects = await scrape_subjects(settings.BASE_URL)
    with Session(engine) as session:
        for s in subjects:
            session.merge(Subject(code=s.code, name=s.name, paper_count=s.paper_count, url=s.url))
        session.commit()
    log.info(f"  → {len(subjects)} subjects saved")

    log.info("Bootstrapping authors (this may take a few minutes)...")
    authors = await scrape_creators(settings.BASE_URL)
    with Session(engine) as session:
        for a in authors:
            session.merge(Author(slug=a.slug, name=a.name, paper_count=a.paper_count, url=a.url))
        session.commit()
    log.info(f"  → {len(authors)} authors saved")


async def crawl_year(year: int) -> dict:
    log.info(f"Crawling year {year}...")
    url = f"{settings.BASE_URL}/view/year/{year}.html"
    stubs = await scrape_listing(url)
    ids = [s.eprint_id for s in stubs]
    log.info(f"  Found {len(ids)} papers in {year}")
    results = await _run_worker_pool(ids)
    log.info(f"  Year {year} done: {results}")
    return results


async def crawl_division(code: str) -> dict:
    log.info(f"Crawling division {code}...")
    base_url = settings.BASE_URL
    division_index_url = f"{base_url}/view/divisions/{code}/"

    # Division index pages list year sub-pages (e.g. 2024.html, 2023.html)
    # rather than papers directly. Discover all year sub-page links first.
    from app.scrapers.base import get_soup as _get_soup
    import re as _re

    soup = await _get_soup(division_index_url)
    _year_link = _re.compile(r"^(\d{4})\.html$")
    year_urls: list[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if _year_link.match(href):
            # Relative URL — resolve to absolute
            year_urls.append(f"{division_index_url}{href}")

    if not year_urls:
        # Fallback: the division page might directly list papers (some do)
        stubs = await scrape_listing(division_index_url)
        ids = [s.eprint_id for s in stubs]
    else:
        log.info(f"  Division {code} has {len(year_urls)} year sub-pages")
        ids: list[int] = []
        seen_ids: set[int] = set()
        for yurl in year_urls:
            stubs = await scrape_listing(yurl)
            for s in stubs:
                if s.eprint_id not in seen_ids:
                    seen_ids.add(s.eprint_id)
                    ids.append(s.eprint_id)

    log.info(f"  Found {len(ids)} papers in division {code}")
    results = await _run_worker_pool(ids)
    log.info(f"  Division {code} done: {results}")
    return results


async def crawl_author(slug_or_name: str) -> dict:
    """Crawl by author slug (URL-encoded) or human name lookup in DB."""
    # Try to resolve a human name to a slug via the DB
    with Session(engine) as session:
        author = session.get(Author, slug_or_name)
        if not author:
            # Try name search
            results_db = session.exec(
                select(Author).where(Author.name.ilike(f"%{slug_or_name}%"))
            ).first()
            author = results_db

    if author:
        slug = author.slug
        url = author.url
    else:
        # Treat the argument as a raw slug
        slug = slug_or_name
        url = f"{settings.BASE_URL}/view/creators/{slug}.html"

    log.info(f"Crawling author slug={slug}...")
    stubs = await scrape_listing(url)
    ids = [s.eprint_id for s in stubs]
    log.info(f"  Found {len(ids)} papers for author {slug}")
    results = await _run_worker_pool(ids)
    log.info(f"  Author done: {results}")
    return results


async def crawl_all() -> dict:
    """Full crawl: bootstrap indexes then crawl every year."""
    await bootstrap()
    years = await scrape_years(settings.BASE_URL)
    total: dict = {}
    for entry in years:
        r = await crawl_year(entry.year)
        for k, v in r.items():
            total[k] = total.get(k, 0) + v
    log.info(f"Full crawl complete: {total}")
    return total


async def crawl_incremental() -> dict:
    """Only re-crawl years/divisions where site count differs from DB count."""
    await bootstrap()
    years = await scrape_years(settings.BASE_URL)
    total: dict = {}

    with Session(engine) as session:
        for entry in years:
            db_count = session.exec(
                select(func.count(Paper.id)).where(Paper.year == entry.year)
            ).one()
            if db_count < entry.paper_count:
                log.info(f"Year {entry.year}: site={entry.paper_count}, db={db_count} → re-crawling")
                r = await crawl_year(entry.year)
                for k, v in r.items():
                    total[k] = total.get(k, 0) + v
            else:
                log.debug(f"Year {entry.year}: up to date ({db_count} papers)")

    log.info(f"Incremental crawl complete: {total}")
    return total

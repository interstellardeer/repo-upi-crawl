# PROMPT-PROJECT-STRUCTURE.md
# Project Structure — UPI Repository Scraper API

Use this file as shared context when prompting an LLM to work on any part of this project.
It defines the folder layout, each file's responsibility, and the key design decisions.

---

## Tech Stack

| Layer | Choice |
|---|---|
| Language | Python 3.11+ |
| HTTP client | `httpx` (async) |
| HTML parser | `BeautifulSoup4` + `lxml` |
| API framework | `FastAPI` |
| ORM & DB | `SQLModel` on top of `SQLite` |
| FTS | SQLite FTS5 virtual table |
| Task scheduling | `APScheduler` (optional periodic re-crawl) |
| CLI | `typer` |

---

## Folder Layout

```
repo-upi-crawl/
│
├── PROMPT-DICTIONARY.md        # Domain terms, field names, URL conventions
├── PROMPT-SITE-STRUCTURE.md    # Target site URL map and HTML structure
├── PROMPT-PROJECT-STRUCTURE.md # This file — project layout & design decisions
├── PROMPT-SCRAPER.md           # Scraper logic, algorithms, and rules
│
├── README.md                   # User-facing usage guide
├── requirements.txt            # Pinned dependencies
├── .env.example                # Template for environment variables
│
├── app/
│   ├── main.py                 # FastAPI app factory — mounts all routers, sets up DB
│   ├── config.py               # Pydantic Settings — reads from .env
│   ├── database.py             # SQLModel engine + get_session dependency
│   ├── models.py               # All SQLModel table definitions
│   │
│   ├── scrapers/               # Pure parsing/fetching — no DB writes
│   │   ├── __init__.py
│   │   ├── base.py             # AsyncHTTPClient wrapper: rate limit, retry, UA header
│   │   ├── divisions.py        # Parse /view/divisions/ → list[DivisionSeed]
│   │   ├── subjects.py         # Parse /view/subjects/ → list[SubjectSeed]
│   │   ├── years.py            # Parse /view/year/ → list[int]
│   │   ├── creators.py         # Parse /view/creators/ → list[AuthorSeed]
│   │   ├── listing.py          # Parse any listing page → list[PaperStub]
│   │   └── paper.py            # Parse /{eprint_id}/ → PaperDetail
│   │
│   ├── crawlers/               # Orchestration — DB reads/writes, queue management
│   │   ├── __init__.py
│   │   └── orchestrator.py     # CrawlOrchestrator class — drives the full crawl
│   │
│   ├── api/                    # FastAPI routers
│   │   ├── __init__.py
│   │   ├── papers.py           # GET /papers, GET /papers/{id}, GET /papers/search
│   │   ├── divisions.py        # GET /divisions, GET /divisions/{code}/papers
│   │   ├── subjects.py         # GET /subjects, GET /subjects/{code}/papers
│   │   ├── authors.py          # GET /authors, GET /authors/{slug}/papers
│   │   └── search.py           # GET /search (cross-entity full-text)
│   │
│   └── cli.py                  # Typer CLI — `crawl`, `serve`, `reset` commands
│
├── data/
│   └── upi_repository.db       # SQLite DB — gitignored, created on first crawl
│
└── tests/
    ├── fixtures/               # Saved HTML pages for parser unit tests
    │   ├── listing_2024.html
    │   ├── detail_126926.html
    │   └── divisions.html
    ├── test_scrapers.py        # Unit tests for all scraper parse functions
    └── test_api.py             # Integration tests using FastAPI TestClient
```

---

## File Responsibilities

### `app/config.py`
- Uses `pydantic_settings.BaseSettings`
- Reads from environment / `.env` file
- Key settings:
  ```python
  BASE_URL: str = "https://repository.upi.edu"
  DB_PATH: str = "data/upi_repository.db"
  CONCURRENCY: int = 5          # asyncio.Semaphore size
  REQUEST_DELAY: float = 0.5    # seconds between requests
  CRAWL_API_KEY: str = ""       # for POST /crawl/trigger
  ```

### `app/database.py`
- Creates the SQLite engine with `check_same_thread=False`
- Calls `SQLModel.metadata.create_all(engine)` on startup
- Creates an FTS5 virtual table for `papers` (title + abstract)
- Provides `get_session()` as a FastAPI dependency

### `app/models.py`
Four table classes: `Paper`, `Author`, `Division`, `Subject`.
See `PROMPT-DICTIONARY.md` for full field definitions.
All have `model_config = {"arbitrary_types_allowed": True}`.

### `app/scrapers/base.py`
- Wraps `httpx.AsyncClient` with:
  - Shared `asyncio.Semaphore(config.CONCURRENCY)`
  - `asyncio.sleep(config.REQUEST_DELAY)` after each request
  - `User-Agent` header
  - Exponential backoff (3 retries) on 429 / 503 / network errors
- Exposes a single `async def get(url: str) -> BeautifulSoup` method

### `app/scrapers/listing.py`
- Single function: `async def scrape_listing(url: str) -> list[PaperStub]`
- Works for year, division, subject, and creator listing pages (same HTML template)
- Returns `PaperStub(eprint_id, title, author, year, degree_type)`

### `app/scrapers/paper.py`
- Single function: `async def scrape_paper(eprint_id: int) -> PaperDetail`
- Returns `PaperDetail` with all fields (see dictionary)
- Raises `ScraperError` if page returns 404 or unparseable

### `app/crawlers/orchestrator.py`
- `CrawlOrchestrator` class
- Methods:
  - `bootstrap()` — scrape all four browse indexes into DB
  - `crawl_year(year)` / `crawl_division(code)` / `crawl_author(slug)` — targeted crawls
  - `crawl_all()` — full crawl using year listing as the master source
  - `crawl_incremental()` — only visit listing pages where site count ≠ DB count
- Uses `asyncio.Queue` internally to process eprint IDs via a worker pool

### `app/cli.py`
Typer commands:
```
python -m app.cli crawl --year 2024
python -m app.cli crawl --division ILKOM
python -m app.cli crawl --author "Aam Ali Rahman"
python -m app.cli crawl --all
python -m app.cli crawl --incremental
python -m app.cli serve            # starts uvicorn
python -m app.cli reset            # drops and recreates DB
```

---

## Key Design Decisions

1. **Scrapers are pure** — they only fetch + parse, never touch the DB. The orchestrator handles all DB writes. This makes scraper functions trivially unit-testable with fixture HTML.

2. **SQLite is sufficient** — at ~90k rows with no concurrent writes during normal API operation, SQLite handles reads fine. The `PRAGMA journal_mode=WAL` is set to allow reads during crawl writes.

3. **eprintID is the deduplication key** — before fetching a detail page, the orchestrator checks `SELECT 1 FROM paper WHERE id = ?`. Already-scraped papers are skipped unless `--force` is passed.

4. **FTS5 virtual table** — created alongside the main `paper` table. Updated via trigger on `INSERT OR REPLACE INTO paper`. Enables full-text search on `title`, `abstract_id`, `abstract_en`.

5. **Year listing as the master crawl source** — it's the most complete view (all papers appear under their year). Division/subject/author listings are used for targeted crawls and for populating the reference tables, not as the primary paper discovery mechanism.

6. **No PDF downloads** — only PDF URLs are stored. Actual PDF bytes are not fetched or saved.

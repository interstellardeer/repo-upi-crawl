# Architecture

**Analysis Date:** 2025-03-24

## System Overview

```text
┌─────────────────────────────────────────────────────────────┐
│                   Entry Points (CLI / API)                  │
│          `app/cli.py`           `app/main.py`               │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Crawl Orchestrator                        │
│             `app/crawlers/orchestrator.py`                  │
│       (Queue Management, Concurrency, Worker Pool)          │
└────────┬─────────────────────────┬──────────────────────────┘
         │                         │
         ▼                         ▼
┌──────────────────┐      ┌───────────────────────────────────┐
│     Scrapers     │      │         Data Storage              │
│ `app/scrapers/`  │      │ `app/database.py`, `app/models.py`│
│ (Parsing Logic)  │      │         (SQLite / SQLModel)       │
└──────────────────┘      └───────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| API | Provides REST endpoints to query papers and trigger background crawls. | `app/main.py` |
| CLI | Provides command-line interface for manual crawls, bootstrapping, and DB resets. | `app/cli.py` |
| Orchestrator | Manages the crawl lifecycle, worker pool, and task distribution via `asyncio.Queue`. | `app/crawlers/orchestrator.py` |
| Scrapers | Specialized modules for parsing specific pages (papers, divisions, years, etc.) using BeautifulSoup. | `app/scrapers/` |
| Database | SQLModel definitions and engine configuration for SQLite storage. | `app/database.py`, `app/models.py` |
| Config | Centralized settings using Pydantic BaseSettings for environment variables. | `app/config.py` |

## Pattern Overview

**Overall:** Modular Crawler with Worker-based Orchestration.

**Key Characteristics:**
- **Asynchronous I/O:** Uses `httpx` and `asyncio` for concurrent scraping.
- **Worker Pool:** Uses a Producer-Consumer pattern with `asyncio.Queue` to manage parallel paper detail scraping.
- **Schema-First Storage:** Uses `SQLModel` (SQLAlchemy + Pydantic) for structured data storage and validation.

## Layers

**Entry Layer:**
- Purpose: Handles user interaction via HTTP or CLI commands.
- Location: `app/main.py`, `app/cli.py`
- Contains: FastAPI app, Typer CLI commands.
- Depends on: `app/crawlers/orchestrator.py`, `app/database.py`.

**Orchestration Layer:**
- Purpose: Coordinates the scraping process.
- Location: `app/crawlers/`
- Contains: Logic for discovery (finding what to crawl) and execution (worker pool).
- Depends on: `app/scrapers/`, `app/models.py`, `app/database.py`.

**Scraping Layer:**
- Purpose: Extracts structured data from raw HTML.
- Location: `app/scrapers/`
- Contains: Parsing logic for different UPI repository pages.
- Depends on: `app/scrapers/base.py`, `app/config.py`.

**Persistence Layer:**
- Purpose: Manages data storage and retrieval.
- Location: `app/database.py`, `app/models.py`, `app/api/`
- Contains: Database models, session handling, and API routers.

## Data Flow

### Primary Request Path (Crawl Trigger)

1. **Trigger:** User runs `python -m app.cli crawl` or hits `POST /crawl/trigger`.
2. **Discovery:** Orchestrator calls `scrape_years` or `scrape_listing` to get a list of eprint IDs (`app/crawlers/orchestrator.py`).
3. **Queueing:** IDs are pushed into an `asyncio.Queue` (`app/crawlers/orchestrator.py`).
4. **Processing:** Workers pull IDs from the queue and call `scrape_paper(eprint_id)` (`app/scrapers/paper.py`).
5. **Storage:** Scraped `PaperDetail` is merged into the SQLite database via `Session.merge()` (`app/crawlers/orchestrator.py`).

### Data Access Path

1. **Request:** User hits GET `/papers/{id}` (`app/api/papers.py`).
2. **Retrieval:** API uses `Session.get(Paper, id)` to fetch data from SQLite.
3. **Response:** FastAPI serializes the SQLModel instance to JSON.

**State Management:**
- Application state (crawl progress) is transient and managed by the Orchestrator's worker pool.
- Persistent state is stored in `data/db.sqlite`.

## Key Abstractions

**Scraper Modules:**
- Purpose: Encapsulate parsing logic for a single page type.
- Examples: `app/scrapers/paper.py`, `app/scrapers/divisions.py`.
- Pattern: Functional scrapers returning Dataclasses or Pydantic models.

**Worker Pool:**
- Purpose: Throttle requests to the source site while maximizing throughput.
- Implementation: `_run_worker_pool` in `app/crawlers/orchestrator.py`.

## Entry Points

**FastAPI Server:**
- Location: `app/main.py`
- Triggers: HTTP requests.
- Responsibilities: Serving data, triggering background tasks.

**Typer CLI:**
- Location: `app/cli.py`
- Triggers: Shell commands.
- Responsibilities: Manual maintenance, full crawls, DB setup.

## Architectural Constraints

- **Threading:** Single-threaded asynchronous event loop (Python `asyncio`).
- **Global state:** Database engine (`app/database.py`) and Config (`app/config.py`) are singletons shared across the app.
- **Circular imports:** Managed by local imports in entry points (e.g., `import app.crawlers.orchestrator` inside functions).

## Anti-Patterns

### Heavy Main Thread
**What happens:** Large crawls blocking the API event loop.
**Why it's wrong:** Makes the API unresponsive.
**Do this instead:** Uses `asyncio.create_task()` to run crawls in the background (`app/main.py`).

## Error Handling

**Strategy:** Graceful degradation with retries and logging.

**Patterns:**
- **Base Scraper Retries:** `app/scrapers/base.py` implements exponential backoff for HTTP failures.
- **Worker Isolation:** Errors in a single paper scrape do not crash the entire crawl.

## Cross-Cutting Concerns

**Logging:** Standard library `logging` configured in `app/main.py` and `app/cli.py`.
**Validation:** `SQLModel` (Pydantic) for data validation during scraping and API responses.
**Authentication:** Simple API Key check for crawl triggers (`app/main.py`).

---

*Architecture analysis: 2025-03-24*

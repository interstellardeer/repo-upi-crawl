# External Integrations

**Analysis Date:** 2026-05-02

## APIs & External Services

**UPI Repository (repository.upi.edu):**
- Service - Academic paper archive of Universitas Pendidikan Indonesia.
  - SDK/Client: Custom scraper using `httpx` and `BeautifulSoup4` in `app/scrapers/`.
  - Auth: None (Public access).

## Data Storage

**Databases:**
- SQLite
  - Connection: `sqlite:///{settings.DB_PATH}` (Default: `data/upi_repository.db`).
  - Client: `SQLModel` (SQLAlchemy-based).
  - Features: Uses FTS5 virtual tables for full-text search on paper titles and abstracts (`app/database.py`).

**File Storage:**
- Local filesystem only - Stores the SQLite database file in the `data/` directory.

**Caching:**
- None - Direct reads from SQLite.

## Authentication & Identity

**Auth Provider:**
- Custom (API Key)
  - Implementation: Simple API key check for crawler triggers via `CRAWL_API_KEY` environment variable in `app/main.py`.

## Monitoring & Observability

**Error Tracking:**
- None

**Logs:**
- Standard Python `logging` module configured in `app/main.py` and `app/crawlers/orchestrator.py`.

## CI/CD & Deployment

**Hosting:**
- Not specified (Portable Python application).

**CI Pipeline:**
- None detected.

## Environment Configuration

**Required env vars:**
- `BASE_URL`: The URL of the UPI Repository to scrape (Default: `https://repository.upi.edu`).
- `DB_PATH`: Path to the SQLite database file (Default: `data/upi_repository.db`).
- `CONCURRENCY`: Number of concurrent scraper workers (Default: 5).
- `REQUEST_DELAY`: Delay between requests in seconds (Default: 0.5).
- `CRAWL_API_KEY`: Key to authorize crawl triggers via API.

**Secrets location:**
- `.env` file (excluded from git).

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

---

*Integration audit: 2026-05-02*

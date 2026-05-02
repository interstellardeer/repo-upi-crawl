# Coding Conventions

**Analysis Date:** 2025-05-02

## Naming Patterns

**Files:**
- Snake case: `database.py`, `models.py`, `api/authors.py`.

**Functions:**
- Snake case: `get_soup`, `parse_divisions`, `init_db`.
- Internal helpers prefixed with underscore: `_extract_count`, `_worker`.

**Variables:**
- Snake case: `eprint_id`, `paper_count`, `settings`.
- Constants in UPPER_CASE: `HEADERS`, `NUM_WORKERS`.

**Types:**
- PascalCase for classes: `Paper`, `Division`, `Author`, `ScraperError`.
- Dataclasses for intermediate data structures: `DivisionSeed`, `PaperDetail`.

## Code Style

**Formatting:**
- No explicit tool (e.g., Black) config detected, but code is consistently formatted following PEP 8.
- 4-space indentation.

**Linting:**
- No explicit linter config detected.
- Type hints are used extensively throughout the codebase.

## Import Organization

**Order:**
1. Standard library imports (e.g., `import json`, `import asyncio`).
2. Third-party library imports (e.g., `from fastapi import FastAPI`, `from sqlmodel import Field`).
3. Local application imports (e.g., `from app.database import init_db`).

**Path Aliases:**
- None detected. Imports use the full `app` package path: `from app.models import Paper`.

## Error Handling

**Patterns:**
- Custom exception hierarchy for scrapers: `ScraperError` (base), `PageNotFoundError`.
- Exponential backoff and retries in `app/scrapers/base.py`.
- Try-except-finally blocks in async workers to ensure queue tasks are marked done.

## Logging

**Framework:** `logging` (standard library).

**Patterns:**
- Root logger configured in entry points (`app/cli.py`, `app/main.py`) using `logging.basicConfig`.
- Per-module loggers created via `log = logging.getLogger(__name__)`.
- Structured log messages using f-strings.

## Comments

**When to Comment:**
- Docstrings for public functions and classes explaining purpose and parameters.
- Inline comments for specific workarounds (e.g., SSL verification bypass in `app/scrapers/base.py`).

**JSDoc/TSDoc:**
- Not applicable (Python project). Standard Python docstrings used.

## Function Design

**Size:**
- Most functions are focused and concise (< 50 lines).
- Orchestrator functions are larger but well-structured into sub-steps.

**Parameters:**
- Type hints used for all parameters.
- Optional parameters with default values used for configuration.

**Return Values:**
- Type hints used for return values.
- Dataclasses or Seeds used for complex return structures.

## Module Design

**Exports:**
- Modules designed around specific entities (e.g., `app/api/papers.py`, `app/scrapers/paper.py`).
- `__init__.py` files used to organize package structure, though mostly empty.

**Barrel Files:**
- `app/api/__init__.py` and `app/scrapers/__init__.py` are present but don't export everything; explicit imports are preferred in `app/main.py` and `app/crawlers/orchestrator.py`.

## Scraping Patterns

**Concurrency:**
- `asyncio.Semaphore` used to limit concurrent requests.
- Concurrency level controlled via `settings.CONCURRENCY` in `app/config.py`.

**Politeness:**
- `asyncio.sleep(settings.REQUEST_DELAY)` between requests.
- Custom `User-Agent` header identifying the crawler.

**Resilience:**
- Retries with exponential backoff in `get_soup`.
- Check if paper already exists in DB before scraping detail page.

---

*Convention analysis: 2025-05-02*

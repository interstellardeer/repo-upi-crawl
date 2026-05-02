# Technology Stack

**Analysis Date:** 2026-05-02

## Languages

**Primary:**
- Python 3.10+ - Backend API, crawler logic, and CLI tool.

## Runtime

**Environment:**
- Python Runtime

**Package Manager:**
- pip - Managed via `requirements.txt`.
- Bun - User preference for execution (`bun`, `bunx`) but project is Python-based.

## Frameworks

**Core:**
- FastAPI >= 0.111.0 - Web framework for the REST API.
- Typer >= 0.12.0 - Framework for the command-line interface `app/cli.py`.

**Testing:**
- Not explicitly detected in `requirements.txt` (no pytest/unittest listed), though standard library `unittest` or `pytest` could be used.

**Build/Dev:**
- Uvicorn >= 0.29.0 - ASGI server for running the FastAPI application.

## Key Dependencies

**Critical:**
- SQLModel >= 0.0.19 - ORM for database interactions, combining SQLAlchemy and Pydantic.
- HTTPX >= 0.27.0 - Async HTTP client for scraping the UPI repository.
- BeautifulSoup4 >= 4.12.0 - HTML parsing for scraping.
- LXML >= 5.2.0 - High-performance XML/HTML parser for BeautifulSoup.

**Infrastructure:**
- Pydantic Settings >= 2.2.0 - Environment and configuration management.
- APScheduler >= 3.10.0 - Task scheduling for crawler operations.

## Configuration

**Environment:**
- Configured via `.env` file.
- Managed by `app/config.py` using `pydantic-settings`.

**Build:**
- `requirements.txt` for dependencies.

## Platform Requirements

**Development:**
- Python 3.10+
- SQLite (built-in to Python)

**Production:**
- Any environment supporting Python and SQLite.
- SQLite FTS5 extension must be available (standard in most modern SQLite builds).

---

*Stack analysis: 2026-05-02*

# Codebase Structure

**Analysis Date:** 2025-03-24

## Directory Layout

```
repo-upi-crawl/
├── app/                # Main application package
│   ├── api/            # FastAPI route handlers
│   ├── crawlers/       # Crawl orchestration logic
│   ├── scrapers/       # Site-specific parsing modules
│   ├── cli.py          # Command-line interface
│   ├── config.py       # Configuration and settings
│   ├── database.py     # Database engine and session setup
│   ├── main.py         # FastAPI entry point
│   ├── models.py       # Database table definitions
│   └── __init__.py     # Package marker
├── data/               # Persistent data storage
│   └── db.sqlite       # SQLite database file
├── prompt-history/     # AI development history and task logs
├── .env.example        # Template for environment variables
├── requirements.txt    # Python dependencies
├── start.bat/sh        # Convenience scripts for execution
└── README.md           # Project documentation
```

## Directory Purposes

**app/:**
- Purpose: Root package containing all executable code.
- Contains: Logic for the API, CLI, and crawler.
- Key files: `main.py`, `cli.py`, `models.py`.

**app/api/:**
- Purpose: REST API layer.
- Contains: FastAPI routers for different entities.
- Key files: `papers.py`, `divisions.py`, `authors.py`, `subjects.py`.

**app/crawlers/:**
- Purpose: Logic for coordinating scraping tasks.
- Contains: Orchestration flow, worker pool management, and high-level crawl functions.
- Key files: `orchestrator.py`.

**app/scrapers/:**
- Purpose: Low-level data extraction from HTML.
- Contains: Specific parsers for various repository page types and a shared base client.
- Key files: `base.py`, `paper.py`, `listing.py`, `creators.py`.

**data/:**
- Purpose: Storage for the local SQLite database.
- Contains: `db.sqlite`.

**prompt-history/:**
- Purpose: Documentation of the development process and past AI interactions.
- Contains: Markdown files and images documenting feature implementation.

## Key File Locations

**Entry Points:**
- `app/main.py`: The FastAPI web server.
- `app/cli.py`: The command-line interface for the crawler.

**Configuration:**
- `app/config.py`: Loads environment variables and manages global settings.
- `.env`: (Ignored) Local secrets and overrides.

**Core Logic:**
- `app/crawlers/orchestrator.py`: The "brain" of the crawler.
- `app/scrapers/base.py`: Handles HTTP requests, rate limiting, and retries.

**Testing:**
- `test_authors.py`: Simple standalone test for author scraping.

## Naming Conventions

**Files:**
- `snake_case.py`: Standard Python module naming (e.g., `listing.py`).

**Directories:**
- `snake_case/`: Standard package naming (e.g., `app/api/`).

**Classes/Types:**
- `PascalCase`: SQLModel tables and Scraper dataclasses (e.g., `PaperDetail`).

## Where to Add New Code

**New Feature (Crawl Mode):**
- Primary code: `app/crawlers/orchestrator.py`
- CLI command: `app/cli.py`
- API endpoint: `app/main.py`

**New Entity (Scraping):**
- Parser: `app/scrapers/` (create a new module)
- Model: `app/models.py`
- API Router: `app/api/`

**Utilities:**
- Shared helpers: `app/scrapers/base.py` or a new `app/utils.py` if needed.

## Special Directories

**data/:**
- Purpose: Holds the SQLite database.
- Generated: Yes (by `init_db` or `reset` command).
- Committed: No (only `.gitignore` is committed).

**prompt-history/:**
- Purpose: Tracking AI-assisted development steps.
- Committed: Yes.

---

*Structure analysis: 2025-03-24*

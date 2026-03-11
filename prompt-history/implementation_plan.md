# UPI Repository Scraper API — Implementation Plan

Build a Python-based web scraper that crawls [repository.upi.edu](https://repository.upi.edu) and exposes the data through a clean, self-documenting REST API (FastAPI). This gives developers programmatic access to ~90,000 academic papers from Universitas Pendidikan Indonesia.

---

## Site Structure (Research Results)

The site runs **EPrints** (open-source repository software). Key URL patterns:

| URL | What it contains |
|---|---|
| `/view/divisions/` | Full faculty → department tree with paper counts |
| `/view/subjects/` | Library of Congress subject classification tree |
| `/view/year/` | Years from 1989–2026 with paper counts |
| `/view/creators/` | Full A-Z author index with per-author paper counts |
| `/view/year/{year}.html` | All papers for a year, grouped A-Z by author |
| `/view/divisions/{code}/` | All papers in a division |
| `/view/subjects/{code}.html` | All papers under a subject |
| `/view/creators/{encoded_name}.html` | All papers by a specific author |
| `/{eprint_id}/` | Individual paper detail page |

**Paper detail page fields**: title, author(s), year, degree type (S1/S2/S3), abstract (Indonesian + English), subject codes, division/department, PDF chapter download links, eprint URL.

---

## Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Language | **Python 3.11+** | Best ecosystem for scraping + ML downstream |
| HTTP client | **httpx** (async) | Async, connection pooling, rate limiting |
| HTML parsing | **BeautifulSoup4 + lxml** | Battle-tested for EPrints HTML |
| API framework | **FastAPI** | Auto OpenAPI docs, async, fast |
| Database | **SQLite via SQLModel** | Zero-ops, embedded, good for read-heavy API |
| Caching | SQLite-backed (paper rows cached permanently) | Avoid re-scraping already-seen eprintIDs |
| Task scheduling | **APScheduler** (optional background re-crawl) | Keep data fresh without manual runs |
| Package manager | **uv** or pip + `requirements.txt` | Simple, reproducible |

---

## Project Structure

```
repo-upi-crawl/
├── README.md
├── requirements.txt
├── .env.example
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Settings (rate limits, DB path, base URL)
│   ├── database.py          # SQLModel engine + session factory
│   ├── models.py            # SQLModel ORM models (Paper, Division, Subject, Author)
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── base.py          # Async HTTP client wrapper with rate limiting
│   │   ├── divisions.py     # Scrape /view/divisions/ tree
│   │   ├── subjects.py      # Scrape /view/subjects/ tree
│   │   ├── years.py         # Scrape /view/year/ index
│   │   ├── creators.py      # Scrape /view/creators/ author index
│   │   ├── listing.py       # Scrape listing pages (year/division/subject/creator)
│   │   └── paper.py         # Scrape individual paper detail page
│   ├── crawlers/
│   │   ├── __init__.py
│   │   └── orchestrator.py  # Manages crawl queue, deduplication, progress
│   ├── api/
│   │   ├── __init__.py
│   │   ├── papers.py        # /papers endpoints
│   │   ├── divisions.py     # /divisions endpoints
│   │   ├── subjects.py      # /subjects endpoints
│   │   ├── authors.py       # /authors endpoints
│   │   └── search.py        # /search endpoint (full-text over SQLite FTS5)
│   └── cli.py               # CLI: `python -m app.cli crawl --year 2024`
├── data/
│   └── upi_repository.db    # SQLite database (gitignored)
└── tests/
    ├── test_scrapers.py
    └── test_api.py
```

---

## Data Models

```python
# models.py (SQLModel)

class Division(SQLModel, table=True):
    code: str = Field(primary_key=True)   # e.g. "FPEB"
    name: str                              # e.g. "Fakultas Pendidikan Ekonomi dan Bisnis"
    parent_code: str | None = None        # FK to self (for sub-divisions)
    paper_count: int = 0
    url: str

class Subject(SQLModel, table=True):
    code: str = Field(primary_key=True)   # e.g. "LB1603"
    name: str                              # e.g. "Secondary Education"
    paper_count: int = 0
    url: str

class Author(SQLModel, table=True):
    slug: str = Field(primary_key=True)   # URL-encoded name key, e.g. "Aam_Ali_Rahman=3A-=3A=3A"
    name: str                              # e.g. "Aam Ali Rahman"
    paper_count: int = 0
    url: str                               # e.g. "/view/creators/Aam_Ali_Rahman..."

class Paper(SQLModel, table=True):
    id: int = Field(primary_key=True)     # EPrint ID (e.g. 126926)
    title: str
    author: str
    author_slug: str | None = None        # FK to Author.slug
    year: int | None = None
    degree_type: str | None = None        # "S1", "S2", "S3", "D3"
    abstract_id: str | None = None        # Indonesian abstract
    abstract_en: str | None = None        # English abstract
    division_code: str | None = None
    subject_codes: str | None = None      # JSON array of subject codes
    pdf_urls: str | None = None           # JSON array of PDF download links
    eprint_url: str
    scraped_at: datetime
```

---

## API Endpoints

### Papers
| Method | Path | Description |
|---|---|---|
| `GET` | `/papers` | List papers (paginated). Query: `year`, `division`, `subject`, `degree_type`, `page`, `limit` |
| `GET` | `/papers/{id}` | Get full detail of one paper |
| `GET` | `/papers/search?q=...` | Full-text search across title + abstract (SQLite FTS5) |

### Divisions
| Method | Path | Description |
|---|---|---|
| `GET` | `/divisions` | Full division tree |
| `GET` | `/divisions/{code}/papers` | Papers in a specific division (paginated) |

### Subjects
| Method | Path | Description |
|---|---|---|
| `GET` | `/subjects` | Full subject list |
| `GET` | `/subjects/{code}/papers` | Papers under a subject (paginated) |

### Authors
| Method | Path | Description |
|---|---|---|
| `GET` | `/authors` | Full author list (paginated). Query: `q` for name search |
| `GET` | `/authors/{slug}/papers` | All papers by a specific author |

### Meta / Crawl
| Method | Path | Description |
|---|---|---|
| `GET` | `/stats` | Total papers, authors, divisions, subjects, last crawl time |
| `POST` | `/crawl/trigger` | Trigger a background crawl (protected by API key) |

---

## Scraper Design

### Rate Limiting & Politeness
- `asyncio.Semaphore(5)` — max 5 concurrent requests
- `asyncio.sleep(0.5)` between requests per domain
- `User-Agent: UPI-Repository-Crawler/1.0 (research; contact: your@email.com)`
- Respect `robots.txt` (EPrints typically allows crawling)
- Exponential backoff on 429/503 errors

### Crawl Strategy
1. **Bootstrap**: Scrape `/view/divisions/`, `/view/years/`, and `/view/creators/` to build seed URLs and the author index
2. **Listing crawl**: For each year/division/author listing page, extract all `/{eprint_id}/` links
3. **Detail crawl**: Visit each eprint ID not yet in the DB, parse full metadata
4. **Incremental**: On subsequent runs, only scrape years/divisions/authors where `paper_count` differs from DB count

### CLI Usage
```bash
# Crawl all papers from 2024
python -m app.cli crawl --year 2024

# Crawl a specific division
python -m app.cli crawl --division ILKOM

# Crawl all papers by a specific author
python -m app.cli crawl --author "Aam Ali Rahman"

# Full crawl (slow — ~90k papers)
python -m app.cli crawl --all

# Start the API server
uvicorn app.main:app --reload
```

---

## Verification Plan

### Manual Tests

1. **Run a small crawl**
   ```bash
   cd repo-upi-crawl
   python -m app.cli crawl --division ILKOM
   ```
   Expected: ~816 papers scraped, stored in `data/upi_repository.db`

2. **Start the API server**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   Open browser → `http://localhost:8000/docs` — verify OpenAPI UI renders

3. **Test paper listing endpoint**
   ```bash
   curl "http://localhost:8000/papers?division=ILKOM&limit=5"
   ```
   Expected: JSON with 5 papers, each having `id`, `title`, `author`, `year`

4. **Test full-text search**
   ```bash
   curl "http://localhost:8000/papers/search?q=machine+learning"
   ```
   Expected: Papers with "machine learning" in title or abstract

5. **Test single paper detail**
   ```bash
   curl "http://localhost:8000/papers/126926"
   ```
   Expected: Full metadata for eprint 126926 including abstract, subjects, PDF links

6. **Test author lookup**
   ```bash
   curl "http://localhost:8000/authors?q=Aam+Ali"
   curl "http://localhost:8000/authors/Aam_Ali_Rahman=3A-=3A=3A/papers"
   ```
   Expected: Author record with `paper_count`, then their papers list

### Automated Tests (to be written)
- `tests/test_scrapers.py` — Unit tests for HTML parsing functions using saved fixture HTML
- `tests/test_api.py` — Integration tests using FastAPI `TestClient` against a seeded in-memory DB

---

## User Review Required

> [!IMPORTANT]
> **Ethical/Legal consideration**: Web scraping a university repository is generally acceptable for research/academic tools, but please check UPI's Terms of Service. The plan includes polite crawling (rate limits, proper User-Agent, robots.txt respect) to avoid server strain.

> [!NOTE]
> **PDF download**: The plan includes PDF URLs in the database but does **not** download the actual PDF files. Downloading all ~90k papers' PDFs would use a huge amount of disk space. PDFs can be fetched on-demand via the API if needed.

> [!NOTE]
> **Full crawl time**: Scraping all ~90,000 papers at a polite rate (~5 req/s) will take **~5 hours**. For development, start with a single year or division. The incremental crawl mode handles keeping data fresh.

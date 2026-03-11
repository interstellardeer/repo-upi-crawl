# UPI Repository Scraper API

A web scraper and REST API for [repository.upi.edu](https://repository.upi.edu) — the academic paper archive of Universitas Pendidikan Indonesia (~90,000 papers).

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env if needed (defaults work out of the box)
```

### 3. Crawl some data

```bash
# Option A — crawl a single division (fast, ~1-5 min)
python -m app.cli crawl --division ILKOM

# Option B — crawl a specific year
python -m app.cli crawl --year 2024

# Option C — crawl by author name
python -m app.cli crawl --author "Aam Ali Rahman"

# Option D — full crawl (slow, ~5 hours for all ~90k papers)
python -m app.cli crawl --all

# Option E — incremental update (only new/changed)
python -m app.cli crawl --incremental
```

### 4. Start the API server

```bash
python -m app.cli serve
# or with auto-reload for development:
python -m app.cli serve --reload
```

API docs available at: **http://localhost:8000/docs**

---

## API Endpoints

### Papers

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/papers` | List papers (paginated) |
| `GET` | `/papers/{id}` | Full paper detail |
| `GET` | `/papers/search?q=...` | Full-text search (title + abstract) |

**Filter params for `/papers`**: `year`, `division`, `subject`, `degree_type`, `author_slug`, `page`, `limit`

### Divisions

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/divisions` | All faculties and departments |
| `GET` | `/divisions/{code}` | A single division |
| `GET` | `/divisions/{code}/papers` | Papers in that division |

### Subjects

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/subjects` | All Library of Congress subject codes |
| `GET` | `/subjects/{code}/papers` | Papers under that subject |

### Authors

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/authors?q=name` | Search authors |
| `GET` | `/authors/{slug}/papers` | Papers by a specific author |

### Meta

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/stats` | Total counts and last crawl time |
| `POST` | `/crawl/trigger` | Trigger crawl via API (requires API key) |

---

## Example Requests

```bash
# Get 5 papers from 2024, Computer Science division
curl "http://localhost:8000/papers?year=2024&division=ILKOM&limit=5"

# Full-text search
curl "http://localhost:8000/papers/search?q=machine+learning"

# Get a specific paper
curl "http://localhost:8000/papers/126926"

# All divisions
curl "http://localhost:8000/divisions"

# Search for an author
curl "http://localhost:8000/authors?q=Aam+Ali"

# Stats
curl "http://localhost:8000/stats"
```

---

## CLI Reference

```
python -m app.cli crawl [OPTIONS]
  --year INTEGER       Crawl a specific year
  --division TEXT      Crawl a division (use the code, e.g. ILKOM)
  --author TEXT        Crawl by author slug or name
  --all                Full crawl (all years)
  --incremental        Only crawl what has changed
  --bootstrap          Only update reference tables (no papers)

python -m app.cli serve [OPTIONS]
  --host TEXT          Bind host [default: 0.0.0.0]
  --port INTEGER       Bind port [default: 8000]
  --reload             Enable auto-reload

python -m app.cli reset [--force]
  Drop and recreate the database
```

---

## Data Model

| Table | Key fields |
|---|---|
| `paper` | `id` (eprint ID), `title`, `author`, `year`, `degree_type`, `abstract_id`, `abstract_en`, `division_code`, `subject_codes` (JSON), `pdf_urls` (JSON) |
| `division` | `code`, `name`, `parent_code`, `paper_count` |
| `subject` | `code`, `name`, `paper_count` |
| `author` | `slug`, `name`, `paper_count` |

Full-text search is powered by SQLite FTS5 on `title`, `abstract_id`, and `abstract_en`.

---

## Politeness Policy

The crawler is designed to be respectful of the server:
- Max **5 concurrent requests** 
- **0.5 second delay** between requests
- Proper `User-Agent` header
- Exponential backoff on errors (1s, 2s, 4s)
- Never re-fetches papers already in the database

## Division Codes Reference

Some useful division codes for quick testing:

| Code | Name |
|---|---|
| `ILKOM` | Ilmu Komputer (Computer Science) |
| `PENDILKOM` | Pendidikan Ilmu Komputer |
| `FPEB` | Fakultas Pendidikan Ekonomi dan Bisnis |
| `FIP` | Fakultas Ilmu Pendidikan |
| `FPIPS` | Fakultas Pendidikan Ilmu Pengetahuan Sosial |
| `FPMIPA` | Fakultas Pendidikan Matematika dan IPA |
| `geo` | Pendidikan Geografi S1 |
| `SPS` | Sekolah Pasca Sarjana |

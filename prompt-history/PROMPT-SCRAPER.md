# PROMPT-SCRAPER.md
# Scraper Logic & Algorithms

Use this file as shared context when prompting an LLM to implement or modify the scraper.
It defines the exact parsing rules, crawl algorithms, error handling, and politeness policies.

---

## Guiding Principles

1. **Be polite** — max 5 concurrent requests, 0.5 s delay between requests, correct User-Agent
2. **Be incremental** — never re-fetch a detail page already in the DB (check `id` first)
3. **Be resilient** — retry on transient errors, log and skip on parse errors
4. **Be pure** — scraper functions only parse HTML and return dataclasses; no DB I/O inside scrapers

---

## HTTP Client (`app/scrapers/base.py`)

```python
import asyncio
import httpx
from bs4 import BeautifulSoup
from app.config import settings

_semaphore = asyncio.Semaphore(settings.CONCURRENCY)

async def get_soup(url: str, retries: int = 3) -> BeautifulSoup:
    """Fetch a URL and return a parsed BeautifulSoup document."""
    async with _semaphore:
        for attempt in range(retries):
            try:
                async with httpx.AsyncClient(
                    headers={"User-Agent": "UPI-Repository-Crawler/1.0"},
                    follow_redirects=True,
                    timeout=30.0,
                ) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    await asyncio.sleep(settings.REQUEST_DELAY)
                    return BeautifulSoup(response.text, "lxml")
            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                if attempt == retries - 1:
                    raise
                wait = 2 ** attempt  # 1s, 2s, 4s
                await asyncio.sleep(wait)
```

---

## Scraper 1 — Divisions (`app/scrapers/divisions.py`)

**Input**: `GET /view/divisions/`
**Output**: `list[DivisionSeed]`

```python
@dataclass
class DivisionSeed:
    code: str        # extracted from href, e.g. "FPEB"
    name: str        # link text
    paper_count: int
    url: str
    parent_code: str | None
```

### Parsing algorithm
1. Find all `<a>` tags whose `href` matches `/view/divisions/{code}/`
2. Extract `code` from href by stripping prefix and trailing `/`
3. Extract `name` from link text (strip whitespace)
4. Extract `paper_count` from the text node immediately following the `</a>`: regex `\((\d+)\)`
5. Determine `parent_code` by tracking nesting depth in the `<ul>` tree:
   - Top-level `<li>` → `parent_code = None`
   - Nested `<li>` → `parent_code = code` of the closest ancestor `<li>` that has a division link

---

## Scraper 2 — Subjects (`app/scrapers/subjects.py`)

**Input**: `GET /view/subjects/`
**Output**: `list[SubjectSeed]`

```python
@dataclass
class SubjectSeed:
    code: str
    name: str
    paper_count: int
    url: str
```

### Parsing algorithm
1. Find all `<a>` tags whose `href` matches `/view/subjects/{code}.html`
2. Extract `code` from href (strip prefix + `.html`)
3. Extract `name` from link text
4. Extract `paper_count` from the trailing `(N)` text node

---

## Scraper 3 — Years (`app/scrapers/years.py`)

**Input**: `GET /view/year/`
**Output**: `list[tuple[int, int]]` — (year, paper_count)

### Parsing algorithm
1. Find all `<a>` tags whose `href` matches `/view/year/{year}.html`
2. Extract `year` as integer from href
3. Extract `paper_count` from trailing `(N)` text
4. Deduplicate (the page renders the list twice — once as `<ul>` and once as plain links)

---

## Scraper 4 — Creators (`app/scrapers/creators.py`)

**Input**: `GET /view/creators/`
**Output**: `list[AuthorSeed]`

```python
@dataclass
class AuthorSeed:
    slug: str        # URL-encoded key extracted from href
    name: str        # display name (strip trailing ", -")
    paper_count: int
    url: str
```

### Parsing algorithm
1. Find all `<a>` tags whose `href` matches `/view/creators/{slug}.html`
2. Extract `slug` from href (strip prefix + `.html`)
3. Extract `name` from link text — strip trailing `, -` or `, (-)` artifact
4. Extract `paper_count` from trailing `(N)` text
5. **Important**: the creators page is very large (500+ chunks). Fetch the full page once; do not paginate.

---

## Scraper 5 — Listing Pages (`app/scrapers/listing.py`)

Works for: `/view/year/{year}.html`, `/view/divisions/{code}/`, `/view/subjects/{code}.html`, `/view/creators/{slug}.html`

**Input**: any listing page URL
**Output**: `list[PaperStub]`

```python
@dataclass
class PaperStub:
    eprint_id: int
    title: str
    author: str
    year: int | None
    degree_type: str | None   # "S1", "S2", "S3", "D3", or None
```

### Parsing algorithm
For each entry block in the listing page:
1. Find the title `<a>` tag with `href` matching `/{eprint_id}/` (integer path)
2. `eprint_id` = int(href.strip("/"))
3. `title` = link text (strip whitespace)
4. `author` = text before the `(YYYY)` in the containing `<p>` or block — regex: `^(.*?)\s*\(\d{4}\)`
5. `year` = integer inside `(YYYY)` — regex: `\((\d{4})\)`
6. `degree_type` = first token of the text after the title `<a>` — match against `{"S1", "S2", "S3", "D3", "D-3"}`; normalize `"D-3"` → `"D3"`

### Edge cases
- Some entries have no year (historical papers) — `year = None`
- Some entries have no recognized degree prefix — `degree_type = None`
- Title may contain parentheses — do not confuse `(2024)` mid-title with the year; the year `(YYYY)` is always at the citation level, not inside the `<a>`

---

## Scraper 6 — Paper Detail (`app/scrapers/paper.py`)

**Input**: eprint_id (int)
**Output**: `PaperDetail`

```python
@dataclass
class PaperDetail:
    eprint_id: int
    title: str
    author: str
    year: int | None
    degree_type: str | None
    abstract_id: str | None
    abstract_en: str | None
    division_code: str | None
    subject_codes: list[str]
    pdf_urls: list[str]
    eprint_url: str
```

### Parsing algorithm
1. Fetch `https://repository.upi.edu/{eprint_id}/`
2. `title` = text of `<h1>` tag
3. `author`, `year`, `degree_type` — parse from the citation `<p>` (same regex as listing)
4. **Abstract**:
   - Find the `<div>` or `<section>` containing a heading with text `"Abstract"`
   - Collect all `<p>` text nodes inside it
   - If exactly one paragraph → `abstract_id = text`, `abstract_en = None`
   - If two paragraphs → first is Indonesian, second is English (heuristic: first is usually longer)
   - If neither, search for a `<div class="ep_block">` with "Abstract" label
5. **Subject codes**:
   - Find all `<a href="...view/subjects/{code}...">` links
   - Extract unique codes in order of appearance
6. **Division code**:
   - Find `<a href="...view/divisions/{code}/...">` link
   - Extract the deepest (most specific) division code (last one in the list)
7. **PDF URLs**:
   - Find all `<a>` links whose `href` ends in `.pdf` and contains `repository.upi.edu/{eprint_id}/`
   - Normalize to `https://`
   - Return as ordered list (Title first, then chapters, then appendix)
8. `eprint_url` = `https://repository.upi.edu/{eprint_id}/`

### Error handling
- `404` response → raise `PaperNotFoundError(eprint_id)` — orchestrator logs and skips
- Parse failure on title → raise `ScraperParseError` — orchestrator logs and skips
- Missing abstract → return `None` for both fields (not an error)

---

## Crawl Orchestrator (`app/crawlers/orchestrator.py`)

### Worker pool pattern
```python
async def _worker(queue: asyncio.Queue, session):
    while True:
        eprint_id = await queue.get()
        if eprint_id is None:
            break
        if paper_exists(session, eprint_id):
            queue.task_done()
            continue
        try:
            detail = await scrape_paper(eprint_id)
            upsert_paper(session, detail)
        except Exception as e:
            log.warning(f"Failed {eprint_id}: {e}")
        queue.task_done()
```

### `crawl_year(year: int)`
1. Scrape `/view/year/{year}.html` → list of `PaperStub`s
2. Enqueue all `eprint_id`s into the worker queue
3. Workers fetch detail pages and write to DB

### `crawl_division(code: str)`
1. Scrape `/view/divisions/{code}/` → list of `PaperStub`s
2. Same worker pool pattern as `crawl_year`

### `crawl_author(slug: str)`
1. Scrape `/view/creators/{slug}.html` → list of `PaperStub`s
2. Same worker pool pattern

### `crawl_all()`
1. Bootstrap: scrape all four browse indexes, populate `Division`, `Subject`, `Author` tables
2. Scrape year listing for every year (1989–2026) as the master paper discovery source
3. All eprint IDs discovered are deduplicated globally in the queue

### `crawl_incremental()`
1. For each year row in DB: compare `paper_count` (from site) vs `COUNT(*)` from DB
2. If site count > DB count → re-scrape that year's listing and enqueue missing IDs
3. Same for divisions and authors (useful for catching papers missed via year route)

---

## Politeness Policy

| Rule | Value |
|---|---|
| Max concurrent requests | 5 (`asyncio.Semaphore`) |
| Delay between requests | 0.5 seconds |
| User-Agent | `UPI-Repository-Crawler/1.0 (academic research)` |
| Retry on 429 / 503 | Yes — exponential backoff: 1s, 2s, 4s |
| Retry on network timeout | Yes — same backoff |
| Retry on 404 | No — log and skip |
| Retry on parse error | No — log and skip |
| robots.txt | Fetch and cache on startup; abort if `/` is disallowed |

---

## Logging

Use Python `logging` with these levels:
- `INFO` — crawl started/finished, paper saved, division/year completed
- `WARNING` — 404s, parse errors, retries
- `ERROR` — unrecoverable failures (DB write errors)
- `DEBUG` — per-request URL, response time, semaphore queue depth

Recommended format:
```
%(asctime)s [%(levelname)s] %(name)s: %(message)s
```

---

## Testing Scrapers

Each scraper function takes a `BeautifulSoup` object as input (after fetching).
To unit-test without network:
1. Save real HTML pages to `tests/fixtures/`
2. In tests, open the fixture file with `BeautifulSoup(open("...").read(), "lxml")`
3. Pass the soup object directly to the parse function
4. Assert on the returned dataclass fields

Example:
```python
def test_parse_listing_2024():
    soup = BeautifulSoup(open("tests/fixtures/listing_2024_partial.html").read(), "lxml")
    stubs = parse_listing(soup)
    assert stubs[0].eprint_id == 126926
    assert stubs[0].degree_type == "S1"
    assert stubs[0].year == 2024
```

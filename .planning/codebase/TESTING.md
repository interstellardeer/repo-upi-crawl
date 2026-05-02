# Testing Patterns

**Analysis Date:** 2025-05-02

## Test Framework

**Runner:**
- No formal test runner (e.g., `pytest`, `unittest`, `nose2`) is currently configured in the project.

**Assertion Library:**
- None detected.

**Run Commands:**
```bash
# Manual verification of specific components using ad-hoc scripts
python test_authors.py

# Manual verification of crawler via CLI
python -m app.cli crawl --division ILKOM

# Manual verification of API via FastAPI Swagger UI
python -m app.cli serve --reload
# Then visit http://localhost:8000/docs
```

## Test File Organization

**Location:**
- Ad-hoc test scripts are located in the project root.

**Naming:**
- `test_*.py` (e.g., `test_authors.py`).

**Structure:**
```
[project-root]/
└── test_authors.py    # Ad-hoc verification script
```

## Test Structure

**Suite Organization:**
Not applicable as there is no formal suite. Ad-hoc scripts typically follow this pattern:
```python
import asyncio
from app.config import settings
from app.scrapers.creators import scrape_creators

async def fetch():
    try:
        results = await scrape_creators(settings.BASE_URL)
        print(f"Count: {len(results)}")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(fetch())
```

**Patterns:**
- **Manual Verification:** Running a crawler command for a small subset (e.g., one division or one year) and checking the SQLite database or logs for results.
- **Log Inspection:** Monitoring `INFO` and `WARNING` logs during crawls to identify failed requests or parsing errors.

## Mocking

**Framework:** None used.

**Patterns:**
- No mocking patterns observed. Scrapers hit the live repository URL during manual tests.

**What to Mock:**
- Recommendations for future tests: Mock `httpx.AsyncClient.get` responses with HTML samples to test parsers in isolation.

## Fixtures and Factories

**Test Data:**
- The project currently relies on live data from `repository.upi.edu`.

**Location:**
- Not applicable.

## Coverage

**Requirements:** None enforced.

**View Coverage:**
- Not applicable.

## Test Types

**Unit Tests:**
- None detected. Parsers are currently coupled with network fetching in many scraper modules.

**Integration Tests:**
- Ad-hoc scripts like `test_authors.py` serve as manual integration tests, verifying the end-to-end flow from network request to data extraction.

**E2E Tests:**
- Manual verification of the API using tools like `curl` or Postman against a running server populated with crawled data.

## Common Patterns

**Async Testing:**
- Using `asyncio.run()` to execute async scraper functions in standalone scripts.

**Error Testing:**
- Manually triggering crawls for non-existent years or divisions to verify that `PageNotFoundError` is handled correctly.

## Recommendations

1.  **Introduce Pytest:** Configure `pytest` and `pytest-asyncio` for formal testing.
2.  **Separate Parsing from Fetching:** Refactor scrapers to separate the logic that fetches HTML from the logic that parses it. This allows testing the parser with static HTML fixtures without making network requests.
3.  **API Testing:** Use `fastapi.testclient.TestClient` or `httpx.AsyncClient` with `app` to test API endpoints.
4.  **Database Isolation:** Use a temporary in-memory SQLite database for tests to avoid polluting the production `data/db.sqlite`.

---

*Testing analysis: 2025-05-02*

# Codebase Concerns

**Analysis Date:** 2025-05-02

## Tech Debt

**API Response Inconsistency:**
- Issue: The `/papers/search` endpoint returns raw database rows where JSON columns (`subject_codes`, `pdf_urls`) are strings. The `/papers` and `/papers/{id}` endpoints use a helper function to parse these into proper JSON lists.
- Files: `app/api/papers.py`
- Impact: Frontend or API consumers receive inconsistent data structures depending on whether they use search or list.
- Fix approach: Refactor `search_papers` to use the `_paper_to_dict` helper or a Pydantic model with validators.

**Fragile FTS5 Triggers:**
- Issue: SQLite FTS5 triggers are hardcoded raw SQL strings in the database initialization. They are not managed by an ORM or migration tool.
- Files: `app/database.py`
- Impact: If the `paper` table schema changes (e.g., adding or renaming columns used in search), the triggers will break or fail to sync data silently.
- Fix approach: Move to a migration tool like Alembic and use more robust sync logic or abstract the FTS management.

**Heavy Bootstrap Process:**
- Issue: The `bootstrap` function scrapes all divisions, subjects, and authors in one go. For large repositories, the "Authors" list can be extremely large, leading to long execution times and potential rate limiting.
- Files: `app/crawlers/orchestrator.py`, `app/scrapers/creators.py`
- Impact: Makes initial setup and full crawls very slow and resource-intensive.
- Fix approach: Implement incremental bootstrapping or paginate author scraping more conservatively.

## Known Bugs

**Abstract Language Misidentification:**
- Symptoms: `abstract_id` and `abstract_en` are assigned based purely on the number of paragraphs found under the "Abstract" heading.
- Files: `app/scrapers/paper.py`
- Trigger: If a paper has only one abstract and it's in English, it will be assigned to `abstract_id` (assumed to be Indonesian). If it has 3 paragraphs, the 3rd is ignored.
- Workaround: None currently.

**Single vs Multiple Chapter Links:**
- Symptoms: The scraper collects all PDF links matching an eprint ID pattern. It does not distinguish between a single "Full Paper" PDF and multiple "Chapter" PDFs.
- Files: `app/scrapers/paper.py`
- Trigger: EPrints records where the thesis is split into multiple files (Cover, Chapter 1, Chapter 2, etc.).
- Workaround: The system stores all URLs in a list, but the UI/consumer must guess which one is the main document.

## Security Considerations

**Disabled SSL Verification:**
- Risk: The HTTP client is configured with `verify=False`, making it vulnerable to Man-in-the-Middle (MITM) attacks.
- Files: `app/scrapers/base.py`
- Current mitigation: None. It was implemented to bypass local SSL certificate issues common in Windows Python environments.
- Recommendations: Enable verification and provide a path to a CA bundle if necessary.

**Unprotected API:**
- Risk: The FastAPI application has no authentication or rate limiting.
- Files: `app/main.py`
- Current mitigation: None.
- Recommendations: Add API key authentication or OAuth2, and implement rate limiting (e.g., using `slowapi`).

## Performance Bottlenecks

**Sequential Year Crawling:**
- Problem: `crawl_all` and `crawl_incremental` process years one by one.
- Files: `app/crawlers/orchestrator.py`
- Cause: The logic uses a loop over years, calling `crawl_year` (which itself is concurrent) sequentially.
- Improvement path: Allow multiple years to be queued or processed concurrently, within the limits of the overall concurrency semaphore.

## Fragile Areas

**Scraper Regex and DOM Selectors:**
- Files: `app/scrapers/paper.py`, `app/scrapers/creators.py`, `app/scrapers/listing.py`
- Why fragile: They rely on specific HTML structure (e.g., `h1`, specific `<p>` tag text length, regex for citation parsing). EPrints themes can vary or be updated.
- Safe modification: Use more specific CSS classes where available or implement multiple parsing strategies for different EPrints versions/themes.
- Test coverage: Gaps in testing with diverse HTML samples.

## Test Coverage Gaps

**Scraper Logic:**
- What's not tested: Parsing logic for complex paper pages, especially those with multiple authors, unusual citation formats, or multiple PDF attachments.
- Files: `app/scrapers/*.py`
- Risk: Site structure changes could break the scraper without immediate notice until the database is found to be empty or corrupted.
- Priority: High

---

*Concerns audit: 2025-05-02*

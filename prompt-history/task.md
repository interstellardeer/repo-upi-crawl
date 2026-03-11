# UPI Repository Scraper API — Task Checklist

## Planning
- [x] Explore site structure (divisions, subjects, years, listing pages, paper detail pages)
- [x] Understand data model (author, title, abstract, subjects, division, downloads, eprintID)
- [x] Write implementation plan
- [x] Get user review/approval on plan (creators endpoint added)
- [x] Create PROMPT-DICTIONARY.md
- [x] Create PROMPT-SITE-STRUCTURE.md
- [x] Create PROMPT-PROJECT-STRUCTURE.md
- [x] Create PROMPT-SCRAPER.md

## Execution
- [/] Initialize Python project with FastAPI + dependencies
- [/] Build core scrapers (divisions, subjects, years, creators, listing, paper detail)
- [/] Implement rate-limiting + polite crawling (async httpx + BeautifulSoup)
- [/] Build SQLite cache layer (SQLModel)
- [/] Build FastAPI REST endpoints
- [/] Write README with usage guide

## Verification
- [ ] Manual test: run scraper against a small division slice
- [ ] Manual test: verify API endpoints return correct data
- [ ] Manual test: verify OpenAPI docs render correctly at /docs

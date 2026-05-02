# Issue: Multiple Chapter Links Not Correctly Captured or Handled

## Description
When crawling a paper that has multiple document parts (e.g., Cover, Chapter 1, Chapter 2, Appendix), the system should capture all of them. 

Example: `https://repository.upi.edu/130502/` has 7 PDF links.

## Current State
- The scraper `app/scrapers/paper.py` uses a regex to find `.pdf` links in the HTML body.
- While the current regex `rf"/{eprint_id}/\d+/.+\.pdf"` seems to match the links in the example, there might be cases where links are structured differently or missed.
- The Full Text reader link (`https://reader-repository.upi.edu/...`) is not captured.
- API consistency: The `/papers/search` endpoint returns JSON fields as strings instead of parsed lists, which may lead clients to incorrectly process the `pdf_urls` list.

## Proposed Changes
1. **Scraper Improvement**: 
   - Supplement the PDF discovery by also looking at `<meta name="eprints.document_url">` tags, which are a more reliable source for EPrints documents.
   - Capture the "Full Text" reader link if available.
2. **API Refactor**:
   - Ensure `/papers/search` uses the same `_paper_to_dict` helper as other endpoints to return proper JSON arrays for `pdf_urls` and `subject_codes`.
3. **Database/Model**:
   - Verify that multiple URLs are indeed stored and retrieved correctly (my initial research says yes, but we should ensure the UI/API consumes them properly).

## Success Criteria
- [x] Scraper captures all 7 PDFs for eprint 130502.
- [x] Scraper captures the "Full Text" reader link.
- [x] `/papers/search` returns `pdf_urls` as a JSON array (list), not a string.

## Resolution
- **Scraper Fix**: Enhanced `app/scrapers/paper.py` to check `<meta name="eprints.document_url">` tags and reader-repository links. This ensures all document parts and the interactive reader are captured.
- **API Consistency Fix**: Updated `app/api/papers.py` to use `model_validate` and `_paper_to_dict` in the `/search` endpoint. This ensures JSON fields are returned as proper lists, fixing inconsistent behavior between list and search results.

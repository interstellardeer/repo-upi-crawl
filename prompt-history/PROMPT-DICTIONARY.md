# PROMPT-DICTIONARY.md
# UPI Repository — Data Dictionary & Glossary

Use this file as shared context when prompting an LLM to work on this project.
It defines all domain terms, field names, URL patterns, and data conventions.

---

## Platform

The site (`repository.upi.edu`) runs **EPrints** — an open-source academic repository system.
EPrints structures all content around **eprints** (individual submissions), each identified by a
unique integer ID. Browse pages are server-rendered HTML with predictable URL conventions.

---

## Term Glossary

| Term | Meaning |
|---|---|
| **eprint** | A single repository submission — one thesis, paper, or report |
| **eprint_id** | The integer primary key of an eprint, e.g. `126926` |
| **division** | A faculty or department within UPI, identified by a short `code` (e.g. `FPEB`, `ILKOM`) |
| **division code** | URL-safe string used as the division identifier in browse URLs |
| **subject** | A Library of Congress classification label (e.g. `LB1603 — Secondary Education`) |
| **subject code** | The LC classification code used in the URL (e.g. `LB1603`) |
| **creator / author** | The student or researcher who submitted the paper |
| **creator slug** | The URL-encoded author string used in browse URLs (e.g. `Aam_Ali_Rahman=3A-=3A=3A`) |
| **degree_type** | Academic degree level: `S1` (undergraduate), `S2` (masters), `S3` (doctoral), `D3` (diploma) |
| **abstract_id** | The Indonesian-language abstract text |
| **abstract_en** | The English-language abstract text (not always present) |
| **pdf_urls** | JSON array of per-chapter PDF download URLs (Title, Chapter1–5, Appendix) |
| **listing page** | A browse HTML page that lists many eprints (by year, division, subject, or creator) |
| **detail page** | The individual page at `/{eprint_id}/` containing full metadata for one eprint |
| **scraped_at** | ISO 8601 timestamp recording when a row was last written to the local DB |

---

## Field Conventions

### Paper fields

| Field | Type | Notes |
|---|---|---|
| `id` | `int` | EPrint ID — stable, permanent |
| `title` | `str` | Full thesis/paper title (often in Indonesian) |
| `author` | `str` | Human-readable name, e.g. `"A'isy Muhammad Zain"` |
| `author_slug` | `str` | FK to `Author.slug` — the URL-encoded key |
| `year` | `int \| None` | Submission/publication year |
| `degree_type` | `str \| None` | `"S1"`, `"S2"`, `"S3"`, `"D3"` — parsed from the listing blurb |
| `abstract_id` | `str \| None` | Indonesian abstract (scraped from detail page) |
| `abstract_en` | `str \| None` | English abstract (scraped from detail page, may be absent) |
| `division_code` | `str \| None` | E.g. `"geo"` (Pendidikan Geografi S1) |
| `subject_codes` | `str` | JSON array, e.g. `["L", "LB", "LB1603"]` |
| `pdf_urls` | `str` | JSON array of absolute PDF URLs |
| `eprint_url` | `str` | Canonical URL, e.g. `http://repository.upi.edu/126926/` |
| `scraped_at` | `datetime` | UTC timestamp |

### Author fields

| Field | Type | Notes |
|---|---|---|
| `slug` | `str` | URL-encoded name key (primary key), parsed from href |
| `name` | `str` | Display name, e.g. `"Aam Ali Rahman"` |
| `paper_count` | `int` | As shown on the browse page |
| `url` | `str` | Full URL to the author's paper listing page |

### Division fields

| Field | Type | Notes |
|---|---|---|
| `code` | `str` | Short code used in the URL (primary key), e.g. `"FPEB"`, `"geo"` |
| `name` | `str` | Full name, e.g. `"Pendidikan Geografi-S1"` |
| `parent_code` | `str \| None` | FK to self — set when this is a sub-division |
| `paper_count` | `int` | As shown on the browse page |
| `url` | `str` | Full browse URL for this division |

### Subject fields

| Field | Type | Notes |
|---|---|---|
| `code` | `str` | LC code used in the URL (primary key), e.g. `"LB1603"` |
| `name` | `str` | Full LC label, e.g. `"Secondary Education. High schools"` |
| `paper_count` | `int` | As shown on the browse page |
| `url` | `str` | Full browse URL for this subject |

---

## URL Encoding Notes

EPrints uses a non-standard URL encoding in creator slugs:
- `:` → `=3A`
- `.` → `=2E`
- `'` → `=27`
- `(` / `)` → `=28` / `=29`
- `_` separates words in the slug

Example: author `"A.A. Gde Somatanaya"` → slug `A=2EA=2E_Gde_Somatanaya=3A-=3A=3A`

Division codes are used verbatim as URL path segments. Some codes contain `=5F` (`_`) or `=2E` (`.`).

---

## Listing Page Format

Listing pages (year, division, subject, creator) share a common HTML structure:
- Eprints are listed as `<div class="ep_summary_content">` blocks
- Each block contains: author names, year (in parentheses), a linked title, and degree type
- Title links point to `/{eprint_id}/` (relative URL)
- Degree type is embedded in text like `"S1 thesis, Universitas Pendidikan Indonesia"`

---

## Detail Page Format

Individual eprint pages at `https://repository.upi.edu/{eprint_id}/` contain:
- `<h1>` — paper title
- Citation line — author, year, degree type, institution
- `<div class="ep_block">` with label `"Abstract"` — abstract text (may be bilingual)
- Subject links — `<a href="/view/subjects/...">` elements
- Division links — `<a href="/view/divisions/...">` elements
- PDF download links — `<a href="http://repository.upi.edu/{id}/{n}/filename.pdf">`
- Full-text reader link — `https://reader-repository.upi.edu/index.php/display/file/{id}`

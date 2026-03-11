# PROMPT-SITE-STRUCTURE.md
# Target Site Structure — repository.upi.edu

Use this file as shared context when prompting an LLM to work on the scraper.
It maps every relevant URL pattern and HTML structure on the target site.

---

## Base URL

```
https://repository.upi.edu
```

All relative links on the site are relative to this base.
Some internal links use `http://` (non-TLS) — normalize all to `https://`.

---

## Browse Entry Points

| URL | Page Title | Description |
|---|---|---|
| `/view/divisions/` | Browse by Division and Year | Hierarchical faculty/department tree |
| `/view/subjects/` | Browse by Subject | Library of Congress classification tree |
| `/view/year/` | Browse by Year | Years from 1989–2026 with paper counts |
| `/view/creators/` | Browse by Author | Full A-Z alphabetical author index |

---

## URL Patterns

### 1. Division Listing
```
/view/divisions/{division_code}/
```
- Returns all papers in that division, sorted A-Z by author
- `division_code` examples: `FPEB`, `geo`, `ILKOM`, `T=5FPGSD`
- Some codes are URL-encoded (e.g. `=5F` = `_`, `=2E` = `.`)

### 2. Subject Listing
```
/view/subjects/{subject_code}.html
```
- Returns all papers under that LC subject code
- `subject_code` examples: `LB1603`, `QA75`, `BF`, `L1`

### 3. Year Listing
```
/view/year/{year}.html
```
- Returns all papers published in that year, sorted A-Z by author
- Example: `/view/year/2024.html`

### 4. Author/Creator Listing
```
/view/creators/{creator_slug}.html
```
- Returns all papers by a single author
- `creator_slug` uses EPrints' custom encoding (see PROMPT-DICTIONARY.md)
- Example: `/view/creators/Aam_Ali_Rahman=3A-=3A=3A.html`

### 5. Paper Detail Page
```
/{eprint_id}/
```
- The canonical page for a single paper
- `eprint_id` is a plain integer, e.g. `/126926/`
- Also accessible as `http://repository.upi.edu/{eprint_id}/`

### 6. PDF Downloads
```
/{eprint_id}/{file_index}/{filename}.pdf
```
- File index is a small integer (1, 7, 8, 9, 10, 11, 12…)
- Common filename suffixes: `_Title.pdf`, `_Chapter1.pdf` through `_Chapter5.pdf`, `_Appendix.pdf`

### 7. Full-Text Reader
```
https://reader-repository.upi.edu/index.php/display/file/{eprint_id}
```
- Opens the paper in a JS-based reader (requires login for some papers)

---

## HTML Structure — Listing Pages (Year / Division / Subject / Creator)

All listing pages share the same EPrints template.

### Author entry block
```html
<div class="ep_summary_content_left">
  <!-- Author name, year, linked title, degree type line -->
  <p>
    <strong>Author Name, -</strong> (2024)
    <a href="/126926/">Paper Title Here.</a>
    S1 thesis, Universitas Pendidikan Indonesia.
  </p>
</div>
```

### Key extraction targets per entry
| Data | Where to find it |
|---|---|
| eprint_id | href of the title `<a>` tag → strip leading `/` and trailing `/` |
| title | text of the title `<a>` tag |
| author | text before the year `(YYYY)` |
| year | integer inside `(YYYY)` |
| degree_type | first token of the text after the `<a>` tag, e.g. `S1`, `S2`, `S3`, `D3` |

---

## HTML Structure — Paper Detail Page (`/{eprint_id}/`)

### Title
```html
<h1 class="ep_title...">Paper Title</h1>
```

### Citation line
```html
<p class="ep_block">
  Author Name, - (2024) <em>Paper Title</em>. S1 thesis, Universitas Pendidikan Indonesia.
</p>
```

### Abstract section
```html
<div class="ep_block">
  <h2>Abstract</h2>
  <p>Indonesian abstract text...</p>
  <p>English abstract text...</p>
</div>
```
> The Indonesian abstract comes first; an English translation may follow.
> They can be in the same `<div>` or adjacent `<p>` tags.

### Subject links
```html
<a href="http://repository.upi.edu/view/subjects/LB1603.html">
  LB1603 Secondary Education. High schools
</a>
```

### Division links
```html
<a href="http://repository.upi.edu/view/divisions/geo/">
  Pendidikan Geografi-S1
</a>
```

### PDF download links
```html
<a href="http://repository.upi.edu/126926/1/S_GEO_2006321_Title.pdf">
  Download (954kB)
</a>
<a href="http://repository.upi.edu/126926/8/S_GEO_2006321_Chapter1.pdf">
  Download (333kB)
</a>
```

### Author profile link
```html
<a href="http://repository.upi.edu/cgi/users/home?screen=User::View&amp;userid=209876">
  A'isy Muhammad Zain
</a>
```

---

## HTML Structure — Divisions Browse (`/view/divisions/`)

The page lists divisions in a nested `<ul>` tree:
```html
<ul>
  <li>
    <a href="/view/divisions/FPEB/">Fakultas Pendidikan Ekonomi dan Bisnis</a> (8322)
    <ul>
      <li>
        <a href="/view/divisions/AK/">Akuntansi (non kependidikan)</a> (1260)
      </li>
      ...
    </ul>
  </li>
  ...
</ul>
```
- Top-level `<li>` = Faculty (e.g. FPEB, FIP, FPIPS…)
- Nested `<li>` = Department/program (child of a faculty)
- Paper count is in `(N)` immediately after the `</a>` tag

---

## HTML Structure — Creators Browse (`/view/creators/`)

Listed alphabetically in sections (`A...`, `B...`, etc.):
```html
<h2>A...</h2>
<ul>
  <li>
    <a href="/view/creators/Aam_Ali_Rahman=3A-=3A=3A.html">Aam Ali Rahman, -</a> (16)
  </li>
  ...
</ul>
```
- Author display name is the link text (may include trailing `, -`)
- Slug is extracted from the `href` (strip `/view/creators/` and `.html`)
- Paper count is in `(N)` after the `</a>` tag

---

## Scale & Timing Reference

| Dimension | Value |
|---|---|
| Total papers | ~90,735 |
| Total authors | ~70,000+ (unique slugs on /view/creators/) |
| Total divisions | ~200+ (including sub-divisions) |
| Total subject codes | ~250+ LC codes |
| Years covered | 1989–2026 |
| Avg papers per year (recent) | ~5,000–7,000 |
| Avg listing page parse time | ~50–200 ms (network) |
| Estimated full crawl time at 5 req/s | ~5 hours |

---

## robots.txt

EPrints installations typically serve:
```
User-agent: *
Disallow: /cgi/
Disallow: /perl/
Allow: /
```
The browse and eprint detail pages are allowed. Always fetch and verify before crawling.

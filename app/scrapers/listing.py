import re
from dataclasses import dataclass
from typing import Optional

from bs4 import BeautifulSoup

DEGREE_TYPES = {"S1", "S2", "S3", "D3", "D4", "D-3", "D-4"}
DEGREE_NORM = {"D-3": "D3", "D-4": "D4"}

# Match BOTH relative (/126926/) and absolute (http://repository.upi.edu/126926/) eprint URLs
_EPRINT_HREF_REL = re.compile(r"^/(\d+)/?$")
_EPRINT_HREF_ABS = re.compile(r"repository\.upi\.edu/(\d+)/?$")
_YEAR_PAT = re.compile(r"\((\d{4})\)")
_AUTHOR_PAT = re.compile(r"^(.*?)\s*\(\d{4}\)", re.DOTALL)


@dataclass
class PaperStub:
    eprint_id: int
    title: str
    author: str
    year: Optional[int]
    degree_type: Optional[str]


def _extract_eprint_id(href: str) -> Optional[int]:
    """Return integer eprint ID from either relative or absolute eprint URL, or None."""
    m = _EPRINT_HREF_REL.match(href) or _EPRINT_HREF_ABS.search(href)
    return int(m.group(1)) if m else None


def parse_listing(soup: BeautifulSoup) -> list[PaperStub]:
    """Parse any listing page (year/division/subject/creator) into PaperStub list."""
    results: list[PaperStub] = []
    seen: set[int] = set()

    for a in soup.find_all("a", href=True):
        eprint_id = _extract_eprint_id(a["href"])
        if eprint_id is None or eprint_id in seen:
            continue
        seen.add(eprint_id)

        title = a.get_text(" ", strip=True)
        if not title:
            continue

        # Get the surrounding block text to extract author and year
        parent = a.find_parent(["p", "div", "li", "td"])
        full_text = parent.get_text(" ", strip=True) if parent else ""

        # Extract year
        year_match = _YEAR_PAT.search(full_text)
        year = int(year_match.group(1)) if year_match else None

        # Extract author: text before (YYYY)
        author_match = _AUTHOR_PAT.match(full_text)
        author = author_match.group(1).strip().rstrip(",") if author_match else ""

        # Extract degree_type: first word after the title in the parent text
        title_end = full_text.find(title)
        after_title = full_text[title_end + len(title):].strip() if title_end >= 0 else ""
        degree_type: Optional[str] = None
        first_token = after_title.split()[0] if after_title else ""
        if first_token in DEGREE_TYPES:
            degree_type = DEGREE_NORM.get(first_token, first_token)

        results.append(PaperStub(
            eprint_id=eprint_id,
            title=title,
            author=author,
            year=year,
            degree_type=degree_type,
        ))

    return results


async def scrape_listing(url: str) -> list[PaperStub]:
    """Fetch and parse any listing page URL."""
    from app.scrapers.base import get_soup
    soup = await get_soup(url)
    return parse_listing(soup)

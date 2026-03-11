import json
import re
from dataclasses import dataclass, field
from typing import Optional

from bs4 import BeautifulSoup

from app.scrapers.base import PageNotFoundError, ScraperError, get_soup
from app.config import settings

_YEAR_PAT = re.compile(r"\((\d{4})\)")
_DEGREE_TYPES = {"S1", "S2", "S3", "D3", "D4", "D-3", "D-4"}
_DEGREE_NORM = {"D-3": "D3", "D-4": "D4"}


@dataclass
class PaperDetail:
    eprint_id: int
    title: str
    author: str
    year: Optional[int]
    degree_type: Optional[str]
    abstract_id: Optional[str]
    abstract_en: Optional[str]
    division_code: Optional[str]
    subject_codes: list[str] = field(default_factory=list)
    pdf_urls: list[str] = field(default_factory=list)
    eprint_url: str = ""


def _normalize_url(url: str) -> str:
    """Always return https:// URLs."""
    return url.replace("http://", "https://")


def parse_paper(soup: BeautifulSoup, eprint_id: int, base_url: str) -> PaperDetail:
    # --- Title ---
    h1 = soup.find("h1")
    if not h1:
        raise ScraperError(f"No <h1> found for eprint {eprint_id}")
    title = h1.get_text(" ", strip=True)

    # --- Citation line: author, year, degree ---
    # The citation <p> is a plain unclassed paragraph: "Author, - (YYYY) Title. Degree thesis, ..."
    # Scan all <p> tags for the one containing "(YYYY)"
    citation_text = ""
    year_m_global = None
    for p_tag in soup.find_all("p"):
        p_text = p_tag.get_text(" ", strip=True)
        if _YEAR_PAT.search(p_text) and len(p_text) > 20:
            citation_text = p_text
            year_m_global = _YEAR_PAT.search(p_text)
            break

    year = int(year_m_global.group(1)) if year_m_global else None

    author = ""
    if citation_text:
        author_m = re.match(r"^(.*?)\s*\(\d{4}\)", citation_text, re.DOTALL)
        if author_m:
            author = author_m.group(1).strip().rstrip(",").strip().rstrip("-").strip().rstrip(",").strip()

    degree_type: Optional[str] = None
    for token in citation_text.split():
        if token in _DEGREE_TYPES:
            degree_type = _DEGREE_NORM.get(token, token)
            break

    # --- Abstract ---
    abstract_id: Optional[str] = None
    abstract_en: Optional[str] = None

    # EPrints uses: <h2>Abstract</h2> followed by sibling <p> tags with the actual text
    abs_heading = soup.find(lambda tag: tag.name in ("h2", "h3")
                            and tag.get_text(strip=True).lower() == "abstract")
    if abs_heading:
        paragraphs = []
        for sib in abs_heading.next_siblings:
            if hasattr(sib, "name"):
                if sib.name in ("h2", "h3"):
                    break  # Next major section — stop
                if sib.name == "p":
                    text = sib.get_text(" ", strip=True)
                    if text:
                        paragraphs.append(text)
        if len(paragraphs) == 1:
            abstract_id = paragraphs[0]
        elif len(paragraphs) >= 2:
            abstract_id = paragraphs[0]
            abstract_en = paragraphs[1]

    # --- Subject codes ---
    subject_codes: list[str] = []
    seen_subjects: set[str] = set()
    for a in soup.find_all("a", href=re.compile(r"/view/subjects/")):
        href = a["href"]
        code = href.rstrip("/").split("/")[-1].replace(".html", "")
        if code and code not in seen_subjects:
            seen_subjects.add(code)
            subject_codes.append(code)

    # --- Division code ---
    division_code: Optional[str] = None
    div_links = soup.find_all("a", href=re.compile(r"/view/divisions/[^/]+/?$"))
    if div_links:
        # Use the most specific (last) division link
        href = div_links[-1]["href"]
        division_code = href.rstrip("/").split("/")[-1]

    # --- PDF URLs ---
    pdf_urls: list[str] = []
    for a in soup.find_all("a", href=re.compile(rf"/{eprint_id}/\d+/.+\.pdf")):
        raw_href = a["href"]
        normalized = _normalize_url(raw_href if raw_href.startswith("http") else base_url + raw_href)
        if normalized not in pdf_urls:
            pdf_urls.append(normalized)

    eprint_url = f"{base_url}/{eprint_id}/"

    return PaperDetail(
        eprint_id=eprint_id,
        title=title,
        author=author,
        year=year,
        degree_type=degree_type,
        abstract_id=abstract_id,
        abstract_en=abstract_en,
        division_code=division_code,
        subject_codes=subject_codes,
        pdf_urls=pdf_urls,
        eprint_url=eprint_url,
    )


async def scrape_paper(eprint_id: int) -> PaperDetail:
    url = f"{settings.BASE_URL}/{eprint_id}/"
    soup = await get_soup(url)
    return parse_paper(soup, eprint_id, settings.BASE_URL)

import re
from dataclasses import dataclass, field
from typing import Optional

from bs4 import BeautifulSoup


@dataclass
class DivisionSeed:
    code: str
    name: str
    paper_count: int
    url: str
    parent_code: Optional[str]


def _extract_code_from_href(href: str) -> str:
    """Extract division code from /view/divisions/{code}/ href."""
    return href.rstrip("/").split("/")[-1]


def _extract_count(text: str) -> int:
    """Extract the (N) count from surrounding text node."""
    m = re.search(r"\((\d+)\)", text)
    return int(m.group(1)) if m else 0


def parse_divisions(soup: BeautifulSoup, base_url: str) -> list[DivisionSeed]:
    """Parse /view/divisions/ page and return a flat list of DivisionSeed."""
    results: list[DivisionSeed] = []

    def _walk(ul_tag, parent_code: Optional[str]) -> None:
        for li in ul_tag.find_all("li", recursive=False):
            a = li.find("a", recursive=False)
            if not a or not a.has_attr("href"):
                continue
            href = a["href"]

            code = _extract_code_from_href(href)
            
            # Root division seems to be just 'divisions' in the UI, we still record it 
            # so the tree is fully intact if needed
            name = a.get_text(strip=True)

            after = a.next_sibling or ""
            count = _extract_count(str(after))

            # Compose absolute URL properly (href is usually relative e.g., 'FPEB/')
            if href.startswith("http"):
                url = href
            elif href.startswith("/"):
                url = base_url + href
            else:
                url = f"{base_url}/view/divisions/{href}"

            results.append(DivisionSeed(code=code, name=name, paper_count=count, url=url, parent_code=parent_code))

            # Handle children (can be multiple ul siblings for sub-departments)
            for child_ul in li.find_all("ul", recursive=False):
                _walk(child_ul, parent_code=code)

    main_div = soup.find('div', class_='ep_view_menu')
    if main_div:
        # Sometimes there's multiple top-level ULs if they are sibling elements
        for top_ul in main_div.find_all('ul', recursive=False):
            _walk(top_ul, parent_code=None)

    # Fallback: if the above found nothing, just scrape all division links flat
    if not results:
        for a in soup.find_all("a", href=re.compile(r"/view/divisions/[^/]+/?$")):
            href = a["href"]
            code = _extract_code_from_href(href)
            name = a.get_text(strip=True)
            after = a.next_sibling or ""
            count = _extract_count(str(after))
            url = href if href.startswith("http") else base_url + href
            results.append(DivisionSeed(code=code, name=name, paper_count=count, url=url, parent_code=None))

    return results


async def scrape_divisions(base_url: str) -> list[DivisionSeed]:
    from app.scrapers.base import get_soup
    url = f"{base_url}/view/divisions/"
    soup = await get_soup(url)
    return parse_divisions(soup, base_url)

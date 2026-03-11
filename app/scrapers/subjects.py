import re
from dataclasses import dataclass

from bs4 import BeautifulSoup


@dataclass
class SubjectSeed:
    code: str
    name: str
    paper_count: int
    url: str


def _extract_count(text: str) -> int:
    m = re.search(r"\((\d+)\)", text)
    return int(m.group(1)) if m else 0


def parse_subjects(soup: BeautifulSoup, base_url: str) -> list[SubjectSeed]:
    results: list[SubjectSeed] = []
    seen: set[str] = set()

    # Subjects list is inside ep_view_page or ep_view_menu
    main_div = soup.find('div', class_=re.compile(r"ep_view_(page|menu)"))
    if not main_div:
        return results

    # Links are like href="LB.html" or href="AC.html"
    for a in main_div.find_all("a", href=re.compile(r"^[A-Z0-9-]+\.html$")):
        href = a["href"]
        # skip the index link itself if present
        if href == "subjects.html":
            continue

        # code = strip .html
        code = href.replace(".html", "")
        if code in seen:
            continue
        seen.add(code)
        
        name = a.get_text(strip=True)
        after = a.next_sibling or ""
        count = _extract_count(str(after))
        url = base_url + "/view/subjects/" + href
        results.append(SubjectSeed(code=code, name=name, paper_count=count, url=url))

    return results


async def scrape_subjects(base_url: str) -> list[SubjectSeed]:
    from app.scrapers.base import get_soup
    url = f"{base_url}/view/subjects/"
    soup = await get_soup(url)
    return parse_subjects(soup, base_url)

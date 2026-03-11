import re
from dataclasses import dataclass

from bs4 import BeautifulSoup


@dataclass
class YearEntry:
    year: int
    paper_count: int


def _extract_count(text: str) -> int:
    m = re.search(r"\((\d+)\)", text)
    return int(m.group(1)) if m else 0


def parse_years(soup: BeautifulSoup, base_url: str) -> list[YearEntry]:
    results: list[YearEntry] = []
    seen: set[int] = set()

    main_div = soup.find('div', class_=re.compile(r"ep_view_(page|menu)"))
    if not main_div:
        return results

    for a in main_div.find_all("a", href=re.compile(r"^\d{4}\.html$")):
        href = a["href"]
        year_str = href.replace(".html", "")
        try:
            year = int(year_str)
        except ValueError:
            continue
        if year in seen:
            continue
        seen.add(year)
        after = a.next_sibling or ""
        count = _extract_count(str(after))
        results.append(YearEntry(year=year, paper_count=count))

    results.sort(key=lambda e: e.year, reverse=True)
    return results


async def scrape_years(base_url: str) -> list[YearEntry]:
    from app.scrapers.base import get_soup
    url = f"{base_url}/view/year/"
    soup = await get_soup(url)
    return parse_years(soup, base_url)

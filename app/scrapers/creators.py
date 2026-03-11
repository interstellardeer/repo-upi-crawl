import re
from dataclasses import dataclass

from bs4 import BeautifulSoup


@dataclass
class AuthorSeed:
    slug: str
    name: str
    paper_count: int
    url: str


def _extract_count(text: str) -> int:
    m = re.search(r"\((\d+)\)", text)
    return int(m.group(1)) if m else 0


def _clean_name(raw: str) -> str:
    """Strip trailing ', -' or ', (-)' artifact from creator display names."""
    return re.sub(r",\s*[-\(\)]+\s*$", "", raw).strip()


def parse_creators(soup: BeautifulSoup, base_url: str) -> list[AuthorSeed]:
    results: list[AuthorSeed] = []
    seen: set[str] = set()

    main_div = soup.find('div', class_=re.compile(r"ep_view_(page|menu)"))
    if not main_div:
        return results

    for a in main_div.find_all("a", href=re.compile(r"^.+\.html$")):
        href = a["href"]
        # Skip pagination links like 'index.B.html' and root like 'creators.html'
        if href.startswith('index.') or href == 'creators.html':
            continue

        slug = href.replace(".html", "")
        if slug in seen:
            continue
        seen.add(slug)
        raw_name = a.get_text(strip=True)
        name = _clean_name(raw_name)
        after = a.next_sibling or ""
        count = _extract_count(str(after))
        url = base_url + "/view/creators/" + href
        results.append(AuthorSeed(slug=slug, name=name, paper_count=count, url=url))

    return results


async def scrape_creators(base_url: str) -> list[AuthorSeed]:
    import asyncio
    from app.scrapers.base import get_soup
    
    url = f"{base_url}/view/creators/"
    soup = await get_soup(url)
    
    # Parse the first page (usually "A")
    all_seeds = parse_creators(soup, base_url)
    
    # Find pagination links: <a href="index.B.html">B</a>
    main_div = soup.find('div', class_=re.compile(r"ep_view_(page|menu)"))
    if main_div:
        toolbox = main_div.find('div', class_="ep_toolbox")
        if toolbox:
            # Gather subsequent URLs to fetch
            subsequent_urls = []
            for a in toolbox.find_all("a", href=re.compile(r"^index\.[A-Z]\.html$")):
                subsequent_urls.append(f"{base_url}/view/creators/{a['href']}")
            
            # Fetch them concurrently
            async def _fetch_and_parse(u: str) -> list[AuthorSeed]:
                s = await get_soup(u)
                return parse_creators(s, base_url)
                
            tasks = [_fetch_and_parse(u) for u in subsequent_urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for res in results:
                if isinstance(res, list):
                    all_seeds.extend(res)
                    
    # Deduplicate seeds by slug just in case
    unique_seeds = {seed.slug: seed for seed in all_seeds}.values()
    return list(unique_seeds)

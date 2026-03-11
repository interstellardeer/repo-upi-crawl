import asyncio
import logging

import httpx
from bs4 import BeautifulSoup

from app.config import settings

log = logging.getLogger(__name__)

_semaphore = asyncio.Semaphore(settings.CONCURRENCY)

HEADERS = {
    "User-Agent": "UPI-Repository-Crawler/1.0 (academic research; github.com/repo-upi-crawl)"
}


async def get_soup(url: str, retries: int = 3) -> BeautifulSoup:
    """Fetch a URL with rate-limiting, retries, and politeness delay."""
    async with _semaphore:
        last_exc: Exception | None = None
        for attempt in range(retries):
            try:
                async with httpx.AsyncClient(
                    headers=HEADERS,
                    follow_redirects=True,
                    timeout=30.0,
                    verify=False,  # Bypass SSL cert issues common on Windows Python
                ) as client:
                    response = await client.get(url)
                    if response.status_code == 404:
                        raise PageNotFoundError(url)
                    response.raise_for_status()
                    await asyncio.sleep(settings.REQUEST_DELAY)
                    return BeautifulSoup(response.text, "lxml")
            except PageNotFoundError:
                raise
            except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                last_exc = exc
                wait = 2 ** attempt
                log.warning(f"[attempt {attempt+1}/{retries}] {url} → {exc}. Retrying in {wait}s")
                await asyncio.sleep(wait)
        raise ScraperError(f"Failed to fetch {url} after {retries} attempts") from last_exc


class ScraperError(Exception):
    pass


class PageNotFoundError(ScraperError):
    pass

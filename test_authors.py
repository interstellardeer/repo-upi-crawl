import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
from app.config import settings
from app.scrapers.creators import scrape_creators

async def fetch():
    try:
        auths = await scrape_creators(settings.BASE_URL)
        print(f"Total authors extracted: {len(auths)}")
        for a in auths[:3]:
            print(f"Author: {a.name} ({a.slug}) - {a.paper_count} papers")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(fetch())

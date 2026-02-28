"""
Scrape NCTO member directory.

https://ncto.org/about/members/
"""

import re
import time
from typing import Iterator

import requests
from bs4 import BeautifulSoup

from .base import normalize_record

BASE = "https://ncto.org/about/members"
SOURCE = "NCTO"
SOURCE_URL = "https://ncto.org/about/members/"


def _fetch(url: str, timeout: int = 30) -> str:
    r = requests.get(url, timeout=timeout, headers={"User-Agent": "CottonSearching/1.0"})
    r.raise_for_status()
    return r.text


def _parse_page(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not href.startswith("https://ncto.org/") or href == "https://ncto.org/about/members/":
            continue
        if "/about/members" in href and "/page/" in href:
            continue
        name = (a.get_text() or "").strip()
        if not name or len(name) < 2:
            continue
        if name in ("Learn More", "Contact Us", "Join Now", "MENU"):
            continue
        # Find council type from nearby text
        parent = a.find_parent()
        council = ""
        if parent:
            txt = parent.get_text()
            if "Council:" in txt:
                m = re.search(r"Council:\s*(\w+(?:\s+\w+)*)", txt)
                if m:
                    council = m.group(1).strip()
        # Map council to products
        council_products = {
            "Yarn": "Yarn spinning",
            "Fiber": "Fiber",
            "Fabric & Home Products": "Fabric; Home products",
            "Finished Textile & Apparel": "Finished textile; Apparel",
            "Industry Support": "Textile industry support",
        }
        products = council_products.get(council, council) if council else "Textile industry"
        rows.append(
            normalize_record(
                name=name,
                city="",
                state="",
                url=href,
                website=href,
                buy_link=href,
                type="manufacturer",
                notes=f"NCTO: {council}" if council else "NCTO member",
                products=products,
                source=SOURCE,
                source_url=SOURCE_URL,
            )
        )
    return rows


def scrape(delay: float = 1.0) -> Iterator[dict]:
    """Scrape NCTO member directory (all pages)."""
    seen = set()
    page = 1
    while True:
        url = f"{BASE}/" if page == 1 else f"{BASE}/page/{page}/"
        try:
            html = _fetch(url)
        except Exception as e:
            yield {"_error": str(e), "_url": url}
            break
        rows = _parse_page(html)
        if not rows:
            break
        for r in rows:
            key = r["name"]
            if key not in seen:
                seen.add(key)
                yield r
        # Check for next page
        if not re.search(rf'page/{page + 1}/', html):
            break
        page += 1
        time.sleep(delay)

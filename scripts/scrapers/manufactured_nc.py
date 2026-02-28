"""
Scrape NC manufacturers from ManufacturedNC (filter by NAICS 313, 314, 315 for textile/apparel).

https://www.manufacturednc.com/
"""

import re
import time
from typing import Iterator

import requests
from bs4 import BeautifulSoup

from .base import normalize_record

BASE = "https://www.manufacturednc.com"
SOURCE = "ManufacturedNC"
SOURCE_URL = f"{BASE}/"

# NAICS: 313=Textile Mills, 314=Textile Product Mills, 315=Apparel
NAICS_APPAREL = "315"
NAICS_TEXTILE = "313,314"


def _fetch(url: str, timeout: int = 30) -> str:
    r = requests.get(url, timeout=timeout, headers={"User-Agent": "CottonSearching/1.0"})
    r.raise_for_status()
    return r.text


def _parse_search(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    # Structure: "City, NC" then "Company Name" then "(Visit Page)" link to manufacturednc.com/Slug
    for link in soup.find_all("a", href=True):
        href = link.get("href", "")
        if "manufacturednc.com" not in href or "/search" in href or "/contact" in href or href.rstrip("/") == "https://www.manufacturednc.com":
            continue
        if "(Visit Page)" not in (link.get_text() or ""):
            continue
        # Company name from previous h3/h4
        name = ""
        prev = link.find_previous(["h2", "h3", "h4"])
        if prev:
            name = (prev.get_text() or "").replace("(Visit Page)", "").strip()
        if not name or len(name) < 2:
            continue
        # City from text before name (e.g. "Asheboro, NC")
        city = ""
        for p in link.find_all_previous():
            txt = (p.get_text() or "").strip()
            if txt.endswith(", NC"):
                city = txt.replace(", NC", "").strip()
                break
            if p.name in ("h2", "h3", "h4") and p != prev:
                break
        url = href if href.startswith("http") else f"{BASE}{href}" if href.startswith("/") else f"{BASE}/{href}"
        # NAICS 315=Apparel, 313=Textile mills, 314=Textile product mills
        products = "Apparel; Textiles; NC manufacturer"
        rows.append(
            normalize_record(
                name=name,
                city=city,
                state="NC",
                url=url,
                website=url,
                buy_link=url,
                type="manufacturer",
                notes="ManufacturedNC",
                products=products,
                source=SOURCE,
                source_url=SOURCE_URL,
            )
        )
    return rows


def _parse_search_v2(html: str) -> list[dict]:
    """Parse search results - alternate structure."""
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    # Look for "City, NC" headers and company links
    for el in soup.find_all(["h2", "h3", "h4", "a"]):
        if el.name in ("h2", "h3", "h4"):
            text = (el.get_text() or "").strip()
            if text.endswith(", NC"):
                city = text.replace(", NC", "").strip()
                # Next siblings: company links
                for sib in el.find_next_siblings():
                    if sib.name == "a" and sib.get("href"):
                        href = sib["href"]
                        if "/company/" in href or "/supplier/" in href:
                            name = (sib.get_text() or "").strip()
                            name = re.sub(r"\s*\(Visit Page\)\s*$", "", name, flags=re.I).strip()
                            if name:
                                url = href if href.startswith("http") else f"{BASE}{href}" if href.startswith("/") else f"{BASE}/{href}"
                                rows.append(
                                    normalize_record(
                                        name=name,
                                        city=city,
                                        state="NC",
                                        url=url,
                                        website=url,
                                        buy_link=url,
                                        type="manufacturer",
                                        notes="ManufacturedNC",
                                        source=SOURCE,
                                        source_url=SOURCE_URL,
                                    )
                                )
                    elif sib.name in ("h2", "h3", "h4"):
                        break
        elif el.name == "a" and el.get("href"):
            href = el["href"]
            if "/company/" in href or "/supplier/" in href:
                name = (el.get_text() or "").strip()
                name = re.sub(r"\s*\(Visit Page\)\s*$", "", name, flags=re.I).strip()
                if name:
                    parent = el.find_parent()
                    city = ""
                    if parent:
                        for p in parent.find_all_previous(limit=5):
                            t = (p.get_text() or "").strip()
                            if t.endswith(", NC"):
                                city = t.replace(", NC", "").strip()
                                break
                    url = href if href.startswith("http") else f"{BASE}{href}" if href.startswith("/") else f"{BASE}/{href}"
                    rows.append(
                        normalize_record(
                            name=name,
                            city=city,
                            state="NC",
                            url=url,
                            website=url,
                            buy_link=url,
                            type="manufacturer",
                            notes="ManufacturedNC",
                            source=SOURCE,
                            source_url=SOURCE_URL,
                        )
                    )
    return rows


def scrape(naics: str = "313,314,315", delay: float = 1.0) -> Iterator[dict]:
    """Scrape ManufacturedNC - textile/apparel NAICS."""
    seen = set()
    page = 1
    per_page = 100
    while True:
        url = f"{BASE}/search?naics={naics}&page={page}"
        try:
            html = _fetch(url)
        except Exception as e:
            yield {"_error": str(e), "_url": url}
            break
        rows = _parse_search(html)
        if not rows:
            rows = _parse_search_v2(html)
        if not rows:
            break
        for r in rows:
            key = (r["name"], r.get("city", ""), r.get("state", ""))
            if key not in seen:
                seen.add(key)
                yield r
        if len(rows) < per_page:
            break
        page += 1
        time.sleep(delay)

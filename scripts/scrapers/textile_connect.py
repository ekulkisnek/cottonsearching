"""
Scrape USA manufacturers from Textile Connect directory.

https://textileconnect.com/directory/
Filter: country=usa, categories: apparel-and-product-manufacturing, textile-manufacturing
"""

import re
import time
from typing import Iterator

import requests
from bs4 import BeautifulSoup

from .base import normalize_record

BASE = "https://textileconnect.com/directory"
SOURCE = "Textile Connect"
SOURCE_URL = "https://textileconnect.com/directory/"

# Categories to scrape (USA cotton/apparel relevant)
CATEGORIES = [
    "apparel-and-product-manufacturing",  # 855
    "textile-manufacturing",              # 1494
    "textile-products",                   # 612 - towels, linens, etc.
    "raw-materials",                      # 458 - fiber, yarn
]
LETTERS = ["_", "0-9"] + [chr(i) for i in range(ord("a"), ord("z") + 1)]


def _fetch(url: str, timeout: int = 30) -> str:
    r = requests.get(url, timeout=timeout, headers={"User-Agent": "CottonSearching/1.0"})
    r.raise_for_status()
    return r.text


def _parse_listing(html: str, category: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    # Listing table: rows with company links
    for a in soup.select('a[href*="/directory/"]'):
        href = a.get("href", "")
        if "/directory/tc_category/" in href or "/directory/?l=" in href or "/directory/page/" in href:
            continue
        if href.count("/") < 4:  # skip category/letter links
            continue
        name = (a.get_text() or "").strip()
        if not name or len(name) < 2:
            continue
        # Find parent row for city/state
        row = a.find_parent("tr") or a.find_parent("div", class_=re.compile(r"listing|row|item"))
        city, state = "", ""
        if row:
            texts = row.get_text(separator="|").split("|")
            for i, t in enumerate(texts):
                t = t.strip()
                if t == "USA" and i + 2 < len(texts):
                    state = texts[i + 1].strip() if i + 1 < len(texts) else ""
                    city = texts[i + 2].strip() if i + 2 < len(texts) else ""
                    break
        if not city and not state:
            # Fallback: look for "USA", "State", "City" pattern in siblings
            parent = a.find_parent("td") or a.find_parent("div")
            if parent:
                sibs = parent.find_next_siblings()
                for s in sibs[:6]:
                    txt = (s.get_text() or "").strip()
                    if txt in ("USA", "United States"):
                        continue
                    if len(txt) == 2 and txt.upper() == txt:
                        state = txt
                        break
                    if txt and not re.match(r"^[A-Z]{2}$", txt) and len(txt) > 2:
                        city = txt
                        break
        detail_url = href if href.startswith("http") else f"https://textileconnect.com{href}" if href.startswith("/") else f"{BASE}/{href}"
        rows.append(
            normalize_record(
                name=name,
                city=city,
                state=state,
                url=detail_url,
                website=detail_url,
                buy_link=detail_url,
                type="manufacturer",
                notes=f"Textile Connect: {category}",
                source=SOURCE,
                source_url=SOURCE_URL,
            )
        )
    return rows


def _parse_listing_v2(html: str, category: str) -> list[dict]:
    """Parse listing page - extract from directory listing structure."""
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    # WPBDP directory structure: each listing has Company Name link, then Category, Excerpt, Country, State, City
    listings = soup.select(".wpbdp-listing, .listing-title, [class*='listing']")
    if not listings:
        # Fallback: find all links to /directory/SLUG/
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/directory/" not in href or "/tc_category/" in href or "?l=" in href or "/page/" in href:
                continue
            match = re.search(r"/directory/([^/?]+)/?", href)
            if not match:
                continue
            slug = match.group(1)
            if slug in ("tc_category", "page") or slug.isdigit():
                continue
            name = (a.get_text() or "").strip()
            if not name or len(name) < 2:
                continue
            # Try to get city/state from nearby text
            parent = a.find_parent("tr") or a.find_parent("div") or a.find_parent("li")
            city, state = "", ""
            if parent:
                full = parent.get_text(separator=" ").strip()
                # Pattern: ... USA State City Company Name
                usa_match = re.search(r"USA\s+([A-Za-z\s]+?)\s+([A-Za-z\s]+?)(?:\s+Company Name|$)", full)
                if usa_match:
                    state = usa_match.group(1).strip()
                    city = usa_match.group(2).strip()
                else:
                    # Simpler: look for "State" "City" after "USA"
                    parts = full.replace("Country", "").replace("State", "").replace("City", "").split()
                    for i, p in enumerate(parts):
                        if p == "USA" and i + 2 < len(parts):
                            state = parts[i + 1]
                            city = parts[i + 2]
                            break
            detail_url = href if href.startswith("http") else f"https://textileconnect.com{href}" if href.startswith("/") else f"{BASE}/{slug}/"
            rows.append(
                normalize_record(
                    name=name,
                    city=city,
                    state=state,
                    url=detail_url,
                    website=detail_url,
                    buy_link=detail_url,
                    type="manufacturer",
                    notes=f"Textile Connect: {category}",
                    source=SOURCE,
                    source_url=SOURCE_URL,
                )
            )
    return rows


def _extract_from_table(html: str, category: str) -> list[dict]:
    """Extract from wpbdp-listing grid: divs are [thumb, name+link, category, excerpt, country, state, city]."""
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    seen = set()
    for block in soup.select(".wpbdp-listing:not(.wpbdp-listing-table-header)"):
        divs = block.find_all("div", recursive=False)
        if len(divs) < 7:
            continue
        # div 1: Company Name + link; div 5: State; div 6: City
        name, url, state, city = "", "", "", ""
        a = divs[1].find("a", href=True) if len(divs) > 1 else None
        if a:
            href = a.get("href", "")
            if "tc_category" in href or "?l=" in href or "/page/" in href:
                continue
            m = re.search(r"/directory/([^/?]+)/?", href)
            if not m:
                continue
            slug = m.group(1)
            if slug in ("tc_category", "page") or slug.isdigit():
                continue
            name = (a.get_text() or "").strip()
            url = href if href.startswith("http") else f"https://textileconnect.com{href}" if href.startswith("/") else f"{BASE}/{slug}/"
        if len(divs) > 5:
            state = (divs[5].get_text() or "").replace("State", "").strip()
        if len(divs) > 6:
            city = (divs[6].get_text() or "").replace("City", "").strip()
        # div 2: Company Category; div 3: Company Excerpt (products/capabilities)
        products = ""
        if len(divs) > 2:
            cat = (divs[2].get_text() or "").replace("Company Category", "").strip()
            if len(divs) > 3:
                excerpt = (divs[3].get_text() or "").replace("Company Excerpt", "").strip()
                products = "; ".join(filter(None, [cat, excerpt]))
            else:
                products = cat
        if not name or len(name) < 2 or name in seen:
            continue
        seen.add(name)
        rows.append(
            normalize_record(
                name=name,
                city=city,
                state=state,
                url=url,
                website=url,
                buy_link=url,
                type="manufacturer",
                notes=f"Textile Connect: {category}",
                products=products,
                source=SOURCE,
                source_url=SOURCE_URL,
            )
        )
    return rows


def scrape_category(category: str, letters: list[str] | None = None, delay: float = 1.0) -> Iterator[dict]:
    """Scrape one category, iterating over letters and pages."""
    letters = letters or LETTERS
    seen = set()
    for letter in letters:
        page = 1
        while True:
            if letter == "_":
                lparam = "#"
            elif letter == "0-9":
                lparam = "0"
            else:
                lparam = letter
            url = f"{BASE}/?country=usa&tc_category={category}&l={lparam}"
            if page > 1:
                url = f"{BASE}/page/{page}/?country=usa&tc_category={category}&l={lparam}"
            try:
                html = _fetch(url)
            except Exception as e:
                yield {"_error": str(e), "_url": url}
                break
            rows = _extract_from_table(html, category)
            if not rows:
                rows = _parse_listing_v2(html, category)
            if not rows:
                break
            for r in rows:
                key = (r["name"], r.get("city", ""), r.get("state", ""))
                if key not in seen:
                    seen.add(key)
                    yield r
            if len(rows) < 50:  # Last page
                break
            page += 1
            time.sleep(delay)
        time.sleep(delay)


def scrape_all(delay: float = 1.5, letters: list[str] | None = None) -> Iterator[dict]:
    """Scrape all USA manufacturers from Textile Connect (apparel + textile)."""
    seen = set()
    for cat in CATEGORIES:
        for r in scrape_category(cat, letters=letters, delay=delay):
            if "_error" in r:
                yield r
                continue
            key = (r["name"], r.get("city", ""), r.get("state", ""))
            if key not in seen:
                seen.add(key)
                yield r

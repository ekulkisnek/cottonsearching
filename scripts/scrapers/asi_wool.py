"""
Scrape USA wool industry from American Sheep Industry Association.

https://www.sheepusa.org/contacts/wool-pelt
- Wool buyers
- Small & midsize mills
- Wool pools, warehouses, etc.
"""

import re
import time
from typing import Iterator

import requests
from bs4 import BeautifulSoup

from .base import normalize_record

BASE = "https://www.sheepusa.org/contacts/wool-pelt"
SOURCE = "ASI"
SOURCE_URL = BASE

PAGES = [
    ("wool-buyers", "wool_buyer", "Wool buyers"),
    ("small-midsize-mills", "wool_mill", "Small & midsize mills"),
]


def _fetch(url: str, timeout: int = 30) -> str:
    r = requests.get(url, timeout=timeout, headers={"User-Agent": "CottonSearching/1.0"})
    r.raise_for_status()
    return r.text


_STATE_ABBREV = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR", "california": "CA",
    "colorado": "CO", "connecticut": "CT", "delaware": "DE", "florida": "FL", "georgia": "GA",
    "hawaii": "HI", "idaho": "ID", "illinois": "IL", "indiana": "IN", "iowa": "IA",
    "kansas": "KS", "kentucky": "KY", "maine": "ME", "maryland": "MD", "massachusetts": "MA",
    "michigan": "MI", "minnesota": "MN", "mississippi": "MS", "missouri": "MO", "montana": "MT",
    "nebraska": "NE", "nevada": "NV", "new hampshire": "NH", "new jersey": "NJ",
    "new mexico": "NM", "new york": "NY", "north carolina": "NC", "north dakota": "ND",
    "ohio": "OH", "oklahoma": "OK", "oregon": "OR", "pennsylvania": "PA",
    "rhode island": "RI", "south carolina": "SC", "south dakota": "SD",
    "tennessee": "TN", "texas": "TX", "utah": "UT", "vermont": "VT",
    "virginia": "VA", "washington": "WA", "west virginia": "WV", "wisconsin": "WI", "wyoming": "WY",
}


def _parse_page(html: str, page_type: str, page_notes: str) -> list[dict]:
    """Parse ASI wool directory - h3 tags for state and company names."""
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    seen = set()
    current_state = ""

    # ASI uses h3 for state (e.g. " California") and company names
    for h3 in soup.find_all("h3"):
        text = (h3.get_text() or "").strip()
        if not text or len(text) < 2:
            continue

        # State: " California", " Colorado", " New York"
        if text.startswith(" ") or text.lower() in _STATE_ABBREV:
            state_name = text.strip()
            current_state = _STATE_ABBREV.get(state_name.lower(), state_name[:2] if len(state_name) == 2 else state_name)
            continue

        # Company name - get following sibling content for phone, email, website
        name = text
        if len(name) < 3:
            continue

        # Skip nav/section headers
        if name in ("Services & Products", "Contact ASI", "Get the latest ASI news", "Follow Us", "For finished products featuring American wool, please visit") or name.startswith("For finished products featuring American wool"):
            continue

        block = ""
        for sib in h3.find_next_siblings():
            if sib.name == "h3":
                break
            block += (sib.get_text() or "") + "\n"

        phone = ""
        ph = re.search(r"Phone:\s*([\d\-\.\s\(\)]+)", block)
        if ph:
            phone = re.sub(r"\s+", " ", ph.group(1).strip())[:30]

        em = re.search(r"\[([\w\.-]+@[\w\.-]+\.\w+)\]|([\w\.-]+@[\w\.-]+\.\w+)", block)
        email = (em.group(1) or em.group(2) or "").strip() if em else ""

        url = ""
        a = h3.find_next("a", href=lambda h: h and h.startswith("http") and "sheepusa.org" not in h)
        if a:
            url = a.get("href", "")
        if not url:
            w = re.search(r"\[(www\.[\w\.\-]+)\]\(https?://[^\)]+\)|Website:\s*\[?([\w\.\-]+\.(?:com|org|net|biz)[^\s\]\[]*)\]?", block)
            if w:
                url = (w.group(1) or w.group(2) or "").strip()
                if url and not url.startswith("http"):
                    url = "https://" + url

        loc = re.search(r"([A-Za-z\s\.\-]+),?\s*([A-Z]{2})\s+\d{5}", block)
        city = loc.group(1).strip()[:50] if loc else ""
        state = loc.group(2).strip() if loc else (_STATE_ABBREV.get((current_state or "").lower(), (current_state or "")[:2]) if current_state else "")

        products = []
        for term in ["Scouring", "Carding", "Spinning", "Yarn", "Roving", "Batting", "Felting", "Dyeing", "Weaving", "Combing"]:
            if term in block or term.lower() in block:
                products.append(term)
        products_str = "; ".join(products[:8]) if products else page_notes

        key = (name.lower()[:50], (city or "").lower(), (state or "").upper())
        if key in seen:
            continue
        seen.add(key)

        rows.append(
            normalize_record(
                name=name[:80],
                city=city,
                state=state,
                url=url,
                website=url,
                buy_link=url,
                phone=phone,
                email=email,
                type=page_type,
                notes=f"ASI: {page_notes}",
                products=products_str,
                source=SOURCE,
                source_url=SOURCE_URL,
            )
        )
    return rows


def scrape_page(slug: str, page_type: str, page_notes: str, delay: float = 1.0) -> Iterator[dict]:
    """Scrape one ASI wool directory page."""
    url = f"{BASE}/{slug}"
    html = _fetch(url)
    for r in _parse_page(html, page_type, page_notes):
        yield r
    time.sleep(delay)


def scrape(delay: float = 1.0) -> Iterator[dict]:
    """Scrape all ASI wool directory pages."""
    for slug, page_type, page_notes in PAGES:
        yield from scrape_page(slug, page_type, page_notes, delay)

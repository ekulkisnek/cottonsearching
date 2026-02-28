"""
Scrape USA fiber mills from Wool and Fiber Arts US Mill Directory.

https://woolandfiberarts.com/pages/us-mill-directory
State-by-state listing of fiber mills (wool, alpaca, etc.)
"""

import re
import time
from typing import Iterator

import requests
from bs4 import BeautifulSoup

from .base import normalize_record

URL = "https://woolandfiberarts.com/pages/us-mill-directory"
SOURCE = "Wool and Fiber Arts"
SOURCE_URL = URL

def _parse_table(soup) -> list[dict]:
    """Parse HTML table - cell 1 has state (no link) or mill name (with link)."""
    rows = []
    seen = set()
    current_state = ""
    for tr in soup.select("table tr"):
        cells = tr.find_all(["td", "th"])
        if len(cells) < 2:
            continue
        cell1 = cells[1]
        txt = (cell1.get_text() or "").strip()
        a = cell1.find("a", href=lambda h: h and "woolandfiberarts" not in (h or ""))
        if a and (a.get("href") or "").startswith("http"):
            name = (a.get_text() or "").strip()
            if not name or len(name) < 2:
                continue
            url = a.get("href", "")
            services = (cells[2].get_text() if len(cells) > 2 else "") or ""
            fibers = (cells[3].get_text() if len(cells) > 3 else "") or ""
            products = []
            for term in ["Wool", "Yarn", "Roving", "Carding", "Spinning", "Felting", "Dyeing"]:
                if term in (services + fibers):
                    products.append(term)
            products_str = "; ".join(products[:8]) if products else "Fiber processing"
            key = (name.lower(), current_state)
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                normalize_record(
                    name=name[:80], city="", state=current_state, url=url, website=url, buy_link=url,
                    type="wool_mill", notes=f"Wool and Fiber Arts: {current_state or 'USA'}",
                    products=products_str, source=SOURCE, source_url=SOURCE_URL,
                )
            )
        elif txt and txt.lower() in _STATE_ABBREV:
            current_state = _STATE_ABBREV[txt.lower()]
    return rows


_STATE_ABBREV = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR", "california": "CA",
    "colorado": "CO", "conneticut": "CT", "connecticut": "CT", "delaware": "DE", "florida": "FL",
    "georgia": "GA", "hawaii": "HI", "idaho": "ID", "illinois": "IL", "indiana": "IN", "iowa": "IA",
    "kansas": "KS", "kentucky": "KY", "maine": "ME", "maryland": "MD", "massachusettes": "MA",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
    "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV", "new hampshire": "NH",
    "new jersey": "NJ", "new mexico": "NM", "new york": "NY", "north carolina": "NC",
    "north dakota": "ND", "ohio": "OH", "oklahoma": "OK", "oregon": "OR", "pennsylvania": "PA",
    "rhode island": "RI", "south carolina": "SC", "south dakota": "SD", "tennessee": "TN",
    "texas": "TX", "utah": "UT", "vermont": "VT", "virginia": "VA", "washington": "WA",
    "west virginia": "WV", "wisconsin": "WI", "wyoming": "WY",
}


def _fetch(timeout: int = 30) -> str:
    r = requests.get(URL, timeout=timeout, headers={"User-Agent": "CottonSearching/1.0"})
    r.raise_for_status()
    return r.text


def _parse(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    # Try table first (Shopify may render as table)
    table_rows = _parse_table(soup)
    if table_rows:
        return table_rows
    # Fallback: parse text for markdown-style [Name](url)
    text = soup.get_text(separator="\n")
    rows = []
    seen = set()
    current_state = ""

    # Parse lines - state names then [Mill Name](url) | services | fibers
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue

        # State row - "Alabama", "California", etc. (may have | after)
        parts = line.split("|")
        first = (parts[0].strip() if parts else "").strip()
        first_lower = first.lower()

        if first_lower in _STATE_ABBREV:
            current_state = _STATE_ABBREV[first_lower]
            continue
        if first in ("Alabama", "Alaska", "California", "Colorado", "Connecticut", "Georgia",
                     "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Maine",
                     "Massachusetts", "Michigan", "Minnesota", "Missouri", "Montana", "Nebraska",
                     "New Hampshire", "New York", "North Carolina", "North Dakota", "Ohio",
                     "Oklahoma", "Oregon", "Pennsylvania", "South Carolina", "South Dakota",
                     "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
                     "West Virginia", "Wisconsin") or first == "Conneticut" or first == "Massachusettes":
            current_state = _STATE_ABBREV.get(first_lower, first[:2])
            continue

        # Mill row - [Name](url) or * | [Name](url)
        m = re.search(r"\*?\s*\[([^\]]+)\]\((https?://[^\)]+)\)", first or line)
        if not m:
            continue

        name = m.group(1).strip()
        url = m.group(2).strip()
        if not name or len(name) < 2:
            continue

        # Get services and fibers from rest of line
        rest = "|".join(parts[1:]) if len(parts) > 1 else ""
        services = rest
        fibers = rest

        products = []
        if "Wool" in fibers or "wool" in rest:
            products.append("Wool")
        if "Yarn" in services or "yarn" in rest or "Process - Yarn" in rest:
            products.append("Yarn")
        if "Roving" in services or "roving" in rest or "Process - Roving" in rest:
            products.append("Roving")
        if "Carding" in services or "carding" in rest:
            products.append("Carding")
        if "Spinning" in services or "spinning" in rest:
            products.append("Spinning")
        if "Felting" in services or "felting" in rest or "Process - Felt" in rest:
            products.append("Felting")
        if "Dyeing" in services or "dyeing" in rest:
            products.append("Dyeing")
        products_str = "; ".join(products[:8]) if products else "Fiber processing"

        key = (name.lower(), current_state)
        if key in seen:
            continue
        seen.add(key)

        rows.append(
            normalize_record(
                name=name[:80],
                city="",
                state=current_state,
                url=url,
                website=url,
                buy_link=url,
                type="wool_mill",
                notes=f"Wool and Fiber Arts: {current_state or 'USA'}",
                products=products_str,
                source=SOURCE,
                source_url=SOURCE_URL,
            )
        )
    return rows


def scrape(delay: float = 1.0) -> Iterator[dict]:
    """Scrape Wool and Fiber Arts US Mill Directory."""
    html = _fetch()
    for r in _parse(html):
        yield r
    time.sleep(delay)

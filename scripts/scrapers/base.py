"""
Base utilities for manufacturer scrapers.
"""

import re
from typing import Any


def normalize_record(
    name: str,
    city: str = "",
    state: str = "",
    *,
    url: str = "",
    website: str = "",
    buy_link: str = "",
    phone: str = "",
    email: str = "",
    type: str = "manufacturer",
    notes: str = "",
    products: str = "",
    production: str = "",
    source: str = "",
    source_url: str = "",
    prices: str = "Contact for quote",
    **extra: Any,
) -> dict:
    """Build a normalized buyable-style record."""
    state = _abbrev_state(state)
    return {
        "name": (name or "").strip(),
        "city": (city or "").strip(),
        "state": state,
        "url": url or website or "",
        "website": website or url or "",
        "buy_link": buy_link or website or url or "",
        "phone": (phone or "").strip(),
        "email": (email or "").strip(),
        "type": type,
        "notes": (notes or "").strip(),
        "products": (products or "").strip(),
        "production": (production or "").strip(),
        "source": source,
        "source_url": source_url,
        "prices": prices,
        **{k: v for k, v in extra.items() if k not in ("name", "city", "state", "url", "website", "buy_link", "phone", "email", "type", "notes", "products", "production", "source", "source_url", "prices")},
    }


_US_STATE_ABBREV = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT",
    "delaware": "DE", "district of columbia": "DC",
    "florida": "FL", "georgia": "GA", "hawaii": "HI",
    "idaho": "ID", "illinois": "IL", "indiana": "IN", "iowa": "IA",
    "kansas": "KS", "kentucky": "KY", "louisiana": "LA",
    "maine": "ME", "maryland": "MD", "massachusetts": "MA", "michigan": "MI",
    "minnesota": "MN", "mississippi": "MS", "missouri": "MO", "montana": "MT",
    "nebraska": "NE", "nevada": "NV", "new hampshire": "NH", "new jersey": "NJ",
    "new mexico": "NM", "new york": "NY", "north carolina": "NC", "north dakota": "ND",
    "ohio": "OH", "oklahoma": "OK", "oregon": "OR", "pennsylvania": "PA",
    "rhode island": "RI", "south carolina": "SC", "south dakota": "SD",
    "tennessee": "TN", "texas": "TX", "utah": "UT", "vermont": "VT",
    "virginia": "VA", "washington": "WA", "west virginia": "WV",
    "wisconsin": "WI", "wyoming": "WY",
}


def _abbrev_state(s: str) -> str:
    if not s:
        return ""
    s = s.strip()
    if len(s) == 2 and s.upper() == s:
        return s.upper()
    return _US_STATE_ABBREV.get(s.lower(), s)


def slugify(name: str) -> str:
    """Convert company name to URL slug (e.g. for CFDA)."""
    s = re.sub(r"[^\w\s-]", "", name.lower())
    s = re.sub(r"[-\s]+", "-", s).strip("-")
    return s or ""

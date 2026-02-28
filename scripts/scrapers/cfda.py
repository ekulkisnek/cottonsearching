"""
Scrape USA fashion manufacturers from CFDA Production Directory.

https://cfda.com/resources/supply-chain-manufacturing/production-directory/
~380+ U.S. manufacturers. Each has detail page with contact info.
"""

import re
import time
from typing import Iterator

import requests
from bs4 import BeautifulSoup

from .base import normalize_record

BASE = "https://cfda.com/resources/supply-chain-manufacturing/production-directory"
SOURCE = "CFDA"
SOURCE_URL = f"{BASE}/"


def _fetch(url: str, timeout: int = 30) -> str:
    r = requests.get(url, timeout=timeout, headers={"User-Agent": "CottonSearching/1.0"})
    r.raise_for_status()
    return r.text


def _extract_names_from_index(html: str) -> list[str]:
    """Extract manufacturer names from main directory page (buttons with data-post-id)."""
    soup = BeautifulSoup(html, "html.parser")
    names = []
    for btn in soup.find_all(attrs={"data-post-id": True}):
        name = (btn.get_text() or "").strip()
        if name and len(name) > 2:
            names.append(name)
    return list(dict.fromkeys(names))  # dedupe


def _name_to_slug(name: str) -> str:
    """Convert company name to CFDA URL slug."""
    s = name.lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "-", s).strip("-")
    return s


def _parse_detail(html: str, name: str) -> dict | None:
    """Parse detail page for contact info."""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator=" ")
    city, state, phone, email = "", "", "", ""
    # Address: "265 West 37th St. 4th Fl. New York , NY , 10018"
    addr = re.search(r"([A-Za-z\s]+),\s*([A-Z]{2})\s*,?\s*\d{5}", text)
    if addr:
        city = addr.group(1).strip()
        state = addr.group(2).strip()
    # Phone: "Phone: 212-465-1093"
    ph = re.search(r"Phone:\s*([\d\-\.\(\)\s]+)", text)
    if ph:
        phone = ph.group(1).strip()
    # Email
    em = re.search(r"[\w.-]+@[\w.-]+\.\w+", text)
    if em:
        email = em.group(0)
    # Parse Products, Services, Categories from detail page
    products = []
    for section in ("Products", "Services", "Categories"):
        # Look for section headers and following content
        idx = text.find(section + ":")
        if idx >= 0:
            chunk = text[idx : idx + 500]
            # Extract list items (Knits, Sportswear, etc.)
            for line in chunk.split("\n"):
                line = line.strip()
                if line and len(line) < 50 and line[0].isupper() and ":" not in line[:20]:
                    products.append(line)
    products_str = "; ".join(products[:15]) if products else "Fashion manufacturing"
    return normalize_record(
        name=name,
        city=city,
        state=state,
        phone=phone,
        email=email,
        type="cut_and_sew",
        notes="CFDA Production Directory",
        products=products_str,
        source=SOURCE,
        source_url=SOURCE_URL,
    )


def scrape(detail_pages: bool = True, delay: float = 1.0) -> Iterator[dict]:
    """Scrape CFDA Production Directory."""
    html = _fetch(BASE + "/")
    names = _extract_names_from_index(html)
    if not names:
        # Fallback: find all directory links
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            m = re.search(r"/production-directory/([^/]+)/?$", a["href"])
            if m:
                slug = m.group(1)
                if slug in ("production-directory", "materials-hub", "sustainability", "fashion-manufacturing"):
                    continue
                name = (a.get_text() or "").strip()
                if name and len(name) > 2:
                    names.append(name)
        names = list(dict.fromkeys(names))
    seen = set()
    for name in names:
        slug = _name_to_slug(name)
        if not slug or slug in seen:
            continue
        seen.add(slug)
        detail_url = f"{BASE}/{slug}/"
        if detail_pages:
            try:
                detail_html = _fetch(detail_url)
                rec = _parse_detail(detail_html, name)
                if rec:
                    rec["url"] = detail_url
                    rec["website"] = detail_url
                    rec["buy_link"] = detail_url
                    yield rec
            except Exception:
                yield normalize_record(
                    name=name,
                    type="cut_and_sew",
                    notes="CFDA Production Directory",
                    products="Fashion manufacturing",
                    source=SOURCE,
                    source_url=SOURCE_URL,
                    url=detail_url,
                    website=detail_url,
                    buy_link=detail_url,
                )
            time.sleep(delay)
        else:
            yield normalize_record(
                name=name,
                type="cut_and_sew",
                notes="CFDA Production Directory",
                products="Fashion manufacturing",
                source=SOURCE,
                source_url=SOURCE_URL,
                url=detail_url,
                website=detail_url,
                buy_link=detail_url,
            )

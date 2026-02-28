"""
Scrape cut & sew manufacturers from Cotton Incorporated.

https://www.cottoninc.com/quality-products/textile-sourcing/cut-and-sew/
"""

import re
from typing import Iterator

import requests
from bs4 import BeautifulSoup

from .base import normalize_record

URL = "https://www.cottoninc.com/quality-products/textile-sourcing/cut-and-sew/"
SOURCE = "Cotton Incorporated"
SOURCE_URL = URL


def _fetch(timeout: int = 45) -> str:
    r = requests.get(URL, timeout=timeout, headers={"User-Agent": "CottonSearching/1.0"})
    r.raise_for_status()
    return r.text


def _parse(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    seen = set()
    # Each company is in div.item or div with textile_sourcing; contains external link
    for block in soup.select(".item.textile_sourcing, .sourcing-lists .item"):
        a = block.find("a", href=lambda h: h and h.startswith("http") and "cottoninc.com" not in h)
        if not a:
            continue
        href = a["href"]
        txt = block.get_text(separator=" ")
        name = (a.get_text() or "").strip() or (block.find(string=re.compile(r"^[A-Za-z].*")) or "")
        if isinstance(name, str):
            name = name.strip().split("\n")[0].strip()
        else:
            name = (name or "").strip() if name else ""
        # Name is usually first line of block before city
        txt = block.get_text()
        cotton_types = ("Apparel", "CMT", "Denim", "Home", "Knits", "Uniforms", "Wovens")
        products = [t for t in cotton_types if t in txt]
        lines = [l.strip() for l in txt.split("\n") if l.strip()]
        for line in lines:
            if line.startswith("http") or "Phone:" in line:
                continue
            if re.match(r"^[A-Za-z][A-Za-z\s\.&',\-]+$", line) and len(line) > 2:
                name = line
                break
        products_str = ", ".join(products) if products else "Cut & sew"
        loc = re.search(r"([A-Za-z\s]+),\s*([A-Z]{2})\b", txt)
        city, state = (loc.group(1).strip(), loc.group(2).strip()) if loc else ("", "")
        ph = re.search(r"Phone:\s*\(?([\d\-\.\s]+)\)?", txt)
        phone = ph.group(1).strip() if ph else ""
        if not name:
            continue
        key = (name, city, state)
        if key not in seen:
            seen.add(key)
            rows.append(
                normalize_record(
                    name=name,
                    city=city,
                    state=state,
                    url=href,
                    website=href,
                    buy_link=href,
                    phone=phone,
                    type="cut_and_sew",
                    notes="Cotton Inc cut & sew",
                    products=products_str,
                    source=SOURCE,
                    source_url=SOURCE_URL,
                )
            )
    return rows


def scrape() -> Iterator[dict]:
    """Scrape Cotton Incorporated cut & sew directory."""
    html = _fetch()
    for r in _parse(html):
        yield r

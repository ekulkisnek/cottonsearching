"""
Parse CottonWorks U.S. Supplier List PDF.

https://cottonworks.com/sourcing/find-us-suppliers/
PDF: cottonworks.com/wp-content/uploads/.../US-Supplier-List*.pdf
"""

import re
from pathlib import Path
from typing import Iterator

from .base import normalize_record

SOURCE = "CottonWorks"
SOURCE_URL = "https://cottonworks.com/sourcing/find-us-suppliers/"

# PDF URLs (try latest first)
PDF_URLS = [
    "https://cottonworks.com/wp-content/uploads/2026/01/US-Supplier-List-high-rez-2.pdf",
    "https://cottonworks.com/wp-content/uploads/2025/10/US-Supplier-List.pdf",
]


def _download_pdf(url: str, cache_path: Path | None = None) -> bytes | None:
    """Download PDF; optionally cache to file."""
    try:
        import requests

        r = requests.get(url, timeout=60, headers={"User-Agent": "CottonSearching/1.0"})
        r.raise_for_status()
        data = r.content
        if cache_path:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_bytes(data)
        return data
    except Exception:
        return None


def _extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF using pypdf."""
    from pypdf import PdfReader
    from io import BytesIO

    reader = PdfReader(BytesIO(pdf_bytes))
    return "\n".join(p.extract_text() or "" for p in reader.pages)


def _parse_pdf_text(text: str) -> list[dict]:
    """
    Parse CottonWorks PDF. Format:
    Line 1: Company Name   Phone: (xxx) xxx-xxxx Capabilities:
    Line 2: City, ST Website: domain.com [capabilities]
    """
    rows = []
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    i = 0
    while i < len(lines):
        line = lines[i]
        # Skip section headers
        if re.match(r"^(CUT & SEW|SPINNERS|WEAVERS|KNITTERS|FINISHERS|DYEHOUSES|PRINTERS|U\.S\. SUPPLIERS|\d+)$", line, re.I):
            i += 1
            continue
        # Match "City, ST" - often at start of line or after Capabilities:
        loc = re.search(r"([A-Za-z\s\.\-]+),\s*([A-Z]{2})\b", line)
        if loc:
            city, state = loc.group(1).strip(), loc.group(2).strip()
            # Name + phone on previous line: "Company Name   Phone: (xxx) xxx-xxxx Capabilities:"
            prev = lines[i - 1].strip() if i > 0 else ""
            name = ""
            phone = ""
            website = ""
            if prev:
                ph = re.search(r"Phone:\s*([\d\-\.\s\(\)]+?)(?:\s+Capabilities|$)", prev)
                if ph:
                    phone = ph.group(1).strip()
                # Name is everything before "Phone:"
                name_match = re.match(r"^(.+?)\s+Phone:", prev)
                if name_match:
                    name = name_match.group(1).strip()
                else:
                    name = re.sub(r"\s+Phone:.*", "", prev).strip()
            # Website from current line
            web = re.search(r"Website:\s*([a-zA-Z0-9\-\.]+)", line)
            if web:
                website = "https://" + web.group(1) if not web.group(1).startswith("http") else web.group(1)
            # Capabilities: after Website or at end of line (Apparel, Denim, CMT, Dyehouse, etc.)
            products = ""
            cap_match = re.search(r"(?:Website:\s*[a-zA-Z0-9\-\.]+\s+)?(.+)$", line)
            if cap_match:
                cap_text = cap_match.group(1).strip()
                if cap_text and not re.match(r"^https?://", cap_text):
                    products = cap_text
            # Also check next line for more capabilities
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and not re.search(r"^[A-Za-z\s]+,?\s*[A-Z]{2}\b", next_line) and "Website:" not in next_line:
                    if products:
                        products = products + "; " + next_line[:200]
                    else:
                        products = next_line[:200]
            if not name:
                name = line.split(",")[0].strip()
            if name and len(name) > 2 and city and state:
                rows.append(
                    normalize_record(
                        name=name,
                        city=city,
                        state=state,
                        phone=phone,
                        url=website,
                        website=website,
                        buy_link=website or SOURCE_URL,
                        type="us_supplier",
                        notes="CottonWorks U.S. Supplier List",
                        products=products,
                        source=SOURCE,
                        source_url=SOURCE_URL,
                    )
                )
        i += 1
    return rows


def scrape(pdf_path: Path | None = None, cache_dir: Path | None = None) -> Iterator[dict]:
    """
    Scrape CottonWorks U.S. Supplier List.
    If pdf_path given, use that file. Else download from URL and optionally cache.
    """
    pdf_bytes = None
    if pdf_path and pdf_path.exists():
        pdf_bytes = pdf_path.read_bytes()
    else:
        root = Path(__file__).resolve().parent.parent.parent
        cache_dir = cache_dir or (root / "data" / "cache")
        cache = cache_dir / "cottonworks_us_supplier.pdf"
        if cache.exists():
            pdf_bytes = cache.read_bytes()
        else:
            for url in PDF_URLS:
                pdf_bytes = _download_pdf(url, cache)
                if pdf_bytes:
                    break
    if not pdf_bytes:
        yield {"_error": "Could not load CottonWorks PDF", "_urls": PDF_URLS}
        return
    text = _extract_text_from_pdf(pdf_bytes)
    seen = set()
    for r in _parse_pdf_text(text):
        if "_error" in r:
            yield r
            continue
        key = (r["name"], r.get("city", ""), r.get("state", ""))
        if key not in seen:
            seen.add(key)
            yield r

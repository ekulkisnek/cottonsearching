#!/usr/bin/env python3
"""
Enrich wool records with products and production by checking each website.

Extracts product/capability info from wool company sites when products field is empty.
Looks for: scouring, carding, spinning, yarn, roving, capacity, lbs/yr, etc.

Usage:
  python scripts/enrich_products_wool.py [--input data/wool_merged.csv] [--output data/wool_with_products.csv]
  python scripts/enrich_products_wool.py --limit 30 --delay 1.0
"""

import argparse
import csv
import re
import sys
import time
import urllib3
from pathlib import Path

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests

from src.sources.wool import _enrich_record
from bs4 import BeautifulSoup

# Skip directory hubs - we don't fetch these for product extraction
SKIP_DOMAINS = (
    "sheepusa.org", "americanwool.org", "nationalmillinventory.com",
    "woolandfiberarts.com", "fibershed.com",
)


def _get_url(r: dict) -> str | None:
    """Return first valid URL for fetching."""
    for k in ("website", "buy_link", "url"):
        u = (r.get(k) or "").strip()
        if u and u.startswith("http") and not any(d in u for d in SKIP_DOMAINS):
            return u
    return None


def _fetch(url: str, timeout: int = 12) -> str | None:
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "CottonSearching/1.0"}, verify=False)
        r.raise_for_status()
        return r.text
    except Exception:
        return None


def _extract_products_wool(html: str) -> str:
    """Extract wool product/capability keywords from page."""
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True).lower()

    # Wool-specific keywords
    keywords = [
        "wool", "fleece", "scouring", "carding", "spinning", "roving", "batting",
        "felting", "dyeing", "combing", "weaving", "worsted", "woolen",
        "yarn", "alpaca", "mohair", "merino", "raw wool", "scoured wool",
        "blankets", "socks", "hats", "apparel", "fabric", "textile",
        "responsible wool", "rws", "organic wool", "american wool",
        "fiber processing", "custom processing", "commission", "toll",
        "small batch", "farm to fiber", "traceable", "sustainable",
    ]
    found = []
    for kw in keywords:
        if kw in text and kw not in found:
            found.append(kw)

    # "We offer", "We process", "Services:", "Capabilities:"
    for pattern in [
        r"(?:we\s+(?:offer|process|provide|specialize\s+in)\s+(?:in\s+)?)([^.]{8,120})",
        r"(?:services?:\s*|capabilities?:\s*|we\s+process\s+)([^.]{8,120})",
        r"(?:specializing\s+in\s+)([^.]{8,100})",
        r"(?:our\s+(?:services?|products?)\s+include[:\s]+)([^.]{8,120})",
        r"(?:process(?:ing)?\s+)([^.]{8,100})",
        r"(?:since\s+)(\d{4})",
    ]:
        m = re.search(pattern, text, re.I)
        if m:
            snippet = re.sub(r"\s+", " ", m.group(1).strip())[:100]
            if len(snippet) > 8 and snippet not in str(found).lower():
                found.append(snippet)

    seen = set()
    out = []
    for f in found:
        f = str(f).strip().title()
        if f and f not in seen and len(f) > 2:
            seen.add(f)
            out.append(f)
    return "; ".join(out[:20]) if out else ""


def _extract_production_wool(html: str) -> str:
    """Extract production/volume from wool company page."""
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    found = []
    # lbs/yr, fleece/yr, million lbs
    m = re.search(r"[\d\s,\.\-+KkMm]+(?:\s*(?:lbs?|fleece|pounds?|tons?)\s*(?:/|per)\s*(?:yr|year)|million\s*(?:lbs?|pounds?))", text, re.I)
    if m:
        found.append(m.group(0).strip()[:50])
    # capacity, production volume
    m = re.search(r"(?:capacity|production\s+volume|annual\s+production)\s*[:\s]*([\d\s,\.\-KkMm]+(?:\s*(?:lbs?|yards?|tons?|million))?)", text, re.I)
    if m:
        found.append("Capacity: " + m.group(1).strip()[:40])
    # MOQ
    m = re.search(r"(?:moq|minimum\s+order)\s*[:\s]*([\d\s,\.\-KkMm]+(?:\s*(?:lbs?|yards?|units?))?)", text, re.I)
    if m:
        found.append("MOQ: " + m.group(1).strip()[:30])
    # employees
    m = re.search(r"(\d[\d,]+)\s*(?:employees?|people|staff)", text, re.I)
    if m:
        found.append(m.group(1).strip() + " employees")
    # since YYYY
    m = re.search(r"since\s+(\d{4})", text, re.I)
    if m:
        found.append("Est. " + m.group(1))
    return "; ".join(found[:3]) if found else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", "-i", default="data/wool_merged.csv")
    ap.add_argument("--output", "-o", default="data/wool_with_products.csv")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--delay", type=float, default=1.0)
    ap.add_argument("--skip-filled", action="store_true", help="Skip records that already have products")
    args = ap.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"Input not found: {in_path}", file=sys.stderr)
        return 1

    rows = list(csv.DictReader(open(in_path, encoding="utf-8")))
    fieldnames = list(rows[0].keys()) if rows else []
    if "products" not in fieldnames:
        fieldnames.insert(fieldnames.index("notes") + 1, "products")
    if "production" not in fieldnames:
        fieldnames.insert(fieldnames.index("products") + 1, "production")

    rows = [_enrich_record(r) for r in rows]

    to_check = []
    for r in rows:
        url = _get_url(r)
        if not url:
            continue
        if args.skip_filled and (r.get("products") or "").strip():
            continue
        to_check.append(r)

    if args.limit:
        to_check = to_check[: args.limit]

    print(f"Enriching wool products for {len(to_check)} records...", file=sys.stderr)
    updated = 0
    for r in to_check:
        url = _get_url(r)
        if not url:
            continue
        html = _fetch(url)
        if not html:
            continue
        products = _extract_products_wool(html)
        production = _extract_production_wool(html)
        existing = (r.get("products") or "").strip()
        existing_prod = (r.get("production") or "").strip()
        if products and not existing:
            r["products"] = products
            updated += 1
            print(f"  {r.get('name','')[:40]}: {products[:60]}...", file=sys.stderr)
        elif products and len(products) > len(existing):
            r["products"] = products
            updated += 1
            print(f"  {r.get('name','')[:40]}: {products[:60]}...", file=sys.stderr)
        if production and not existing_prod:
            r["production"] = production
            print(f"  {r.get('name','')[:40]}: production {production[:50]}", file=sys.stderr)
        time.sleep(args.delay)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    print(f"Updated {updated} records; wrote {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

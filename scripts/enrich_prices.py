#!/usr/bin/env python3
"""
Enrich buyable sources with price info by checking each website.

Fetches website/buy_link for each record, parses for price-related content:
- MOQ (minimum order quantity)
- Dollar amounts ($X, $X.XX)
- Wholesale, contact for quote, get quote
- Minimum order, pricing page links

Usage:
  python scripts/enrich_prices.py [--input data/buyable_merged.csv] [--output data/buyable_with_prices.csv]
  python scripts/enrich_prices.py --limit 50   # Test with first 50
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
from bs4 import BeautifulSoup

# Skip these URLs (directory pages, not company sites)
SKIP_DOMAINS = (
    "textileconnect.com",
    "cottoninc.com",
    "cfda.com",
    "manufacturednc.com",
    "ncto.org",
    "cottonworks.com",
)


def _get_fetch_url(r: dict) -> str | None:
    """Get best URL to fetch - prefer company website over directory link."""
    for key in ("website", "buy_link", "url"):
        u = (r.get(key) or "").strip()
        if not u or not u.startswith("http"):
            continue
        if any(d in u for d in SKIP_DOMAINS):
            continue
        return u
    return None


def _fetch_page(url: str, timeout: int = 12) -> str | None:
    """Fetch page HTML."""
    try:
        r = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": "CottonSearching/1.0 (price research)"},
            allow_redirects=True,
            verify=False,  # Some manufacturer sites have expired SSL
        )
        r.raise_for_status()
        return r.text
    except Exception:
        return None


def _extract_price_info(html: str) -> list[str]:
    """Extract price-related snippets from HTML."""
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True).lower()
    findings = []

    # MOQ patterns: "MOQ 50", "minimum 25", "min order 100"
    moq = re.findall(
        r"(?:moq|minimum\s*order|min\.?\s*order|minimum)\s*(?:of\s*)?(?:quantity\s*)?[:\s]*(\d+[\d,]*)\s*(?:units?|pieces?|pcs?|garments?)?",
        text,
        re.I,
    )
    if moq:
        findings.append(f"MOQ {moq[0]}")

    # "starting at $X", "from $X", "as low as $X"
    start_price = re.search(r"(?:starting\s*at|from|as\s*low\s*as)\s*(\$[\d,]+(?:\.\d{2})?)", text, re.I)
    if start_price:
        findings.append(f"From {start_price.group(1)}")

    # Dollar amounts (skip if tiny like $0 or $1 - likely not product price)
    dollars = re.findall(r"\$[\d,]+(?:\.\d{2})?", text)
    if dollars:
        seen = set()
        for d in dollars[:5]:
            if d not in seen:
                # Skip tiny amounts
                num = re.sub(r"[\$,]", "", d)
                if num.replace(".", "").isdigit() and float(num) >= 2:
                    seen.add(d)
                    findings.append(d)

    # Keywords (only add if we don't have concrete info yet)
    if not findings or "wholesale" in text:
        if "no minimum" in text or "no minimums" in text:
            findings.append("No minimum")
        elif "wholesale" in text:
            findings.append("Wholesale")
    if "apply for account" in text or "wholesale account" in text:
        findings.append("Apply for wholesale account")
    if "see website" in text or "prices on website" in text:
        findings.append("See website")
    # "Contact for quote" only if we have nothing else
    if not findings and ("contact for quote" in text or "request a quote" in text or "get a quote" in text):
        findings.append("Contact for quote")

    out = []
    for f in findings:
        f = str(f).strip()
        if f and f not in out:
            out.append(f)
    return out[:5]


def main():
    ap = argparse.ArgumentParser(description="Enrich buyable sources with price info from websites")
    ap.add_argument("--input", "-i", default="data/buyable_merged.csv", help="Input CSV")
    ap.add_argument("--output", "-o", default="data/buyable_with_prices.csv", help="Output CSV")
    ap.add_argument("--limit", "-n", type=int, default=None, help="Limit to first N fetchable records (for testing)")
    ap.add_argument("--offset", type=int, default=0, help="Skip first N fetchable records")
    ap.add_argument("--delay", type=float, default=1.0, help="Seconds between requests")
    ap.add_argument("--skip-existing", action="store_true", help="Skip records that already have non-default prices")
    ap.add_argument("--batch", type=int, default=None, help="Process in batches of N; save after each batch (for resumable runs)")
    args = ap.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"Input not found: {in_path}", file=sys.stderr)
        return 1

    rows = []
    with open(in_path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # Filter to records with fetchable URLs
    to_check = []
    for r in rows:
        url = _get_fetch_url(r)
        if not url:
            continue
        if args.skip_existing:
            p = (r.get("prices") or "").strip()
            if p and p != "Contact for quote":
                continue
        to_check.append(r)

    to_check = to_check[args.offset : (args.offset + args.limit) if args.limit else None]
    print(f"Checking {len(to_check)} of {len(rows)} records (offset={args.offset})...", file=sys.stderr)
    fieldnames = list(rows[0].keys()) if rows else []

    updated = 0
    out_path = Path(args.output)
    batch_size = args.batch or len(to_check)

    for batch_start in range(0, len(to_check), batch_size):
        batch = to_check[batch_start : batch_start + batch_size]
        for i, r in enumerate(batch):
            url = _get_fetch_url(r)
            if not url:
                continue

            html = _fetch_page(url)
            findings = _extract_price_info(html) if html else []
            if findings:
                new_prices = "; ".join(findings)
                existing = (r.get("prices") or "").strip()
                if existing and existing != "Contact for quote":
                    pass
                elif new_prices and new_prices != existing:
                    r["prices"] = new_prices
                    updated += 1
                    idx = batch_start + i + 1
                    print(f"  [{idx}] {r.get('name','')[:45]}: {new_prices[:70]}", file=sys.stderr)

            time.sleep(args.delay)

        # Save after each batch
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
        if batch_size < len(to_check):
            print(f"  Saved batch {batch_start//batch_size + 1} ({len(rows)} rows)", file=sys.stderr)
    print(f"Updated {updated} records; wrote {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

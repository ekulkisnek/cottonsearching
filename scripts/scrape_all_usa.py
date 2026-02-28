#!/usr/bin/env python3
"""
Scrape all USA cotton and apparel manufacturers from directories.

Sources:
- Textile Connect (apparel + textile manufacturing, USA only)
- Cotton Incorporated (cut & sew)
- CFDA Production Directory (~380 manufacturers)
- ManufacturedNC (NC textile/apparel NAICS 313, 314, 315)
- NCTO members

Output: data/scraped_usa.csv (deduplicated, normalized)

Usage:
  python scripts/scrape_all_usa.py [--sources textile,cfda,cotton,mnc,ncto] [--output data/scraped_usa.csv]
"""

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.scrapers.textile_connect import scrape_all as scrape_textile
from scripts.scrapers.cotton_inc import scrape as scrape_cotton
from scripts.scrapers.cfda import scrape as scrape_cfda
from scripts.scrapers.manufactured_nc import scrape as scrape_mnc
from scripts.scrapers.ncto import scrape as scrape_ncto
from scripts.scrapers.cottonworks_pdf import scrape as scrape_cottonworks


SOURCES = {
    "textile": ("Textile Connect", scrape_textile, {}),
    "cotton": ("Cotton Incorporated", scrape_cotton, {}),
    "cfda": ("CFDA", scrape_cfda, {"detail_pages": True, "delay": 1.5}),
    "mnc": ("ManufacturedNC", scrape_mnc, {"naics": "313,314,315", "delay": 1.0}),
    "ncto": ("NCTO", scrape_ncto, {"delay": 1.0}),
    "cottonworks": ("CottonWorks PDF", scrape_cottonworks, {}),
}


def _dedupe_key(r: dict) -> tuple:
    """Key for deduplication: normalize name, city, state."""
    name = (r.get("name") or "").strip().lower()
    city = (r.get("city") or "").strip().lower()
    state = (r.get("state") or "").strip().upper()
    return (name, city, state)


def _merge_records(records: list[dict]) -> dict:
    """Merge multiple records for same entity - prefer non-empty fields."""
    out = {}
    for r in records:
        for k, v in r.items():
            if k.startswith("_"):
                continue
            if v and (k not in out or not out.get(k)):
                out[k] = v
    return out


def run_scraper(name: str, scraper_fn, kwargs: dict) -> list[dict]:
    """Run one scraper, return list of records."""
    rows = []
    errors = []
    try:
        for r in scraper_fn(**kwargs):
            if "_error" in r:
                errors.append(r)
                continue
            rows.append(r)
    except Exception as e:
        errors.append({"_error": str(e), "_source": name})
    if errors:
        for e in errors:
            print(f"  [ERROR] {name}: {e.get('_error', e)}", file=sys.stderr)
    return rows


def main():
    ap = argparse.ArgumentParser(description="Scrape USA cotton/apparel manufacturers")
    ap.add_argument("--sources", default="textile,cotton,cfda,mnc,ncto",
                    help="Comma-separated: textile,cotton,cfda,mnc,ncto,cottonworks")
    ap.add_argument("--output", "-o", default="data/scraped_usa.csv",
                    help="Output CSV path")
    ap.add_argument("--no-detail", action="store_true",
                    help="Skip CFDA detail page fetches (faster, less contact info)")
    ap.add_argument("--quick", action="store_true",
                    help="Quick mode: textile=letters a-c only, cfda=no detail")
    args = ap.parse_args()

    source_names = [s.strip().lower() for s in args.sources.split(",")]
    by_key = {}
    for key in source_names:
        if key not in SOURCES:
            print(f"Unknown source: {key}", file=sys.stderr)
            continue
        label, fn, kwargs = SOURCES[key]
        if key == "cfda" and (args.no_detail or getattr(args, "quick", False)):
            kwargs = {**kwargs, "detail_pages": False}
        if key == "textile" and getattr(args, "quick", False):
            kwargs = {**kwargs, "letters": ["a", "b", "c"]}
        print(f"Scraping {label}...", file=sys.stderr)
        rows = run_scraper(key, fn, kwargs)
        print(f"  Got {len(rows)} records", file=sys.stderr)
        for r in rows:
            k = _dedupe_key(r)
            by_key.setdefault(k, []).append(r)

    # Merge duplicates
    merged = [_merge_records(group) for group in by_key.values()]

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not merged:
        print("No records to write", file=sys.stderr)
        return 1

    fieldnames = ["name", "city", "state", "url", "website", "buy_link", "phone", "email",
                  "type", "notes", "products", "production", "source", "source_url", "prices"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(merged)

    print(f"Wrote {len(merged)} records to {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

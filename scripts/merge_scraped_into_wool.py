#!/usr/bin/env python3
"""
Merge scraped USA wool industry into wool pipeline.

Reads data/scraped_wool.csv and combines with existing wool sources.
Output: data/wool_merged.csv

Usage:
  python scripts/merge_scraped_into_wool.py [--scraped data/scraped_wool.csv] [--output data/wool_merged.csv]
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.sources.wool import WoolSource, _enrich_record


def _key(r: dict) -> tuple:
    name = (r.get("name") or "").strip().lower()
    city = (r.get("city") or "").strip().lower()
    state = (r.get("state") or "").strip().upper()
    return (name, city, state)


def main():
    scraped_path = Path("data/scraped_wool.csv")
    out_path = Path("data/wool_merged.csv")

    if not scraped_path.exists():
        print(f"Run scrape_all_wool.py first to create {scraped_path}", file=sys.stderr)
        return 1

    # Load existing wool sources
    existing = {_key(r): r for r in WoolSource().fetch_all()}

    # Load scraped
    scraped = []
    with open(scraped_path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            scraped.append(r)

    # Merge: prefer existing, add new from scraped
    merged = list(existing.values())
    added = 0
    for r in scraped:
        k = _key(r)
        if k not in existing:
            merged.append(r)
            added += 1

    # Apply enrichment
    merged = [_enrich_record(r) for r in merged]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["name", "city", "state", "url", "website", "buy_link", "phone", "email",
                  "type", "notes", "products", "production", "source", "source_url", "prices"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(merged)

    print(f"Merged: {len(existing)} existing + {added} new = {len(merged)} total -> {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

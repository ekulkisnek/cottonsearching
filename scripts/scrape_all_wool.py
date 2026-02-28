#!/usr/bin/env python3
"""
Scrape all USA wool industry - growers to fabric makers to manufacturers.

Sources:
- ASI (American Sheep Industry): wool buyers, small & midsize mills
- Wool and Fiber Arts: US Mill Directory by state

Output: data/scraped_wool.csv (deduplicated, normalized)

Usage:
  python scripts/scrape_all_wool.py [--output data/scraped_wool.csv]
"""

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.scrapers.asi_wool import scrape as scrape_asi
from scripts.scrapers.wool_fiber_arts import scrape as scrape_wool_fiber_arts


def _dedupe_key(r: dict) -> tuple:
    name = (r.get("name") or "").strip().lower()
    city = (r.get("city") or "").strip().lower()
    state = (r.get("state") or "").strip().upper()
    return (name, city, state)


def _merge_records(records: list[dict]) -> dict:
    """Merge duplicates - prefer non-empty fields."""
    out = {}
    for r in records:
        for k, v in r.items():
            if k.startswith("_"):
                continue
            if v and (k not in out or not out.get(k)):
                out[k] = v
    return out


def main():
    ap = argparse.ArgumentParser(description="Scrape USA wool industry")
    ap.add_argument("--output", "-o", default="data/scraped_wool.csv")
    ap.add_argument("--sources", default="asi,wool_fiber_arts", help="asi,wool_fiber_arts")
    args = ap.parse_args()

    by_key = {}
    source_names = [s.strip().lower() for s in args.sources.split(",")]

    if "asi" in source_names:
        print("Scraping ASI wool directory...", file=sys.stderr)
        asi_count = 0
        for r in scrape_asi():
            k = _dedupe_key(r)
            by_key.setdefault(k, []).append(r)
            asi_count += 1
        print(f"  ASI: {asi_count} records", file=sys.stderr)

    if "wool_fiber_arts" in source_names:
        print("Scraping Wool and Fiber Arts...", file=sys.stderr)
        wfa_count = 0
        for r in scrape_wool_fiber_arts():
            k = _dedupe_key(r)
            by_key.setdefault(k, []).append(r)
            wfa_count += 1
        print(f"  Wool and Fiber Arts: {wfa_count} records", file=sys.stderr)

    merged = [_merge_records(group) for group in by_key.values()]

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

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

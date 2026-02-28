#!/usr/bin/env python3
"""
Run the full enrichment pipeline to add products and prices to as many records as possible.

Steps:
  1. Scrape (if scraped_usa.csv missing or --scrape)
  2. Merge scraped + existing buyable
  3. Enrich products (from notes, then fetch URLs for TC/MNC/company sites)
  4. Enrich prices (fetch company sites)

Usage:
  python scripts/run_enrich_all.py
  python scripts/run_enrich_all.py --scrape    # Force fresh scrape
  python scripts/run_enrich_all.py --no-prices # Skip price enrichment (faster)
"""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(cmd: list[str], desc: str) -> bool:
    print(f"\n--- {desc} ---", file=sys.stderr)
    r = subprocess.run(cmd, cwd=ROOT)
    return r.returncode == 0


def main():
    ap = argparse.ArgumentParser(description="Run full enrichment pipeline")
    ap.add_argument("--scrape", action="store_true", help="Force fresh scrape (default: only if scraped_usa.csv missing)")
    ap.add_argument("--no-prices", action="store_true", help="Skip price enrichment")
    ap.add_argument("--limit", type=int, default=None, help="Limit product enrichment to N records (for testing)")
    args = ap.parse_args()

    scraped = ROOT / "data" / "scraped_usa.csv"
    if args.scrape or not scraped.exists():
        if not run(
            [sys.executable, "scripts/scrape_all_usa.py", "-o", str(scraped)],
            "Scraping USA manufacturers",
        ):
            return 1
    else:
        print(f"Using existing {scraped}", file=sys.stderr)

    if not run(
        [sys.executable, "scripts/merge_scraped_into_buyable.py"],
        "Merging scraped + buyable (applying products from notes)",
    ):
        return 1

    product_args = [
        sys.executable, "scripts/enrich_products.py",
        "-i", "data/buyable_merged.csv",
        "-o", "data/buyable_with_products.csv",
        "--merge",
    ]
    if args.limit:
        product_args.extend(["--limit", str(args.limit)])
    if not run(product_args, "Enriching products (fetching URLs)"):
        return 1

    if not args.no_prices:
        if not run(
            [
                sys.executable, "scripts/enrich_prices.py",
                "-i", "data/buyable_with_products.csv",
                "-o", "data/buyable_full.csv",
                "--batch", "50",
            ],
            "Enriching prices",
        ):
            return 1
        print(f"\nDone. Output: data/buyable_full.csv", file=sys.stderr)
    else:
        print(f"\nDone. Output: data/buyable_with_products.csv", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

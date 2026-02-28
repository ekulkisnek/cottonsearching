#!/usr/bin/env python3
"""
Generate veal industry CSV from curated sources.

Output: data/veal_merged.csv

Usage:
  python scripts/merge_veal.py [--output data/veal_merged.csv]
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.sources.veal import VealSource, _enrich_record


def main():
    out_path = Path("data/veal_merged.csv")

    records = list(VealSource().fetch_all())
    records = [_enrich_record(r) for r in records]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "name", "city", "state", "url", "website", "buy_link",
        "phone", "email", "type", "raising", "notes", "products",
        "production", "source", "source_url", "prices",
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(records)

    pasture = sum(1 for r in records if r.get("raising") == "pasture_raised")
    conv = sum(1 for r in records if r.get("raising") == "conventional")
    both = sum(1 for r in records if r.get("raising") == "both")
    print(
        f"Wrote {len(records)} records -> {out_path}  "
        f"(pasture:{pasture}  conventional:{conv}  both:{both})",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

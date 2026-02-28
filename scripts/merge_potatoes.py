#!/usr/bin/env python3
"""
Generate organic potato industry CSV from curated sources.

Output: data/potatoes_merged.csv

Usage:
  python scripts/merge_potatoes.py [--output data/potatoes_merged.csv]
"""

import csv
import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Load potatoes module directly to avoid src.sources.__init__ (pandas dependency)
_spec = importlib.util.spec_from_file_location(
    "potatoes",
    Path(__file__).resolve().parent.parent / "src" / "sources" / "potatoes.py",
)
_potatoes = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_potatoes)
PotatoSource = _potatoes.PotatoSource
_enrich_record = _potatoes._enrich_record


def main():
    out_path = Path("data/potatoes_merged.csv")

    records = list(PotatoSource().fetch_all())
    records = [_enrich_record(r) for r in records]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "name", "city", "state", "url", "website", "buy_link",
        "phone", "email", "type", "certification", "notes", "products",
        "production", "source", "source_url", "prices",
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(records)

    organic = sum(1 for r in records if r.get("certification") == "certified_organic")
    conv = sum(1 for r in records if r.get("certification") == "conventional")
    both = sum(1 for r in records if r.get("certification") == "both")
    print(
        f"Wrote {len(records)} records -> {out_path}  "
        f"(organic:{organic}  conventional:{conv}  both:{both})",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

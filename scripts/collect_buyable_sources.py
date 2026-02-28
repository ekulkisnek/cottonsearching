#!/usr/bin/env python3
"""
Collect all valid USA cotton / apparel sources from documented directories.

Sources (100% coverage target):
- Cotton Incorporated: cottoninc.com/quality-products/textile-sourcing/cut-and-sew/
- CottonWorks U.S. Supplier List: cottonworks.com/sourcing/find-us-suppliers/ (PDF)
- CFDA Production Directory: cfda.com/resources/supply-chain-manufacturing/production-directory (380+)
- Textile Connect: textileconnect.com/directory/ (855 apparel, 186 cut & sew mfg, 115 contractors)
- ManufacturedNC: manufacturednc.com (199 NC manufacturers)
- NCTO Members: ncto.org/about/members/
- Makers Row: app.makersrow.com (3000+ USA manufacturers)

Output: CSV with name, city, state, url, website, buy_link, phone, email, type, notes, source, source_url, prices
"""

import csv
import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.sources.buyable import BuyableSource


def main():
    source = BuyableSource()
    rows = list(source.fetch_all())

    out_path = Path(__file__).parent.parent / "data" / "buyable_all.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        print("No rows to export", file=sys.stderr)
        return 0

    fieldnames = list(rows[0].keys())
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    # Summary by type
    by_type = {}
    for r in rows:
        t = r.get("type", "unknown")
        by_type[t] = by_type.get(t, 0) + 1

    print(f"Exported {len(rows)} buyable sources to {out_path}", file=sys.stderr)
    for t, n in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"  {t}: {n}", file=sys.stderr)
    return len(rows)


if __name__ == "__main__":
    sys.exit(0 if main() else 1)

#!/usr/bin/env python3
"""
Cotton Searching CLI - Locate cotton growers in the USA.

Usage:
  python -m src.cli fetch-fsa [--year 2024] [--no-download] [--output growers.csv]
  python -m src.cli fetch-nass [--output stats.csv]   # Requires NASS_API_KEY
  python -m src.cli fetch-associations [--output associations.json]
  python -m src.cli search [--state TX] [--name "Smith"]  # Search cached FSA data
  python -m src.cli export [--format csv|json] [--output out.csv]
"""

import argparse
import csv
import json
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import DATA_DIR
from src.sources.fsa import FSAPaymentSource
from src.sources.nass import NASSSource
from src.sources.state_associations import StateAssociationSource
from src.sources.datagov import DataGovSource
from src.sources.ewg_growers import EWGGrowersSource
from src.sources.ginners import GinnersSource
from src.sources.ncc_producers import NCCProducersSource
from src.sources.buyable import BuyableSource
from src.sources.wool import WoolSource
from src.sources.potatoes import PotatoSource


def cmd_fetch_fsa(args):
    """Fetch cotton growers from FSA Farm Programs Payments."""
    source = FSAPaymentSource(year=args.year)
    urls = source.urls[: args.limit] if getattr(args, "limit", None) else None
    growers = list(source.fetch_cotton_growers(download=not args.no_download, urls=urls))
    print(f"Found {len(growers)} cotton growers from FSA", file=sys.stderr)
    _write_output(growers, args.output, args.format)
    return len(growers)


def cmd_fetch_nass(args):
    """Fetch cotton statistics from NASS QuickStats API."""
    api_key = args.api_key or os.environ.get("NASS_API_KEY")
    if not api_key:
        print("Error: NASS_API_KEY required. Get key at https://quickstats.nass.usda.gov/api/", file=sys.stderr)
        return 0
    source = NASSSource(api_key=api_key)
    stats = list(source.fetch_cotton_statistics())
    print(f"Found {len(stats)} cotton statistics from NASS", file=sys.stderr)
    _write_output(stats, args.output, args.format)
    return len(stats)


def cmd_fetch_associations(args):
    """Fetch state cotton association info."""
    source = StateAssociationSource()
    assocs = list(source.fetch_associations())
    print(f"Found {len(assocs)} state associations", file=sys.stderr)
    _write_output(assocs, args.output, args.format)
    return len(assocs)


def cmd_fetch_ginners(args):
    """Fetch cotton gins and cooperatives (organizations serving growers)."""
    source = GinnersSource()
    if args.info_only:
        print(json.dumps(source.get_info(), indent=2))
        return 0
    ginners = list(source.fetch_ginners())
    print(f"Found {len(ginners)} cotton gins/cooperatives", file=sys.stderr)
    _write_output(ginners, args.output, args.format)
    return len(ginners)


def cmd_fetch_datagov(args):
    """Show Data.gov cotton datasets catalog info."""
    source = DataGovSource()
    print(json.dumps(source.get_info(), indent=2))
    return 0


def cmd_fetch_buyable(args):
    """Fetch cotton sources you can buy from (coops, merchants, direct-sale brands)."""
    source = BuyableSource(include_scraped=getattr(args, "include_scraped", False))
    if getattr(args, "type", None):
        type_filter = [t.strip().lower() for t in args.type.split(",")]
        rows = []
        fetchers = {
            "cooperative": source.fetch_cooperatives,
            "merchant": source.fetch_merchants,
            "primary_buyer": source.fetch_primary_buyers,
            "direct_sale": source.fetch_direct_sale,
            "mill": source.fetch_mills,
            "ice_warehouse": source.fetch_ice_warehouses,
            "warehouse": source.fetch_warehouses,
            "association": source.fetch_associations,
            "grower_direct": source.fetch_growers,
            "us_supplier": source.fetch_us_suppliers,
            "cut_and_sew": source.fetch_cut_and_sew,
        }
        for t in type_filter:
            if t in fetchers:
                rows.extend(fetchers[t]())
        # Deduplicate by (name, city, state)
        seen = set()
        deduped = []
        for r in rows:
            key = (r.get("name"), r.get("city", ""), r.get("state", ""))
            if key not in seen:
                seen.add(key)
                deduped.append(r)
        rows = deduped
    else:
        rows = list(source.fetch_all())
    print(f"Found {len(rows)} buyable cotton sources", file=sys.stderr)
    _write_output(rows, args.output, args.format)
    return len(rows)


def cmd_fetch_wool(args):
    """Fetch USA wool industry - growers, buyers, mills, manufacturers."""
    source = WoolSource(include_scraped=getattr(args, "include_scraped", False))
    rows = list(source.fetch_all())
    if getattr(args, "type", None):
        type_filter = [t.strip().lower() for t in args.type.split(",")]
        rows = [r for r in rows if (r.get("type") or "").lower() in type_filter]
    print(f"Found {len(rows)} wool industry sources", file=sys.stderr)
    _write_output(rows, args.output, args.format)
    return len(rows)


def cmd_fetch_potatoes(args):
    """Fetch USA organic potato industry - farms, processors, retailers."""
    source = PotatoSource()
    rows = list(source.fetch_all())
    if getattr(args, "type", None):
        type_filter = [t.strip().lower() for t in args.type.split(",")]
        rows = [r for r in rows if (r.get("type") or "").lower() in type_filter]
    if getattr(args, "certification", None):
        cert_filter = [c.strip().lower() for c in args.certification.split(",")]
        rows = [r for r in rows if (r.get("certification") or "").lower() in cert_filter]
    print(f"Found {len(rows)} organic potato sources", file=sys.stderr)
    _write_output(rows, args.output, args.format)
    return len(rows)


def cmd_fetch_growers(args):
    """Fetch cotton growers from EWG and NCC (actual farm names)."""
    growers = []
    seen = set()
    for g in EWGGrowersSource().fetch_growers():
        key = (g["name"], g.get("city", ""), g.get("state", ""))
        if key not in seen:
            seen.add(key)
            growers.append(g)
    for g in NCCProducersSource().fetch_growers():
        key = (g["name"], g.get("city", ""), g.get("state", ""))
        if key not in seen:
            seen.add(key)
            growers.append(g)
    print(f"Found {len(growers)} cotton growers (EWG + NCC)", file=sys.stderr)
    _write_output(growers, args.output, args.format)
    return len(growers)


def cmd_export(args):
    """Export combined data from cached FSA growers."""
    cache_dir = Path(DATA_DIR) / "fsa"
    if not cache_dir.exists():
        print("No cached FSA data. Run 'fetch-fsa' first.", file=sys.stderr)
        return 0
    source = FSAPaymentSource()
    growers = list(source.fetch_cotton_growers(download=False))
    print(f"Exported {len(growers)} cotton growers", file=sys.stderr)
    _write_output(growers, args.output, args.format)
    return len(growers)


def cmd_search(args):
    """Search cached FSA cotton growers by state and/or name."""
    cache_dir = Path(DATA_DIR) / "fsa"
    if not cache_dir.exists():
        print("No cached FSA data. Run 'fetch-fsa' first.", file=sys.stderr)
        return 0
    source = FSAPaymentSource()
    growers = list(source.fetch_cotton_growers(download=False))
    if args.state:
        state_upper = args.state.upper()
        growers = [g for g in growers if (g.get("state") or "").upper() == state_upper]
    if args.name:
        name_lower = args.name.lower()
        growers = [g for g in growers if name_lower in (g.get("name") or "").lower()]
    print(f"Found {len(growers)} matching cotton growers", file=sys.stderr)
    _write_output(growers, args.output, args.format)
    return len(growers)


def cmd_fetch_all(args):
    """Fetch all available cotton industry data (growers, ginners, associations)."""
    all_rows = []
    seen_growers = set()
    # EWG + NCC cotton growers
    for g in EWGGrowersSource().fetch_growers():
        g["category"] = "grower"
        key = (g["name"], g.get("city", ""), g.get("state", ""))
        if key not in seen_growers:
            seen_growers.add(key)
            all_rows.append(g)
    for g in NCCProducersSource().fetch_growers():
        g["category"] = "grower"
        key = (g["name"], g.get("city", ""), g.get("state", ""))
        if key not in seen_growers:
            seen_growers.add(key)
            all_rows.append(g)
    # Ginners
    ginners = list(GinnersSource().fetch_ginners())
    for g in ginners:
        g["category"] = "gin/cooperative"
        all_rows.append(g)
    # Associations
    for a in StateAssociationSource().fetch_associations():
        a["category"] = "association"
        all_rows.append(a)
    print(f"Found {len(all_rows)} total entries (growers + ginners + associations)", file=sys.stderr)
    _write_output(all_rows, args.output, args.format)
    return len(all_rows)


def _write_output(rows: list, output: str | None, fmt: str):
    """Write rows to file or stdout."""
    if not rows:
        return
    out = open(output, "w", newline="", encoding="utf-8") if output else sys.stdout
    try:
        if fmt == "json":
            json.dump(rows, out, indent=2, default=str)
        else:
            w = csv.DictWriter(out, fieldnames=list(rows[0].keys()), extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
    finally:
        if output:
            out.close()


def main():
    parser = argparse.ArgumentParser(description="Cotton Searching - Locate cotton growers in the USA")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # fetch-fsa
    p_fsa = sub.add_parser("fetch-fsa", help="Fetch cotton growers from FSA Farm Programs Payments")
    p_fsa.add_argument("--year", type=int, default=2024, help="Payment year")
    p_fsa.add_argument("--no-download", action="store_true", help="Use cached files only")
    p_fsa.add_argument("--limit", type=int, default=None, help="Limit to first N files (for testing)")
    p_fsa.add_argument("--output", "-o", help="Output file (default: stdout)")
    p_fsa.add_argument("--format", "-f", choices=["csv", "json"], default="csv")
    p_fsa.set_defaults(func=cmd_fetch_fsa)

    # fetch-nass
    p_nass = sub.add_parser("fetch-nass", help="Fetch cotton statistics from NASS QuickStats API")
    p_nass.add_argument("--api-key", help="NASS API key (or set NASS_API_KEY)")
    p_nass.add_argument("--output", "-o", help="Output file")
    p_nass.add_argument("--format", "-f", choices=["csv", "json"], default="csv")
    p_nass.set_defaults(func=cmd_fetch_nass)

    # fetch-associations
    p_assoc = sub.add_parser("fetch-associations", help="Fetch state cotton association info")
    p_assoc.add_argument("--output", "-o", help="Output file")
    p_assoc.add_argument("--format", "-f", choices=["csv", "json"], default="json")
    p_assoc.set_defaults(func=cmd_fetch_associations)

    # fetch-ginners
    p_gin = sub.add_parser("fetch-ginners", help="Fetch cotton gins and cooperatives")
    p_gin.add_argument("--info-only", action="store_true", help="Show metadata only")
    p_gin.add_argument("--output", "-o", help="Output file")
    p_gin.add_argument("--format", "-f", choices=["csv", "json"], default="csv")
    p_gin.set_defaults(func=cmd_fetch_ginners)

    # fetch-datagov
    p_dg = sub.add_parser("fetch-datagov", help="Show Data.gov cotton datasets catalog info")
    p_dg.set_defaults(func=cmd_fetch_datagov)

    # fetch-buyable
    p_buy = sub.add_parser("fetch-buyable", help="Fetch cotton sources you can buy from (coops, merchants, direct-sale)")
    p_buy.add_argument("--output", "-o", help="Output file")
    p_buy.add_argument("--format", "-f", choices=["csv", "json"], default="csv")
    p_buy.add_argument("--type", "-t", help="Filter by type(s): cooperative,merchant,primary_buyer,direct_sale,mill,ice_warehouse,warehouse,association,grower_direct,us_supplier,cut_and_sew")
    p_buy.add_argument("--include-scraped", action="store_true", help="Include scraped USA manufacturers from data/scraped_usa.csv")
    p_buy.set_defaults(func=cmd_fetch_buyable)

    # fetch-wool
    p_wool = sub.add_parser("fetch-wool", help="Fetch USA wool industry (growers, buyers, mills, manufacturers)")
    p_wool.add_argument("--output", "-o", help="Output file")
    p_wool.add_argument("--format", "-f", choices=["csv", "json"], default="csv")
    p_wool.add_argument("--type", "-t", help="Filter by type: wool_buyer,wool_mill,wool_processor,wool_fabric,wool_apparel,association")
    p_wool.add_argument("--include-scraped", action="store_true", help="Include scraped from data/scraped_wool.csv")
    p_wool.set_defaults(func=cmd_fetch_wool)

    # fetch-potatoes
    p_potatoes = sub.add_parser("fetch-potatoes", help="Fetch USA organic potato industry (farms, processors, retailers)")
    p_potatoes.add_argument("--output", "-o", help="Output file")
    p_potatoes.add_argument("--format", "-f", choices=["csv", "json"], default="csv")
    p_potatoes.add_argument("--type", "-t", help="Filter by type: potato_farm,potato_processor,potato_retailer,potato_wholesale,association")
    p_potatoes.add_argument("--certification", "-c", help="Filter by certification: certified_organic,conventional,both")
    p_potatoes.set_defaults(func=cmd_fetch_potatoes)

    # fetch-growers (EWG - actual farm names)
    p_gr = sub.add_parser("fetch-growers", help="Fetch cotton growers from EWG (actual farm names)")
    p_gr.add_argument("--output", "-o", help="Output file")
    p_gr.add_argument("--format", "-f", choices=["csv", "json"], default="csv")
    p_gr.set_defaults(func=cmd_fetch_growers)

    # fetch-all
    p_all = sub.add_parser("fetch-all", help="Fetch all cotton gins, co-ops, and associations")
    p_all.add_argument("--output", "-o", help="Output file")
    p_all.add_argument("--format", "-f", choices=["csv", "json"], default="csv")
    p_all.set_defaults(func=cmd_fetch_all)

    # export
    p_exp = sub.add_parser("export", help="Export cached FSA cotton growers")
    p_exp.add_argument("--output", "-o", help="Output file")
    p_exp.add_argument("--format", "-f", choices=["csv", "json"], default="csv")
    p_exp.set_defaults(func=cmd_export)

    # search
    p_search = sub.add_parser("search", help="Search cached FSA growers by state/name")
    p_search.add_argument("--state", "-s", help="Filter by state (e.g. TX)")
    p_search.add_argument("--name", "-n", help="Filter by name (substring)")
    p_search.add_argument("--output", "-o", help="Output file")
    p_search.add_argument("--format", "-f", choices=["csv", "json"], default="csv")
    p_search.set_defaults(func=cmd_search)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

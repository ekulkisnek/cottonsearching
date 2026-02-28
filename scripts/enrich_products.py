#!/usr/bin/env python3
"""
Enrich records with products/capabilities by checking each website.

Extracts product/category info from company sites when products field is empty.
Looks for: product lists, service offerings, category keywords, "we make", "we offer", etc.

Usage:
  python scripts/enrich_products.py [--input data/buyable_merged.csv] [--output data/buyable_with_products.csv]
  python scripts/enrich_products.py --limit 30 --delay 1.0
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

from src.sources.buyable import _enrich_record
from bs4 import BeautifulSoup

# Skip these - directory hubs, not company sites (we don't fetch these for product extraction)
SKIP_DOMAINS = (
    "cottoninc.com", "cfda.com", "ncto.org", "cottonworks.com", "acsa-cotton.org",
)
# Textile Connect and ManufacturedNC - we DO fetch these (directory detail pages have product info)
DIRECTORY_DOMAINS = ("textileconnect.com", "manufacturednc.com")


def _get_url(r: dict) -> tuple[str | None, bool]:
    """Return (url, is_directory). Directory URLs (TC, MNC) get detail page scraped."""
    for k in ("website", "buy_link", "url"):
        u = (r.get(k) or "").strip()
        if not u or not u.startswith("http"):
            continue
        if any(d in u for d in SKIP_DOMAINS):
            continue
        is_dir = any(d in u for d in DIRECTORY_DOMAINS)
        return (u, is_dir)
    return (None, False)


def _extract_from_textile_connect(html: str) -> str:
    """Extract products from Textile Connect detail page."""
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    found = []
    # Company Category
    m = re.search(r"Company Category\s*([^\n]+?)(?:\n|Company Excerpt|Description|$)", text, re.I)
    if m:
        found.append(m.group(1).strip()[:80])
    # Company Excerpt
    m = re.search(r"Company Excerpt\s*([^\n]+?)(?:\n|Description|Primary|$)", text, re.I)
    if m:
        found.append(m.group(1).strip()[:100])
    # Description: "Embroidery"
    if "Description" in text:
        idx = text.find("Description")
        chunk = text[idx : idx + 200]
        for line in chunk.split("\n"):
            line = line.strip()
            if line and line != "Description" and len(line) < 80:
                found.append(line)
                break
    # Primary NAICS Code: "Narrow Fabric Mills and Schiffli Machine Embroidery (313220)"
    m = re.search(r"Primary NAICS Code\s*([^\n]+?)(?:\n|$)", text, re.I)
    if m:
        found.append(m.group(1).strip()[:80])
    # Primary Brand
    m = re.search(r"Primary Brand\s*([^\n]+?)(?:\n|$)", text, re.I)
    if m:
        found.append("Brand: " + m.group(1).strip()[:40])
    return "; ".join(found[:8]) if found else ""


def _extract_from_manufactured_nc(html: str) -> str:
    """Extract products from ManufacturedNC company detail page."""
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    found = []
    m = re.search(r"Primary Industry Classification:\s*([^\n]+?)(?:\n|Established)", text, re.I)
    if m:
        found.append(m.group(1).strip()[:60])
    m = re.search(r"Materials List:\s*([^\n]+)", text, re.I)
    if m:
        found.append("Materials: " + m.group(1).strip()[:80])
    m = re.search(r"Industries We Serve\s*([^\n]+?)(?:\s+Specializing|With a typical)", text, re.I)
    if m:
        found.append(m.group(1).strip()[:60])
    m = re.search(r"Specializing in\s+([^\n]+?)(?:\s+With a typical|$)", text, re.I)
    if m:
        found.append(m.group(1).strip()[:60])
    # "About Our Company" description (text before Primary Industry / What Makes)
    m = re.search(r"About Our Company\s+(.+?)(?:\s+Primary Industry|What Makes|$)", text, re.I | re.DOTALL)
    if m:
        desc = re.sub(r"\s+", " ", m.group(1).strip())[:100]
        if len(desc) > 15:
            found.append(desc)
    return "; ".join(found[:8]) if found else ""


def _extract_production_from_manufactured_nc(html: str) -> str:
    """Extract production/volume from ManufacturedNC detail page (e.g. typical monthly production volume)."""
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    m = re.search(r"(?:with\s+a\s+)?typical\s+monthly\s+production\s+volume\s+of\s+([\d\s,\-]+)", text, re.I)
    if m:
        return "Monthly: " + m.group(1).strip()[:50]
    return ""


def _extract_production(html: str) -> str:
    """Extract production/volume indicators from company page."""
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    found = []
    # bales/yr, bales/year, units/year
    m = re.search(r"[~]?[\d\s,\.\-KkMm]+(?:\s*bales?/?(?:yr|year)|bales?\s*(?:per|/)\s*year)", text, re.I)
    if m:
        found.append(m.group(0).strip()[:50])
    # capacity, production volume
    m = re.search(r"(?:capacity|production\s+volume|annual\s+production)\s*[:\s]*([\d\s,\.\-KkMm]+(?:\s*(?:bales?|units?|yards?|lbs?|tons?|million))?)", text, re.I)
    if m:
        found.append("Capacity: " + m.group(1).strip()[:40])
    # MOQ
    m = re.search(r"(?:moq|minimum\s+order)\s*[:\s]*([\d\s,\.\-KkMm]+(?:\s*(?:units?|pieces?|yards?|lbs?))?)", text, re.I)
    if m:
        found.append("MOQ: " + m.group(1).strip()[:30])
    # employees (proxy for scale)
    m = re.search(r"(\d[\d,]+)\s*(?:employees?|people|staff)\s*(?:worldwide|globally|in\s+\w+)?", text, re.I)
    if m:
        found.append(m.group(1).strip() + " employees")
    return "; ".join(found[:3]) if found else ""


def _fetch(url: str, timeout: int = 12) -> str | None:
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "CottonSearching/1.0"}, verify=False)
        r.raise_for_status()
        return r.text
    except Exception:
        return None


def _extract_products(html: str) -> str:
    """Extract product/capability keywords from page."""
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True).lower()

    # Product/category keywords (apparel & textile) - expanded
    keywords = [
        "apparel", "garments", "clothing", "t-shirts", "tees", "hoodies", "denim", "jeans",
        "knits", "woven", "fabric", "yarn", "textile", "embroidery", "screen print",
        "cut and sew", "cut & sew", "cmt", "wholesale", "manufacturing", "custom",
        "uniforms", "workwear", "activewear", "athletic", "home textiles", "linens",
        "towels", "terry", "jersey", "fleece", "dyeing", "finishing", "printing",
        "spinning", "weaving", "knitting", "cotton", "organic cotton", "sustainable",
        "sublimation", "dtg", "dtf", "heat transfer", "patches", "labels", "badges",
        "promotional", "blank apparel", "sportswear", "outerwear", "dresses", "shirts",
        "pants", "shorts", "sweatshirts", "polos", "henleys", "underwear", "socks",
        "hosiery", "technical fabric", "industrial", "medical", "military", "tactical",
        "upholstery", "automotive", "marine", "awning", "canvas", "banners", "flags",
        "narrow fabric", "elastic", "webbing", "trim", "ribbon", "lace", "velvet",
        "jacquard", "flannel", "broadcloth", "poplin", "oxford", "twill", "corduroy",
        "seersucker", "chambray", "pique", "interlock", "french terry", "sweater knit",
        "dyehouse", "washhouse", "garment dye", "stone wash", "enzyme wash",
        "mercerizing", "sanforizing", "napping", "brushing", "coating", "lamination",
        # Additional product terms
        "bags", "backpacks", "caps", "hats", "headwear", "bedding", "blankets",
        "sheets", "pillowcases", "scrubs", "ppe", "hospital", "healthcare",
        "aprons", "bibs", "tablecloths", "napkins", "curtains", "drapery",
        "seamless", "circular knit", "warp knit", "weft knit", "double knit",
        "single knit", "rib knit", "flat knit", "tubular", "dyed yarn",
        "piece dye", "yarn dye", "solution dye", "reactive dye", "disperse dye",
        "digital print", "rotary print", "screen printing", "direct to garment",
        "direct to film", "heat press", "vinyl", "appliqué", "monogramming",
        "private label", "full package", "cut-make-trim", "sample development",
        "pattern making", "grading", "tech packs", "small batch", "low moq",
        "made in usa", "domestic", "import", "contract manufacturing",
        # More product terms
        "vests", "jackets", "sweaters", "cardigans", "blouses", "skirts",
        "leggings", "athleisure", "performance wear", "compression",
        "fire resistant", "fr", "arc rated", "high visibility", "hi-vis",
        "safety apparel", "protective gear", "coveralls", "overalls",
        "pillow", "mattress", "drapes", "blinds", "shade", "shutters",
        "tote", "duffel", "messenger", "laptop bag", "backpack",
        "bandana", "neck gaiter", "scarf", "gloves", "mittens",
        "baby", "infant", "children", "kids", "toddler",
        "hospitality", "hotel", "restaurant", "food service",
        "institutional", "government", "commercial", "contract",
        "recycled", "upcycled", "deadstock", "sustainable", "eco",
        "gots", "oeko-tex", "bluesign", "certified",
        "knitwear", "sweater knit", "rib knit", "flat knit",
        "warp knit", "raschel", "tricot", "lace knit",
        "woven", "plain weave", "twill weave", "satin weave",
        "nonwoven", "felt", "bonded", "fused",
        "knit fabric", "woven fabric", "blended", "blend",
    ]
    found = []
    for kw in keywords:
        if kw in text and kw not in found:
            found.append(kw)

    # "We offer", "We make", "Products:", "Services:", "Capabilities:"
    for pattern in [
        r"(?:we\s+(?:offer|make|manufacture|produce|provide|specialize)\s+(?:in\s+)?)([^.]{8,120})",
        r"(?:products?:\s*|services?:\s*|capabilities?:\s*)([^.]{8,120})",
        r"(?:specializing\s+in\s+)([^.]{8,100})",
        r"(?:our\s+(?:products?|services?)\s+include[:\s]+)([^.]{8,120})",
        r"(?:expertise\s+in\s+)([^.]{8,100})",
        r"(?:focus\s+on\s+)([^.]{8,100})",
        r"(?:known\s+for\s+)([^.]{8,100})",
        r"(?:manufacturing\s+)([^.]{8,100})",
        r"(?:producing\s+)([^.]{8,100})",
        r"(?:what\s+we\s+(?:do|make|offer)[:\s]+)([^.]{8,120})",
        r"(?:product\s+lines?[:\s]+)([^.]{8,120})",
        r"(?:we\s+create\s+)([^.]{8,100})",
        r"(?:services\s+include[:\s]+)([^.]{8,120})",
        r"(?:we\s+do\s+)([^.]{8,100})",
        r"(?:our\s+specialty\s+is\s+)([^.]{8,100})",
        r"(?:core\s+(?:products?|business)[:\s]+)([^.]{8,120})",
        r"(?:built\s+for\s+)([^.]{8,80})",
        r"(?:serving\s+(?:the\s+)?)([^.]{8,80})",
        r"(?:ideal\s+for\s+)([^.]{8,80})",
        r"(?:target\s+(?:market|audience)[:\s]+)([^.]{8,80})",
        r"(?:applications?[:\s]+)([^.]{8,120})",
        r"(?:end\s+use[:\s]+)([^.]{8,80})",
    ]:
        m = re.search(pattern, text, re.I)
        if m:
            snippet = re.sub(r"\s+", " ", m.group(1).strip())[:100]
            if len(snippet) > 12 and snippet not in str(found).lower():
                found.append(snippet)

    # NAICS-style: "313220" = Narrow Fabric Mills
    naics_match = re.search(r"naics\s*(?:code)?\s*[:\s]*(\d{6})\s*[–\-]?\s*([^<\n]{10,80})", text, re.I)
    if naics_match:
        found.append(naics_match.group(2).strip()[:60])

    # SIC / industry codes
    sic_match = re.search(r"sic\s*(?:code)?\s*[:\s]*(\d{4})\s*[–\-]?\s*([^<\n]{10,80})", text, re.I)
    if sic_match:
        found.append(sic_match.group(2).strip()[:60])

    # "Industry:" or "Industries:" lines
    ind_match = re.search(r"industr(?:y|ies)\s*[:\s]+([^<\n]{8,80})", text, re.I)
    if ind_match:
        found.append(ind_match.group(1).strip()[:60])

    # "Applications:" or "Markets:" or "End use:"
    for label in [r"applications?", r"markets?", r"end\s+use", r"target\s+markets?"]:
        m = re.search(rf"{label}\s*[:\s]+([^<\n]{{8,80}})", text, re.I)
        if m:
            found.append(m.group(1).strip()[:60])

    # "Materials:" or "Fibers:" beyond NAICS
    mat_match = re.search(r"(?:materials?|fibers?)\s*[:\s]+([^<\n]{8,100})", text, re.I)
    if mat_match:
        found.append("Materials: " + mat_match.group(1).strip()[:70])

    # Dedupe and limit
    seen = set()
    out = []
    for f in found:
        f = str(f).strip().title()
        if f and f not in seen and len(f) > 2:
            seen.add(f)
            out.append(f)
    return "; ".join(out[:28]) if out else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", "-i", default="data/buyable_merged.csv")
    ap.add_argument("--output", "-o", default="data/buyable_with_products.csv")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--delay", type=float, default=1.0)
    ap.add_argument("--skip-filled", action="store_true", help="Skip records that already have products")
    ap.add_argument("--merge", action="store_true", help="Merge new findings into existing products")
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

    # Pre-fill products from notes/type for any record missing them
    rows = [_enrich_record(r) for r in rows]

    to_check = []
    for r in rows:
        url, _ = _get_url(r)
        if not url:
            continue
        if args.skip_filled and (r.get("products") or "").strip():
            continue
        to_check.append(r)

    if args.limit:
        to_check = to_check[: args.limit]

    print(f"Enriching products for {len(to_check)} records...", file=sys.stderr)
    updated = 0
    for r in to_check:
        url, is_directory = _get_url(r)
        if not url:
            continue
        html = _fetch(url)
        if not html:
            continue
        if is_directory and "textileconnect.com" in url:
            products = _extract_from_textile_connect(html)
            production = ""
        elif is_directory and "manufacturednc.com" in url:
            products = _extract_from_manufactured_nc(html)
            production = _extract_production_from_manufactured_nc(html)
        else:
            products = _extract_products(html)
            production = _extract_production(html)
        existing = (r.get("products") or "").strip()
        existing_prod = (r.get("production") or "").strip()
        if products:
            if not existing:
                r["products"] = products
                updated += 1
                print(f"  {r.get('name','')[:40]}: {products[:70]}...", file=sys.stderr)
            elif len(products) > len(existing):
                r["products"] = products
                updated += 1
                print(f"  {r.get('name','')[:40]}: {products[:70]}...", file=sys.stderr)
            elif getattr(args, "merge", False) and existing:
                existing_lower = existing.lower()
                new_bits = [p for p in products.split("; ") if p.strip().lower() not in existing_lower]
                if new_bits:
                    r["products"] = existing + "; " + "; ".join(new_bits[:5])
                    updated += 1
                    print(f"  {r.get('name','')[:40]}: +{len(new_bits)} more", file=sys.stderr)
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

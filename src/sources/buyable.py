"""
Cotton sources you can buy from.

Cooperatives, merchants, and direct-sale brands that sell cotton (or cotton products)
to buyers. These are the entities that connect growers to purchasers.
"""

import re
from pathlib import Path
from typing import Iterator

# Standard contact fields for all records
CONTACT_FIELDS = ("email", "phone", "website", "buy_link", "prices", "products", "production")

# Default products by type when not specified
TYPE_PRODUCTS = {
    "cooperative": "Cotton bales",
    "merchant": "Cotton; commodity trading",
    "primary_buyer": "Cotton; mill service",
    "direct_sale": "Cotton apparel; sheets; towels",
    "mill": "Yarn; fabric",
    "us_supplier": "Yarn; fabric; textiles",
    "warehouse": "Cotton storage; warehousing",
    "ice_warehouse": "Cotton storage; ICE licensed",
    "cut_and_sew": "Apparel; garments; cut & sew",
    "apparel_manufacturer": "Apparel; knit fabrics",
    "manufacturer": "Apparel; textiles; manufacturing",
    "fabric_wholesaler": "Fabric; cotton wholesale",
    "association": "Industry directory; referrals",
    "platform": "Cotton marketplace",
    "grower_direct": "Cotton; direct from farm",
    "textile_manufacturer": "Textiles; fabric; yarn",
    "raw_materials": "Fiber; yarn; raw materials",
}


# Product-like terms to recognize in notes (case-insensitive)
_NOTES_PRODUCT_TERMS = (
    "apparel", "garments", "knits", "woven", "denim", "home", "ppe", "uniforms",
    "cmt", "cut and sew", "embroidery", "screen print", "sublimation", "dtg", "dtf",
    "terry", "jersey", "fleece", "towels", "linens", "fabric", "yarn", "textile",
    "workwear", "activewear", "athletic", "medical", "hospital", "military", "tactical",
    "industrial", "automotive", "marine", "upholstery", "jacquard", "technical fabric",
    "dyehouse", "washhouse", "wholesale", "private label", "full package",
    "fashion", "fashion manufacturing", "cut & sew", "cottonworks", "cotton inc",
    "ncto", "narrow fabric", "elastic", "webbing", "patches", "labels", "badges",
    "fire resistant", "fr", "arc rated", "safety", "protective", "coveralls",
    "bedding", "blankets", "sheets", "scrubs", "hospitality", "institutional",
)

def _products_from_notes(notes: str) -> str:
    """Extract product-like terms from notes when no explicit products given."""
    if not notes:
        return ""
    notes_lower = notes.lower()
    # 1. Match leading product lists: "Knits, Apparel; ..." or "Apparel, Home, PPE, Uniforms"
    m = re.match(r"^([A-Za-z][^;]+(?:;[^;]+){0,3})", notes)
    if m:
        chunk = m.group(1)
        parts = [p.strip() for p in re.split(r"[,;]", chunk) if 2 <= len(p.strip()) <= 40]
        if parts:
            return "; ".join(parts[:10])
    # 2. Extract "Textile Connect: category" or "Cotton Inc: X" from notes
    m = re.search(r"Textile Connect:\s*([a-z0-9\-]+)", notes_lower)
    if m:
        cat = m.group(1).replace("-", " ").title()
        if len(cat) > 3:
            return cat
    m = re.search(r"Cotton Inc[orporated]*[:\s]+([^;]+)", notes, re.I)
    if m:
        return m.group(1).strip()[:80]
    # CFDA Production Directory
    if "cfda" in notes_lower or "fashion manufacturing" in notes_lower:
        return "Fashion manufacturing; apparel"
    # NCTO council type
    m = re.search(r"NCTO[:\s]+([^;]+)", notes, re.I)
    if m:
        return m.group(1).strip()[:80]
    m = re.search(r"(?:Fabric & Home Products|Finished Textile & Apparel|Yarn spinning|Industry Support)", notes, re.I)
    if m:
        return m.group(0).strip()[:80]
    # ManufacturedNC: "Apparel; Textiles; NC manufacturer"
    if "manufacturednc" in notes_lower or "manufactured nc" in notes_lower:
        return "Apparel; Textiles; NC manufacturer"
    # 3. Extract known product terms mentioned anywhere in notes
    found = []
    for term in _NOTES_PRODUCT_TERMS:
        if term in notes_lower and term not in found:
            found.append(term.title())
    if found:
        return "; ".join(found[:12])
    return ""


def _production_from_notes(notes: str) -> str:
    """Extract production/volume indicators from notes."""
    if not notes:
        return ""
    # "~400K bales/year", "50K-65K bales/yr", "~1.5M+ bales/yr"
    m = re.search(r"[~]?[\d\s,\.\-+KkMm]+(?:\s*bales?/?(?:yr|year)|bales?\s*(?:per|/)\s*year)", notes, re.I)
    if m:
        return m.group(0).strip()[:60]
    m = re.search(r"(?:typical\s+)?(?:monthly\s+)?\s*production\s*volume\s*[:\s]*([\d\s,\-]+)", notes, re.I)
    if m:
        return "Monthly: " + m.group(1).strip()[:40]
    m = re.search(r"(\d[\d,\.]+)\s*[KkMm]?\s*(?:bales?|units?|yards?|lbs?|tons?)\s*(?:/|per)\s*(?:yr|year)|(\d[\d,\.]+)\s*[KkMm]?\s*(?:bales?|units?|yards?|lbs?)\s*(?:annually|yearly)", notes, re.I)
    if m:
        return (m.group(1) or m.group(2) or "").strip()[:50]
    # "5,000+ SE growers", "X growers"
    m = re.search(r"([\d,\.]+)\+?\s*(?:\w+\s+)?(?:growers?|members?|employees?)", notes, re.I)
    if m:
        return m.group(0).strip()[:50]
    return ""


def _enrich_record(r: dict, default_prices: str = "Contact for quote") -> dict:
    """Add email, phone, website, buy_link, prices, products, production; normalize url -> website."""
    out = dict(r)
    out.setdefault("email", "")
    out.setdefault("phone", "")
    out.setdefault("website", r.get("url", ""))
    out.setdefault("buy_link", r.get("buy_link", r.get("url", "")))
    out.setdefault("prices", default_prices)
    if not out.get("production"):
        out["production"] = r.get("production") or _production_from_notes(r.get("notes", ""))
    if not out.get("products"):
        out["products"] = (
            r.get("products")
            or _products_from_notes(r.get("notes", ""))
            or TYPE_PRODUCTS.get(out.get("type", ""), "")
        )
    return out

# Cooperatives - buy cotton bales; they aggregate member grower cotton
# AMCOT members: PCCA, Calcot, Staplcotn, Carolinas - ~40% of US cotton
# Source: AMCOT, web research
BUYABLE_COOPERATIVES = [
    {
        "name": "Plains Cotton Cooperative Association (PCCA)",
        "city": "Lubbock",
        "state": "TX",
        "url": "https://pcca.com/",
        "website": "https://pcca.com/",
        "buy_link": "https://pcca.com/contact/",
        "phone": "806-763-8011",
        "email": "",
        "type": "cooperative",
        "notes": "Largest farmer-owned cotton coop; West TX, OK, KS; ~1.5M+ bales/yr; buy cotton bales",
        "prices": "Contact for quote; cotton priced daily",
        "source": "AMCOT",
        "source_url": "https://amcot.org/",
    },
    {
        "name": "Calcot",
        "city": "Bakersfield",
        "state": "CA",
        "url": "https://calcot.com/",
        "website": "https://calcot.com/",
        "buy_link": "https://calcot.com/sales-contact/",
        "phone": "661-327-5961",
        "email": "info@calcot.com",
        "type": "cooperative",
        "notes": "CA, AZ, NM cotton; Upland & Pima; ~400K bales/year",
        "prices": "Contact for quote; cotton priced daily",
        "source": "AMCOT",
        "source_url": "https://amcot.org/",
    },
    {
        "name": "Staple Cotton Cooperative Association (Staplcotn)",
        "city": "Greenwood",
        "state": "MS",
        "url": "https://www.staplcotn.com/",
        "website": "https://www.staplcotn.com/",
        "buy_link": "https://www.staplcotn.com/contact/",
        "phone": "662-453-6231",
        "email": "cotton.services@staplcotn.com",
        "type": "cooperative",
        "notes": "5,000+ SE growers; 11 states; Memphis/Eastern cotton; Mill Sales Program",
        "prices": "Contact for quote; cotton priced daily",
        "source": "AMCOT",
        "source_url": "https://amcot.org/",
    },
    {
        "name": "Carolinas Cotton Growers Cooperative",
        "city": "Garner",
        "state": "NC",
        "url": "https://www.carolinascotton.com/",
        "website": "https://www.carolinascotton.com/",
        "buy_link": "https://www.carolinascotton.com/contact-us",
        "phone": "919-773-2120",
        "email": "ckramer@carolinascotton.com",
        "type": "cooperative",
        "notes": "NC/SC growers; cotton sales & warehousing; marketing ckramer@carolinascotton.com",
        "prices": "Contact for quote; cotton priced daily",
        "source": "AMCOT",
        "source_url": "https://amcot.org/",
    },
    {
        "name": "Texas Cotton Growers Cooperative Association",
        "city": "Taylor",
        "state": "TX",
        "url": "https://txagcouncil.org/texas-cotton-producers-inc/",
        "website": "https://txagcouncil.org/texas-cotton-producers-inc/",
        "buy_link": "https://txagcouncil.org/texas-cotton-producers-inc/",
        "phone": "512-365-5531",
        "email": "",
        "type": "cooperative",
        "notes": "Texas cotton marketing",
        "prices": "Contact for quote",
        "source": "AMCOT",
        "source_url": "https://amcot.org/",
    },
]

# Merchants - buy US cotton; they source from growers/coops
# ACSA members handle 80%+ of US cotton sold domestically and abroad
# Source: acsa-cotton.org/our-members; contact ACSA 901-525-2272 for member directory
ACSA_SOURCE = {"source": "ACSA", "source_url": "https://acsa-cotton.org/our-members"}
ACSA_REFERRAL = {"website": "https://acsa-cotton.org/our-members", "buy_link": "https://acsa-cotton.org/our-members", "phone": "901-525-2272"}
BUYABLE_MERCHANTS = [
    {"name": "ACG Cotton Marketing LLC", "city": "Lubbock", "state": "TX", "type": "merchant", "notes": "ACSA; cotton jobber; Lubbock; contact via ACSA", **ACSA_SOURCE, **ACSA_REFERRAL},
    {"name": "ADM Cotton", "city": "Memphis", "state": "TN", "type": "merchant", "notes": "ACSA merchant; contact via ACSA", **ACSA_SOURCE, **ACSA_REFERRAL},
    {"name": "Allbright Cotton", "city": "Memphis", "state": "TN", "url": "https://www.allbrightcotton.com/", "website": "https://www.allbrightcotton.com/", "buy_link": "https://www.allbrightcotton.com/", "phone": "559-276-1664", "email": "", "type": "merchant", "notes": "Supima & Acala; California & Southwest; Fresno office", **ACSA_SOURCE},
    {"name": "America Tongzhou Cotton Trading Inc", "city": "Memphis", "state": "TN", "type": "merchant", "notes": "ACSA merchant; contact via ACSA", **ACSA_SOURCE, **ACSA_REFERRAL},
    {"name": "Brighann Marketing Inc", "city": "Memphis", "state": "TN", "type": "merchant", "notes": "ACSA merchant; contact via ACSA", **ACSA_SOURCE, **ACSA_REFERRAL},
    {"name": "Bunge", "city": "Memphis", "state": "TN", "type": "merchant", "notes": "ACSA merchant; global commodities; contact via ACSA", **ACSA_SOURCE, **ACSA_REFERRAL},
    {"name": "C&D (USA) Inc", "city": "Memphis", "state": "TN", "type": "merchant", "notes": "ACSA merchant; contact via ACSA", **ACSA_SOURCE, **ACSA_REFERRAL},
    {"name": "Cargill Cotton", "city": "Memphis", "state": "TN", "url": "https://www.cargill.com/agriculture/cotton", "website": "https://www.cargill.com/agriculture/cotton", "buy_link": "https://www.cargill.com/agriculture/cotton/location-contact-us", "phone": "901-454-7851", "email": "", "type": "merchant", "notes": "Global cotton; Memphis, Liverpool", **ACSA_SOURCE},
    {"name": "COFCO Americas Resources Corp", "city": "Memphis", "state": "TN", "type": "merchant", "notes": "ACSA merchant; contact via ACSA", **ACSA_SOURCE, **ACSA_REFERRAL},
    {"name": "Colly Commodities Inc", "city": "Memphis", "state": "TN", "type": "merchant", "notes": "ACSA merchant; contact via ACSA", **ACSA_SOURCE, **ACSA_REFERRAL},
    {"name": "Commonwealth Gin", "city": "Windsor", "state": "VA", "type": "merchant", "notes": "ACSA; gin & merchant; Virginia cotton; contact via ACSA", **ACSA_SOURCE, **ACSA_REFERRAL},
    {"name": "DECA Global LLC", "city": "Memphis", "state": "TN", "type": "merchant", "notes": "ACSA merchant; contact via ACSA", **ACSA_SOURCE, **ACSA_REFERRAL},
    {"name": "ECOM USA LLC", "city": "Memphis", "state": "TN", "type": "merchant", "notes": "ACSA merchant; contact via ACSA", **ACSA_SOURCE, **ACSA_REFERRAL},
    {"name": "ED & F Man Cotton LLC", "city": "Memphis", "state": "TN", "type": "merchant", "notes": "ACSA merchant; contact via ACSA", **ACSA_SOURCE, **ACSA_REFERRAL},
    {"name": "Farmcot", "city": "New York", "state": "NY", "url": "https://www.farmcotinc.com/", "website": "https://www.farmcotinc.com/", "buy_link": "https://www.farmcotinc.com/contact", "phone": "", "email": "", "type": "merchant", "notes": "US cotton; sources from American farmers; contact form on website", "source": "web", "source_url": "https://www.farmcotinc.com/"},
    {"name": "Goetz & Sons Inc", "city": "Memphis", "state": "TN", "type": "merchant", "notes": "ACSA merchant; contact via ACSA", **ACSA_SOURCE, **ACSA_REFERRAL},
    {"name": "Hang Tung Resources (USA) Co Ltd", "city": "Memphis", "state": "TN", "type": "merchant", "notes": "ACSA merchant; contact via ACSA", **ACSA_SOURCE, **ACSA_REFERRAL},
    {"name": "Jess Smith & Sons Cotton Inc", "city": "Bakersfield", "state": "CA", "type": "merchant", "notes": "ACSA; WCSA; California cotton; contact via ACSA", **ACSA_SOURCE, **ACSA_REFERRAL},
    {"name": "Louis Dreyfus Company", "city": "Memphis", "state": "TN", "url": "https://www.ldc.com/us/en/who-we-are/business-lines/cotton/", "website": "https://www.ldc.com/", "buy_link": "https://www.ldc.com/us/en/our-facilities/west-memphis-ar/contact-us-west-memphis-ar/", "phone": "901-383-5000", "email": "datateam@ldc.com", "type": "merchant", "notes": "ACSA merchant; global commodities; Cordova TN office", **ACSA_SOURCE},
    {"name": "Lyons Cotton Inc", "city": "Memphis", "state": "TN", "type": "merchant", "notes": "ACSA merchant; contact via ACSA", **ACSA_SOURCE, **ACSA_REFERRAL},
    {"name": "MemTex Cotton Marketing LLC", "city": "Memphis", "state": "TN", "type": "merchant", "notes": "ACSA merchant; contact via ACSA", **ACSA_SOURCE, **ACSA_REFERRAL},
    {"name": "Olam Agri Americas Inc", "city": "Memphis", "state": "TN", "type": "merchant", "notes": "ACSA merchant; contact via ACSA", **ACSA_SOURCE, **ACSA_REFERRAL},
    {"name": "Old Blue Cotton Company Inc", "city": "Bakersfield", "state": "CA", "type": "merchant", "notes": "ACSA; WCSA; California cotton; contact via ACSA", **ACSA_SOURCE, **ACSA_REFERRAL},
    {"name": "Omnicotton Inc", "city": "Memphis", "state": "TN", "type": "merchant", "notes": "ACSA merchant; contact via ACSA", **ACSA_SOURCE, **ACSA_REFERRAL},
    {"name": "Terra Nova Commodities LLC", "city": "Memphis", "state": "TN", "type": "merchant", "notes": "ACSA merchant; contact via ACSA", **ACSA_SOURCE, **ACSA_REFERRAL},
    {"name": "Toyo Cotton Company", "city": "Memphis", "state": "TN", "type": "merchant", "notes": "ACSA merchant; contact via ACSA", **ACSA_SOURCE, **ACSA_REFERRAL},
    {"name": "Toyoshima International America Inc", "city": "Memphis", "state": "TN", "type": "merchant", "notes": "ACSA merchant; contact via ACSA", **ACSA_SOURCE, **ACSA_REFERRAL},
    {"name": "UNIPET Inc", "city": "Memphis", "state": "TN", "type": "merchant", "notes": "ACSA merchant; contact via ACSA", **ACSA_SOURCE, **ACSA_REFERRAL},
    {"name": "Walcot Trading Company LLC", "city": "Memphis", "state": "TN", "type": "merchant", "notes": "ACSA merchant; contact via ACSA", **ACSA_SOURCE, **ACSA_REFERRAL},
    {"name": "White Gold Cotton Marketing LLC", "city": "Memphis", "state": "TN", "type": "merchant", "notes": "ACSA merchant; contact via ACSA", **ACSA_SOURCE, **ACSA_REFERRAL},
    {"name": "W D Felder & Company", "city": "Memphis", "state": "TN", "type": "merchant", "notes": "ACSA merchant; contact via ACSA", **ACSA_SOURCE, **ACSA_REFERRAL},
]

# Primary buyers / mill service agents - buy cotton for mills
BUYABLE_PRIMARY_BUYERS = [
    {"name": "Choice Cotton Company Inc", "city": "Memphis", "state": "TN", "type": "primary_buyer", "notes": "ACSA; mill service; contact via ACSA", **ACSA_SOURCE, **ACSA_REFERRAL},
    {"name": "East Cotton Company", "city": "Memphis", "state": "TN", "type": "primary_buyer", "notes": "ACSA; mill service; contact via ACSA", **ACSA_SOURCE, **ACSA_REFERRAL},
    {"name": "Globalexim LLC", "city": "Memphis", "state": "TN", "type": "primary_buyer", "notes": "ACSA; mill service; contact via ACSA", **ACSA_SOURCE, **ACSA_REFERRAL},
    {"name": "Indigo Ag", "city": "Memphis", "state": "TN", "type": "primary_buyer", "notes": "ACSA; ag tech; contact via ACSA", **ACSA_SOURCE, **ACSA_REFERRAL},
    {"name": "J G Boswell Company", "city": "Corcoran", "state": "CA", "type": "primary_buyer", "notes": "ACSA; WCSA; California grower/processor; contact via ACSA", **ACSA_SOURCE, **ACSA_REFERRAL},
    {"name": "Jabbour Cotton Company LLC", "city": "Memphis", "state": "TN", "type": "primary_buyer", "notes": "ACSA; mill service; contact via ACSA", **ACSA_SOURCE, **ACSA_REFERRAL},
    {"name": "Loeb and Company Inc", "city": "Memphis", "state": "TN", "type": "primary_buyer", "notes": "ACSA; mill service; contact via ACSA", **ACSA_SOURCE, **ACSA_REFERRAL},
    {"name": "McMeekin Cotton LLC", "city": "Memphis", "state": "TN", "type": "primary_buyer", "notes": "ACSA; mill service; contact via ACSA", **ACSA_SOURCE, **ACSA_REFERRAL},
    {"name": "New Hope AgriServices LLC", "city": "Memphis", "state": "TN", "type": "primary_buyer", "notes": "ACSA; mill service; contact via ACSA", **ACSA_SOURCE, **ACSA_REFERRAL},
    {"name": "Nunn Cotton Company Inc", "city": "Memphis", "state": "TN", "type": "primary_buyer", "notes": "ACSA; mill service; contact via ACSA", **ACSA_SOURCE, **ACSA_REFERRAL},
    {"name": "Plainsman Cotton Company", "city": "Memphis", "state": "TN", "type": "primary_buyer", "notes": "ACSA; mill service; contact via ACSA", **ACSA_SOURCE, **ACSA_REFERRAL},
    {"name": "Wildwood Cotton Technologies", "city": "Memphis", "state": "TN", "type": "primary_buyer", "notes": "ACSA; mill service; contact via ACSA", **ACSA_SOURCE, **ACSA_REFERRAL},
]

# Direct-sale brands - buy products; cotton traces to specific farms
# Source: web research
BUYABLE_DIRECT_SALE = [
    {"name": "Bridgeforth Cotton", "city": "Tanner", "state": "AL", "url": "https://www.bridgeforthcotton.net/", "website": "https://www.bridgeforthcotton.net/", "buy_link": "https://www.bridgeforthcotton.net/", "phone": "", "email": "", "type": "direct_sale", "notes": "Bridgeforth Farms; sheets, towels, apparel; Target, Victoria's Secret partner", "source": "web", "source_url": "https://www.bridgeforthcotton.net/"},
    {"name": "Magnolia Loom", "city": "Sandersville", "state": "GA", "url": "https://www.magnolialoom.com/", "website": "https://www.magnolialoom.com/", "buy_link": "https://www.magnolialoom.com/", "phone": "", "email": "", "type": "direct_sale", "notes": "T-shirts; contracts GA growers $1/lb; QR traces to farm; 100% USA; shop online", "prices": "See website", "source": "web", "source_url": "https://www.magnolialoom.com/"},
    {"name": "HomeGrown Cotton", "city": "Memphis", "state": "TN", "url": "https://homegrowncotton.us/", "website": "https://homegrowncotton.us/", "buy_link": "https://homegrowncotton.us/contact-us", "phone": "", "email": "NAsales@himatsingka.com", "type": "direct_sale", "notes": "50 family farms; sheets, towels, denim; SigNature T® verification", "source": "web", "source_url": "https://homegrowncotton.us/"},
    {"name": "Harvest & Mill", "city": "Los Angeles", "state": "CA", "url": "https://harvestandmill.com/", "website": "https://harvestandmill.com/", "buy_link": "https://harvestandmill.com/", "phone": "", "email": "hello@harvestandmill.com", "type": "direct_sale", "notes": "Organic cotton; grown & sewn USA; farm traceability", "source": "web", "source_url": "https://harvestandmill.com/"},
    {"name": "grown&sewn", "city": "New York", "state": "NY", "url": "https://www.grownandsewn.com/", "website": "https://www.grownandsewn.com/", "buy_link": "https://www.grownandsewn.com/", "phone": "917-686-2964", "email": "info@grownandsewn.com", "type": "direct_sale", "notes": "Made in USA cotton; traceable supply chain", "source": "web", "source_url": "https://www.grownandsewn.com/"},
    {"name": "Imogene + Willie (The Cotton Project)", "city": "Nashville", "state": "TN", "url": "https://www.imogeneandwillie.com/", "website": "https://www.imogeneandwillie.com/", "buy_link": "https://imogeneandwillie.com/pages/contact", "phone": "615-292-5005", "email": "", "type": "direct_sale", "notes": "Traceable t-shirt; Larkin Martin AL + Hill Spinning NC; ~400 mi supply chain", "source": "web", "source_url": "https://www.imogeneandwillie.com/"},
]

# ICE Cotton No. 2 licensed warehouses - 5 delivery points
# Source: ice.com/publicdocs/futures_us_reports/cotton/Cotton No. 2 Warehouse.pdf
ICE_SOURCE = {"source": "ICE", "source_url": "https://www.ice.com/publicdocs/futures_us_reports/cotton/Cotton%20No.%202%20Warehouse.pdf"}
BUYABLE_ICE_WAREHOUSES = [
    {"name": "Crittenden Gin Company", "city": "Crawfordsville", "state": "AR", "type": "ice_warehouse", "capacity": 75500, "delivery_point": "Memphis", "phone": "870-739-3228", "notes": "ICE licensed", **ICE_SOURCE},
    {"name": "Union Compress Warehouse of West Memphis", "city": "West Memphis", "state": "AR", "type": "ice_warehouse", "capacity": 115080, "delivery_point": "Memphis", "phone": "870-732-6566", "notes": "ICE licensed", **ICE_SOURCE},
    {"name": "Riverbend Distribution Center LLC", "city": "West Memphis", "state": "AR", "type": "ice_warehouse", "capacity": 130000, "delivery_point": "Memphis", "phone": "901-383-5137", "notes": "LDC Cotton Storage; ICE licensed", **ICE_SOURCE},
    {"name": "Anderson Clayton Desoto (Olam Cotton)", "city": "Olive Branch", "state": "MS", "type": "ice_warehouse", "capacity": 250000, "delivery_point": "Memphis", "phone": "214-537-4222", "notes": "ICE licensed", **ICE_SOURCE},
    {"name": "Viterra USA Agriculture LLC", "city": "Memphis", "state": "TN", "type": "ice_warehouse", "capacity": 131480, "delivery_point": "Memphis", "phone": "646-949-2035", "notes": "Multiple Memphis facilities; ICE licensed", **ICE_SOURCE},
    {"name": "Cotton Trade Warehouse (Cargill)", "city": "Memphis", "state": "TN", "type": "ice_warehouse", "capacity": 125000, "delivery_point": "Memphis", "notes": "ICE licensed", **ICE_SOURCE},
    {"name": "Cargill Cotton Warehouse", "city": "Memphis", "state": "TN", "type": "ice_warehouse", "capacity": 90000, "delivery_point": "Memphis", "notes": "ICE licensed", **ICE_SOURCE},
    {"name": "Memphis Compress Company", "city": "Memphis", "state": "TN", "type": "ice_warehouse", "capacity": 130000, "delivery_point": "Memphis", "phone": "901-383-5137", "notes": "LDC Cotton Storage; ICE licensed", **ICE_SOURCE},
    {"name": "Producer's Warehouse No. 1 (LDC)", "city": "Memphis", "state": "TN", "type": "ice_warehouse", "capacity": 154000, "delivery_point": "Memphis", "phone": "901-383-5137", "notes": "ICE licensed", **ICE_SOURCE},
    {"name": "Producer's Warehouse No. 2 (LDC)", "city": "Memphis", "state": "TN", "type": "ice_warehouse", "capacity": 85000, "delivery_point": "Memphis", "phone": "901-383-5137", "notes": "ICE licensed", **ICE_SOURCE},
    {"name": "Producer's Warehouse No. 3 (LDC)", "city": "Memphis", "state": "TN", "type": "ice_warehouse", "capacity": 24000, "delivery_point": "Memphis", "phone": "901-383-5137", "notes": "ICE licensed", **ICE_SOURCE},
    {"name": "Distribution Center No. 1 (LDC)", "city": "Memphis", "state": "TN", "type": "ice_warehouse", "capacity": 70000, "delivery_point": "Memphis", "phone": "901-383-5137", "notes": "ICE licensed", **ICE_SOURCE},
    {"name": "River City Warehouse (Sunbelt)", "city": "Memphis", "state": "TN", "type": "ice_warehouse", "capacity": 110000, "delivery_point": "Memphis", "phone": "214-520-1717", "notes": "ICE licensed", **ICE_SOURCE},
    {"name": "Total Commodity Warehouse (Sunbelt)", "city": "Memphis", "state": "TN", "type": "ice_warehouse", "capacity": 70000, "delivery_point": "Memphis", "phone": "214-520-1717", "notes": "ICE licensed", **ICE_SOURCE},
    {"name": "Mallory Alexander International Logistics", "city": "Memphis", "state": "TN", "url": "https://www.mallorygroup.com/", "website": "https://www.mallorygroup.com/", "buy_link": "https://www.mallorygroup.com/contact/", "type": "ice_warehouse", "capacity": 21400, "delivery_point": "Memphis", "phone": "901-370-4201", "email": "", "notes": "ICE licensed", **ICE_SOURCE},
    {"name": "International Cotton Depots ICD 4", "city": "Memphis", "state": "TN", "type": "ice_warehouse", "capacity": 49000, "delivery_point": "Memphis", "phone": "855-850-0049", "email": "raydoroff@cofcointernational.com", "notes": "ICE licensed", **ICE_SOURCE},
    {"name": "Moody Compress & Warehouse Houston", "city": "Houston", "state": "TX", "type": "ice_warehouse", "capacity": 98000, "delivery_point": "Houston", "phone": "409-763-6401", "notes": "ICE licensed", **ICE_SOURCE},
    {"name": "Houston Commodity Warehouse (Sunbelt)", "city": "Houston", "state": "TX", "type": "ice_warehouse", "capacity": 145000, "delivery_point": "Houston", "phone": "214-520-1717", "notes": "ICE licensed", **ICE_SOURCE},
    {"name": "Supply Chain Management LLC Houston", "city": "Pasadena", "state": "TX", "type": "ice_warehouse", "capacity": 65000, "delivery_point": "Houston", "phone": "912-966-9999", "notes": "ICE licensed", **ICE_SOURCE},
    {"name": "Moody Compress Galveston", "city": "Galveston", "state": "TX", "type": "ice_warehouse", "capacity": 153500, "delivery_point": "Galveston", "phone": "409-763-6401", "notes": "ICE licensed", **ICE_SOURCE},
    {"name": "Southern Compress Warehouse (LDC)", "city": "Galveston", "state": "TX", "type": "ice_warehouse", "capacity": 75000, "delivery_point": "Galveston", "phone": "901-383-5137", "notes": "ICE licensed", **ICE_SOURCE},
    {"name": "Supply Chain Management Dallas", "city": "Dallas", "state": "TX", "type": "ice_warehouse", "capacity": 116500, "delivery_point": "Dallas-Ft.Worth", "phone": "469-906-0558", "notes": "ICE licensed", **ICE_SOURCE},
    {"name": "Mallory Alexander Dallas", "city": "Dallas", "state": "TX", "type": "ice_warehouse", "capacity": 63000, "delivery_point": "Dallas-Ft.Worth", "phone": "901-370-4201", "notes": "ICE licensed", **ICE_SOURCE},
    {"name": "Anderson Clayton Dallas (Olam Cotton)", "city": "Dallas", "state": "TX", "type": "ice_warehouse", "capacity": 178000, "delivery_point": "Dallas-Ft.Worth", "phone": "214-537-4222", "notes": "ICE licensed", **ICE_SOURCE},
    {"name": "Fort Worth Commodity Warehouse (Sunbelt)", "city": "Fort Worth", "state": "TX", "type": "ice_warehouse", "capacity": 65000, "delivery_point": "Dallas-Ft.Worth", "phone": "214-520-1717", "notes": "ICE licensed", **ICE_SOURCE},
    {"name": "International Cotton Depots Dallas", "city": "Grand Prairie", "state": "TX", "type": "ice_warehouse", "capacity": 32500, "delivery_point": "Dallas-Ft.Worth", "phone": "855-850-0049", "notes": "ICE licensed", **ICE_SOURCE},
    {"name": "Cargill Cotton Warehouse Haslet", "city": "Haslet", "state": "TX", "type": "ice_warehouse", "capacity": 110000, "delivery_point": "Dallas-Ft.Worth", "notes": "ICE licensed", **ICE_SOURCE},
    {"name": "Dallas Warehouse Company LLC", "city": "Grand Prairie", "state": "TX", "type": "ice_warehouse", "capacity": 40000, "delivery_point": "Dallas-Ft.Worth", "phone": "214-528-9800", "notes": "ICE licensed", **ICE_SOURCE},
    {"name": "International Cotton Depots Greenville", "city": "Greenville", "state": "SC", "type": "ice_warehouse", "capacity": 60000, "delivery_point": "Greenville", "phone": "855-850-0049", "notes": "ICE licensed", **ICE_SOURCE},
    {"name": "Staplcotn Greer", "city": "Greer", "state": "SC", "type": "ice_warehouse", "capacity": 55000, "delivery_point": "Greenville", "phone": "662-453-8941", "notes": "ICE licensed", **ICE_SOURCE},
    {"name": "Spartanburg Distribution Center (LDC)", "city": "Spartanburg", "state": "SC", "type": "ice_warehouse", "capacity": 115000, "delivery_point": "Greenville", "phone": "901-383-5137", "notes": "ICE licensed", **ICE_SOURCE},
]

# Cotton warehouses / compresses - CGWA members + major facilities
# Source: cottongwa.org
CGWA_SOURCE = {"source": "CGWA", "source_url": "https://www.cottongwa.org/"}
BUYABLE_WAREHOUSES = [
    {"name": "Calcot", "city": "Bakersfield", "state": "CA", "url": "https://calcot.com/", "website": "https://calcot.com/", "buy_link": "https://calcot.com/sales-contact/", "phone": "661-327-5961", "email": "info@calcot.com", "type": "warehouse", "notes": "CGWA; coop + warehouse; ~400K bales/year", "production": "~400K bales/year", **CGWA_SOURCE},
    {"name": "Cotton Growers Warehouse", "city": "Garner", "state": "NC", "url": "https://www.carolinascotton.com/", "website": "https://www.carolinascotton.com/", "buy_link": "https://www.carolinascotton.com/contact-us", "phone": "919-773-2120", "email": "", "type": "warehouse", "notes": "CGWA; Carolinas Cotton", **CGWA_SOURCE},
    {"name": "Farmer's Cooperative Compress", "city": "Lubbock", "state": "TX", "url": "https://www.farmerscompress.com/", "website": "https://www.farmerscompress.com/", "buy_link": "https://farmerscompress.com/Open/Home/Contact", "phone": "806-763-9431", "email": "shipping@farmerscompress.com", "type": "warehouse", "notes": "CGWA; Texas High Plains", **CGWA_SOURCE},
    {"name": "Franklin Cotton Warehouse Coop", "city": "Winnsboro", "state": "LA", "phone": "318-435-4436", "email": "", "type": "warehouse", "notes": "CGWA", **CGWA_SOURCE},
    {"name": "Gulf Compress", "city": "Corpus Christi", "state": "TX", "url": "https://www.gulfcompress.com/", "website": "https://www.gulfcompress.com/", "buy_link": "https://www.gulfcompress.com/", "phone": "361-882-5489", "email": "cotton@gulfcompress.com", "type": "warehouse", "notes": "CGWA", **CGWA_SOURCE},
    {"name": "Plains Cotton Cooperative Association", "city": "Lubbock", "state": "TX", "url": "https://pcca.com/", "website": "https://pcca.com/", "buy_link": "https://pcca.com/contact-us/", "phone": "806-763-8011", "email": "", "type": "warehouse", "notes": "CGWA; PCCA; largest West TX coop; ~1.5M+ bales/yr", "production": "~1.5M+ bales/yr", **CGWA_SOURCE},
    {"name": "Southeastern Gin and Peanut", "city": "Surrency", "state": "GA", "url": "https://www.southeasterngin.com/", "website": "https://www.southeasterngin.com/", "buy_link": "https://www.southeasterngin.com/", "phone": "912-366-0808", "email": "Roger@SoutheasternGin.com", "type": "warehouse", "notes": "CGWA", **CGWA_SOURCE},
    {"name": "Sowega Cotton Inc", "city": "Climax", "state": "GA", "url": "https://www.sowegacotton.com/", "type": "warehouse", "notes": "CGWA", **CGWA_SOURCE},
    {"name": "Staplcotn", "city": "Greenwood", "state": "MS", "url": "https://www.staplcotn.com/", "type": "warehouse", "notes": "CGWA; coop + warehouse", **CGWA_SOURCE},
    {"name": "Suncot Warehouse", "city": "Denver City", "state": "TX", "url": "https://www.suncotwarehouse.com/", "website": "https://www.suncotwarehouse.com/", "buy_link": "https://www.suncotwarehouse.com/contact", "phone": "806-592-8448", "email": "suncotacctwhs@gmail.com", "type": "warehouse", "notes": "CGWA", **CGWA_SOURCE},
    {"name": "Texas Cotton Growers Cooperative Association", "city": "Taylor", "state": "TX", "type": "warehouse", "notes": "CGWA", **CGWA_SOURCE},
    {"name": "United Agricultural Cooperative", "city": "El Campo", "state": "TX", "url": "https://news.unitedag.net/", "type": "warehouse", "notes": "CGWA", **CGWA_SOURCE},
    {"name": "Willacy Cotton Warehouse LLC", "city": "Raymondville", "state": "TX", "type": "warehouse", "notes": "CGWA", **CGWA_SOURCE},
    {"name": "Sunbelt Warehouse Corporation", "city": "Memphis", "state": "TN", "type": "warehouse", "notes": "ACSA associate; ICE licensed", "source": "ACSA", "source_url": "https://acsa-cotton.org/"},
    {"name": "Federal Compress & Warehouse Company", "city": "Memphis", "state": "TN", "type": "warehouse", "notes": "ICE licensed; since 1887", **ICE_SOURCE},
]

# US cotton yarn/fabric mills - buy cotton fiber; sell yarn/fabric
# Source: CottonWorks, Cotton Inc EFS Fiber/Yarn Sourcing Directory
EFS_SOURCE = {"source": "CottonWorks/EFS", "source_url": "https://cottonworks.com/sourcing/find-us-suppliers/"}
BUYABLE_MILLS = [
    {"name": "Shuford Yarns LLC", "city": "Hickory", "state": "NC", "url": "https://www.shufordyarns.com/", "website": "https://www.shufordyarns.com/", "buy_link": "https://www.shufordyarns.com/contact-us/", "phone": "828-324-4265", "email": "info@shufordyarns.com", "type": "mill", "notes": "Cotton & synthetic yarns; EFS licensee", **EFS_SOURCE},
    {"name": "Parkdale Mills", "city": "Gastonia", "state": "NC", "url": "https://www.parkdalemills.com/", "website": "https://www.parkdalemills.com/", "buy_link": "https://www.parkdalemills.com/contact/", "phone": "800-331-1843", "email": "sales@parkdalemills.com", "type": "mill", "notes": "World's leading spun yarn manufacturer; EFS licensee", **EFS_SOURCE},
    {"name": "Buhler Quality Yarns Corp", "city": "Jefferson", "state": "GA", "url": "https://www.buhleryarns.com/", "website": "https://www.buhleryarns.com/", "buy_link": "https://www.buhleryarns.com/", "phone": "706-367-9834", "email": "", "type": "mill", "notes": "Supima cotton combed ring spun; EFS licensee", **EFS_SOURCE},
    {"name": "Gildan", "city": "Sanford", "state": "NC", "url": "https://www.gildancorp.com/", "website": "https://www.gildancorp.com/", "buy_link": "https://gildancorp.com/en/other/contact/", "phone": "877-445-3265", "email": "", "type": "mill", "notes": "Apparel; EFS licensee; USA Printwear sales", **EFS_SOURCE},
    {"name": "Cone Denim LLC", "city": "Greensboro", "state": "NC", "url": "https://conedenim.com/", "website": "https://conedenim.com/", "buy_link": "https://conedenim.com/contact/", "phone": "336-379-6165", "email": "", "type": "mill", "notes": "Largest denim producer; EFS licensee", **EFS_SOURCE},
    {"name": "Inman Mills", "city": "Inman", "state": "SC", "url": "https://www.inmanmills.com/", "website": "https://www.inmanmills.com/", "buy_link": "https://www.inmanmills.com/contact/", "phone": "864-472-2121", "email": "", "type": "mill", "notes": "Cotton fabrics; EFS licensee", **EFS_SOURCE},
    {"name": "Milliken & Company", "city": "Spartanburg", "state": "SC", "url": "https://www.milliken.com/", "website": "https://www.milliken.com/", "buy_link": "https://www.milliken.com/en-us/textiles/contact-us", "phone": "864-503-2020", "email": "", "type": "mill", "notes": "Textiles; EFS licensee", **EFS_SOURCE},
    {"name": "Hill Spinning", "city": "Thomasville", "state": "NC", "url": "https://hillspinning.com/", "website": "https://hillspinning.com/", "buy_link": "https://hillspinning.com/", "phone": "336-472-7908", "email": "", "type": "mill", "notes": "Combed & carded ring-spun; organic cotton; AMS EAATM participant", **EFS_SOURCE},
    {"name": "Patrick Yarn Mills", "city": "Kings Mountain", "state": "NC", "url": "https://patrickyarns.com/", "website": "https://patrickyarns.com/", "buy_link": "https://patrickyarns.com/", "phone": "704-739-4119", "email": "", "type": "mill", "notes": "Cotton, synthetic, specialty yarns; closing Dec 2025 (Coats Group)", **EFS_SOURCE},
    {"name": "Cap Yarns", "city": "Clover", "state": "SC", "url": "https://www.capyarns.com/", "website": "https://www.capyarns.com/", "buy_link": "https://www.capyarns.com/", "phone": "803-222-8856", "email": "", "type": "mill", "notes": "Novelty heather, cationic cotton; AMS EAATM participant", **EFS_SOURCE},
    {"name": "Frontier Yarns", "city": "Sanford", "state": "NC", "url": "https://www.frontieryarns.com/", "website": "https://www.frontieryarns.com/", "buy_link": "https://www.gildancorp.com/en/other/contact/", "phone": "919-776-9940", "email": "", "type": "mill", "notes": "Open-end and air-jet spun; Gildan subsidiary; AMS EAATM participant", **EFS_SOURCE},
    {"name": "Keer America", "city": "Indian Land", "state": "SC", "url": "https://keeramerica.com/", "website": "https://keeramerica.com/", "buy_link": "https://keeramerica.com/", "phone": "803-835-1110", "email": "info@keeramerica.com", "type": "mill", "notes": "Open-end spun; AMS EAATM participant", **EFS_SOURCE},
]

# CottonWorks U.S. Supplier List - spinners & weavers (cotton fiber buyers)
# Source: cottonworks.com/sourcing/find-us-suppliers/ (PDF)
# Deduplicated against BUYABLE_MILLS
COTTONWORKS_SOURCE = {"source": "CottonWorks", "source_url": "https://cottonworks.com/sourcing/find-us-suppliers/"}
BUYABLE_US_SUPPLIERS = [
    {"name": "SpunLab", "city": "Gastonia", "state": "NC", "url": "https://spunlab.com/", "website": "https://spunlab.com/", "buy_link": "https://spunlab.com/", "phone": "800-374-6754", "email": "", "type": "us_supplier", "notes": "Parkdale division; CottonWorks spinner", **COTTONWORKS_SOURCE},
    {"name": "Cotswold Industries / Central Textiles", "city": "Central", "state": "SC", "url": "https://ctextiles.com/", "website": "https://ctextiles.com/", "buy_link": "https://ctextiles.com/", "phone": "864-639-2491", "email": "inquiry@ctextiles.com", "type": "us_supplier", "notes": "Spinner/weaver; CottonWorks; Cotswold NY 212-689-3432", **COTTONWORKS_SOURCE},
    {"name": "Greenwood Mills", "city": "Greenwood", "state": "SC", "url": "https://greenwoodmills.com/", "website": "https://greenwoodmills.com/", "buy_link": "https://greenwoodmills.com/", "phone": "864-229-2571", "email": "", "type": "us_supplier", "notes": "Armed Forces uniforms, industrial; CottonWorks", **COTTONWORKS_SOURCE},
    {"name": "1888 Mills", "city": "Griffin", "state": "GA", "url": "https://1888mills.com/", "website": "https://1888mills.com/", "buy_link": "https://1888mills.com/", "phone": "770-229-2361", "email": "b2bsitesupport@1888mills.com", "type": "us_supplier", "notes": "Terry/toweling, sheeting; CottonWorks weaver", **COTTONWORKS_SOURCE},
    {"name": "American Merchant", "city": "Bristol", "state": "VA", "url": "https://americanmerchantusa.com/", "website": "https://americanmerchantusa.com/", "buy_link": "https://americanmerchantusa.com/contact/", "phone": "", "email": "", "type": "us_supplier", "notes": "Home, Terry; CottonWorks weaver", **COTTONWORKS_SOURCE},
    {"name": "DNA Technical Fabrics", "city": "Columbus", "state": "GA", "url": "https://dnatechfab.com/", "website": "https://dnatechfab.com/", "buy_link": "https://www.dnatechfab.com/", "phone": "706-565-3344", "email": "", "type": "us_supplier", "notes": "Technical and industrial; CottonWorks weaver", **COTTONWORKS_SOURCE},
    {"name": "Family Heir-Loom Weavers", "city": "Red Lion", "state": "PA", "url": "https://familyheirloomweavers.com/", "website": "https://familyheirloomweavers.com/", "buy_link": "https://www.familyheirloomweavers.com/contact", "phone": "717-246-2431", "email": "info@familyheirloomweavers.com", "type": "us_supplier", "notes": "Home; CottonWorks weaver", **COTTONWORKS_SOURCE},
    {"name": "Fancy Terry", "city": "Inman", "state": "SC", "url": "https://fancyterry.com/", "website": "https://fancyterry.com/", "buy_link": "https://fancyterry.com/contact/", "phone": "864-472-7965", "email": "cindy@fancyterryinc.com", "type": "us_supplier", "notes": "Home, Jacquard, Terry; CottonWorks weaver", **COTTONWORKS_SOURCE},
    {"name": "Hamrick Mills", "city": "Gaffney", "state": "SC", "url": "https://hamrickmills.com/", "website": "https://hamrickmills.com/", "buy_link": "https://hamrickmills.com/contact/", "phone": "800-297-6306", "email": "JHopkins@HamrickMills.com", "type": "us_supplier", "notes": "Apparel, home, industrial; CottonWorks weaver; sales 864-487-6283", **COTTONWORKS_SOURCE},
    {"name": "HomeTex Incorporated", "city": "Cullman", "state": "AL", "url": "https://homtex.com/", "website": "https://homtex.com/", "buy_link": "https://www.homtex.com/contact-us.php", "phone": "256-734-3937", "email": "info@homtex.com", "type": "us_supplier", "notes": "Home, PPE; CottonWorks weaver", **COTTONWORKS_SOURCE},
    {"name": "Huston Textiles Co.", "city": "Mather", "state": "CA", "url": "https://hustontextile.com/", "website": "https://hustontextile.com/", "buy_link": "https://hustontextile.com/contact/", "phone": "916-546-5001", "email": "support@hustontextile.com", "type": "us_supplier", "notes": "Apparel, Denim; CottonWorks weaver", **COTTONWORKS_SOURCE},
    {"name": "J.B. Martin Company", "city": "Leesville", "state": "SC", "url": "https://jbmartin.com/", "website": "https://jbmartin.com/", "buy_link": "https://jbmartin.com/about/locations-distribution/", "phone": "803-532-6277", "email": "", "type": "us_supplier", "notes": "Apparel, Home, Terry, Velvet; CottonWorks weaver", **COTTONWORKS_SOURCE},
    {"name": "La France Industries", "city": "La France", "state": "SC", "url": "https://lafranceindustries.com/", "website": "https://lafrancefabrics.com/", "buy_link": "https://lafrancefabrics.com/contact-us/", "phone": "864-646-4115", "email": "", "type": "us_supplier", "notes": "Industrial, Automotive; CottonWorks weaver", **COTTONWORKS_SOURCE},
    {"name": "Loom Craft Inc.", "city": "Belton", "state": "SC", "url": "https://loomcraftinc.com/", "website": "https://loomcraftinc.com/", "buy_link": "https://www.loomcraftinc.com/contact/", "phone": "864-839-3974", "email": "info@weavetec.com", "type": "us_supplier", "notes": "Home, Jacquard, Terry; CottonWorks weaver; Weavetec product line", **COTTONWORKS_SOURCE},
    {"name": "Mount Vernon Mills", "city": "Mauldin", "state": "SC", "url": "https://mvmills.com/", "website": "https://mvmills.com/", "buy_link": "https://www.mvmills.com/contact-us/", "phone": "864-688-7100", "email": "", "type": "us_supplier", "notes": "Apparel, Denim, Industrial; CottonWorks weaver", **COTTONWORKS_SOURCE},
    {"name": "Sattler Corp", "city": "Hudson", "state": "NC", "url": "https://usa.sattler.com/", "website": "https://usa.sattler.com/", "buy_link": "https://usa.sattler.com/home", "phone": "828-759-2105", "email": "", "type": "us_supplier", "notes": "Home (Outdoor), Marine, Jacquard; CottonWorks weaver; Outdura brand", **COTTONWORKS_SOURCE},
    {"name": "SSM Industries", "city": "Spring City", "state": "TN", "url": "https://ssmind.com/", "website": "https://ssmind.com/", "buy_link": "https://ssmind.com/", "phone": "423-365-4048", "email": "", "type": "us_supplier", "notes": "Apparel, Uniforms; CottonWorks weaver", **COTTONWORKS_SOURCE},
    {"name": "Swavelle Mill Creek", "city": "New York", "state": "NY", "url": "https://swavelle.com/", "website": "https://swavelle.com/", "buy_link": "https://www.swavelle.com/contact-us/", "phone": "800-544-0478", "email": "customerservice@swavelle.com", "type": "us_supplier", "notes": "Home, Terry, Velvet; CottonWorks weaver", **COTTONWORKS_SOURCE},
    {"name": "Valdese Weavers, LLC", "city": "Valdese", "state": "NC", "url": "https://valdeseweavers.com/", "website": "https://valdeseweavers.com/", "buy_link": "https://www.valdeseweavers.com/contact-us/", "phone": "828-874-2181", "email": "info@valdeseweavers.com", "type": "us_supplier", "notes": "Home, Jacquard, Healthcare; CottonWorks weaver", **COTTONWORKS_SOURCE},
    {"name": "Weavetec, Inc.", "city": "Blacksburg", "state": "SC", "url": "https://weavetec.com/", "website": "https://weavetec.com/", "buy_link": "https://www.weavetec.com/contact-us/", "phone": "864-839-3974", "email": "info@weavetec.com", "type": "us_supplier", "notes": "Home, Jacquard, Specialty, Industrial; CottonWorks weaver", **COTTONWORKS_SOURCE},
]

# Organic cotton mills & fabric suppliers - buy cotton fiber; sell organic fabric
# Source: web research
BUYABLE_ORGANIC_MILLS = [
    {"name": "Tuscarora Mills", "city": "Bedford", "state": "PA", "url": "https://tuscaroramills.com/", "website": "https://tuscaroramills.com/", "buy_link": "https://tuscaroramills.com/contact-us/", "phone": "814-285-8594", "email": "tuscamills@gmail.com", "type": "mill", "notes": "USDA organic cotton fabrics; basketweave, dimity, twill, selvedge denim; established 2020", "source": "web", "source_url": "https://tuscaroramills.com/"},
    {"name": "Spiritex", "city": "Asheville", "state": "NC", "url": "https://fabric.spiritex.net/", "website": "https://fabric.spiritex.net/", "buy_link": "https://wholesale.spiritex.net/", "phone": "", "email": "sales@spiritex.net", "type": "mill", "notes": "100% USA-grown organic cotton; spun, knit, finished domestically; interlock, fleece, jersey, French terry", "source": "web", "source_url": "https://fabric.spiritex.net/"},
    {"name": "Koshtex", "city": "Los Angeles", "state": "CA", "url": "https://www.koshtex.com/", "website": "https://www.koshtex.com/", "buy_link": "https://www.koshtex.com/", "phone": "", "email": "koshtexinc@gmail.com", "type": "mill", "notes": "Cotton jersey knit milled in USA; wholesale fabric", "source": "web", "source_url": "https://www.koshtex.com/"},
]

# Additional warehouses from ACSA affiliates & web research
BUYABLE_ADDITIONAL_WAREHOUSES = [
    {"name": "Paxton Bonded Storages", "city": "Wilson", "state": "NC", "url": "https://www.paxtonbondedstorages.com/", "phone": "252-243-4454", "type": "warehouse", "notes": "ACSA affiliate; 400K sq ft; rail-hub; general storage", "source": "ACSA", "source_url": "https://acsa-cotton.org/affiliates/"},
    {"name": "Plaza Cotton Storage", "city": "Centre", "state": "AL", "phone": "256-927-7828", "type": "warehouse", "notes": "Wholesale fabric; cotton storage; cotton-producing region", "source": "web", "source_url": ""},
    {"name": "Broad Street Bonded Warehouse", "city": "Gastonia", "state": "NC", "url": "https://www.bondedstorage.com/", "website": "https://www.bondedstorage.com/", "buy_link": "https://bondedstorage.com/contactus.html", "phone": "704-867-7253", "email": "info@bondedstorage.com", "type": "warehouse", "notes": "Cotton storage and handling; Gastonia textile region", "source": "web", "source_url": "https://www.bondedstorage.com/"},
]

# Associations / platforms for sourcing
BUYABLE_ASSOCIATIONS = [
    {"name": "American Cotton Shippers Association (ACSA)", "city": "Memphis", "state": "TN", "url": "https://acsa-cotton.org/", "website": "https://acsa-cotton.org/", "buy_link": "https://acsa-cotton.org/our-members/", "phone": "901-525-2272", "email": "", "type": "association", "notes": "80%+ US cotton; merchant/broker federation; contact for member directory", "prices": "Contact members for quotes", "source": "ACSA", "source_url": "https://acsa-cotton.org/"},
    {"name": "Supima", "city": "Phoenix", "state": "AZ", "url": "https://supima.com/", "website": "https://supima.com/", "buy_link": "https://supima.com/", "phone": "602-792-6002", "email": "info@supima.com", "type": "association", "notes": "American Pima cotton; licensing; 500+ licensed manufacturers", "source": "Supima", "source_url": "https://supima.com/"},
    {"name": "The Seam", "city": "Memphis", "state": "TN", "url": "https://www.theseam.com/", "website": "https://www.theseam.com/", "buy_link": "https://ww2.theseam.com/contact-us/", "phone": "877-280-3413", "email": "info@theseam.com", "type": "platform", "notes": "Direct grower-to-buyer marketplace; cash marketing, forward contracts, pool participation; ACSA associate", "source": "The Seam", "source_url": "https://www.theseam.com/"},
    {"name": "Trust Protocol", "city": "", "state": "", "url": "https://trustuscotton.org/", "website": "https://trustuscotton.org/", "buy_link": "https://trustuscotton.org/", "phone": "", "email": "info@trustuscotton.org", "type": "association", "notes": "1,512 growers enrolled; sustainability verification; member portal; no public list", "source": "Trust Protocol", "source_url": "https://trustuscotton.org/"},
    {"name": "COTTON USA Supplier Directory", "city": "", "state": "", "url": "https://www.cottonusa.org/suppliers", "type": "association", "notes": "Searchable directory by location and licensee type; filter by US for domestic suppliers", "source": "COTTON USA", "source_url": "https://www.cottonusa.org/suppliers"},
    {"name": "Cotton Warehouse Association of America (CWAA)", "city": "", "state": "", "url": "https://www.cottonwarehouse.org/", "website": "https://www.cottonwarehouse.org/", "buy_link": "https://www.cottonwarehouse.org/", "phone": "806-577-7193", "email": "", "type": "association", "notes": "Warehouse members; no public list; contact for member directory", "source": "CWAA", "source_url": "https://www.cottonwarehouse.org/"},
    {"name": "The Cotton Board", "city": "Memphis", "state": "TN", "url": "https://www.cottonboard.org/", "website": "https://www.cottonboard.org/", "buy_link": "https://www.cottonboard.org/contact-us", "phone": "901-683-2500", "email": "", "type": "association", "notes": "Cotton Research & Promotion; importer stakeholders; brands, retailers, mills; importers contact cottonboard.org/importers", "source": "Cotton Board", "source_url": "https://www.cottonboard.org/importers"},
]

# USA cut & sew garment manufacturers - make garments from USA cotton
# Sources: Cotton Incorporated cut-and-sew, CottonWorks U.S. Supplier List, CFDA Production Directory,
# Textile Connect (textileconnect.com), ManufacturedNC, NCTO members, Makers Row, web research
COTTONINC_SOURCE = {"source": "Cotton Incorporated", "source_url": "https://www.cottoninc.com/quality-products/textile-sourcing/cut-and-sew/"}
COTTONWORKS_CUTSEW_SOURCE = {"source": "CottonWorks", "source_url": "https://cottonworks.com/sourcing/find-us-suppliers/"}
BUYABLE_CUT_AND_SEW = [
    # Cotton Incorporated + CottonWorks cut & sew list
    {"name": "Stitch K", "city": "Los Angeles", "state": "CA", "url": "https://www.stitchk.com/", "website": "https://www.stitchk.com/", "buy_link": "https://www.stitchk.com/", "phone": "323-325-7568", "email": "", "type": "cut_and_sew", "notes": "Knits, Apparel; Cotton Inc cut & sew", **COTTONINC_SOURCE},
    {"name": "First Avenue Manufacturing", "city": "Thomson", "state": "GA", "url": "https://www.usa-linens.com/", "website": "https://www.usa-linens.com/", "buy_link": "https://www.usa-linens.com/", "phone": "678-392-1432", "email": "", "type": "cut_and_sew", "notes": "Home, Hospital; bed linens, custom sizes; Cotton Inc cut & sew", **COTTONINC_SOURCE},
    {"name": "Topps Safety Apparel Inc", "city": "Rochester", "state": "IN", "url": "https://www.toppssafetyapparel.com/", "website": "https://www.toppssafetyapparel.com/", "buy_link": "https://www.toppssafetyapparel.com/", "phone": "574-223-4311", "email": "", "type": "cut_and_sew", "notes": "Wovens, Denim, Apparel, Uniforms; Cotton Inc cut & sew", **COTTONINC_SOURCE},
    {"name": "JOMEL Seams Reasonable", "city": "Hillside", "state": "NJ", "url": "https://jomel.net/", "website": "https://jomel.net/", "buy_link": "https://jomel.net/", "phone": "973-282-0300", "email": "", "type": "cut_and_sew", "notes": "Apparel, Home, PPE, Uniforms, Military, Hospital; KY & NJ facilities; Cotton Inc cut & sew", **COTTONINC_SOURCE},
    {"name": "Fire-Dex", "city": "Medina", "state": "OH", "url": "https://www.firedex.com/", "website": "https://www.firedex.com/", "buy_link": "https://www.firedex.com/", "phone": "330-723-0000", "email": "", "type": "cut_and_sew", "notes": "Wovens, Denim, CMT, Apparel, Uniforms; fire/rescue gear; Cotton Inc cut & sew", **COTTONINC_SOURCE},
    {"name": "Excel Manufacturing", "city": "El Paso", "state": "TX", "url": "https://www.excelmfg.net/", "website": "https://www.excelmfg.net/", "buy_link": "https://www.excelmfg.net/", "phone": "915-544-0126", "email": "", "type": "cut_and_sew", "notes": "Wovens, Denim, Apparel, Uniforms; dyehouse, washhouse; Cotton Inc cut & sew", **COTTONINC_SOURCE},
    {"name": "Sarah Lynn Sportswear Inc", "city": "Allentown", "state": "PA", "url": "https://www.slsportswear.com/", "website": "https://www.slsportswear.com/", "buy_link": "https://www.slsportswear.com/", "phone": "610-770-1702", "email": "", "type": "cut_and_sew", "notes": "Knits, CMT, Apparel, Uniforms; Cotton Inc cut & sew", **COTTONINC_SOURCE},
    {"name": "Monalisa Manufacturing", "city": "Allentown", "state": "PA", "url": "https://www.monalisamfg.com/", "website": "https://www.monalisamfg.com/", "buy_link": "https://www.monalisamfg.com/", "phone": "610-770-0806", "email": "", "type": "cut_and_sew", "notes": "Knits, Wovens, Apparel; Cotton Inc cut & sew", **COTTONINC_SOURCE},
    {"name": "Lebanon Apparel Corporation (LA CORP)", "city": "Lebanon", "state": "VA", "url": "https://www.lacorpusa.com/", "website": "https://www.lacorpusa.com/", "buy_link": "https://www.lacorpusa.com/", "phone": "276-889-3656", "email": "", "type": "cut_and_sew", "notes": "Knits, Wovens, Denim, Apparel, Home, Uniforms; Cotton Inc cut & sew", **COTTONINC_SOURCE},
    {"name": "Topwin Corporation (Global Point GPI)", "city": "Torrance", "state": "CA", "url": "https://topwin.com/", "website": "https://topwin.com/", "buy_link": "https://topwin.com/", "phone": "310-325-2255", "email": "", "type": "cut_and_sew", "notes": "Knits, Wovens, CMT; Cotton Inc cut & sew", **COTTONINC_SOURCE},
    # Additional USA cotton garment makers from web research
    {"name": "American Giant", "city": "San Francisco", "state": "CA", "url": "https://www.american-giant.com/", "website": "https://www.american-giant.com/", "buy_link": "https://www.american-giant.com/collections/cotton", "phone": "415-529-2429", "email": "service@american-giant.com", "type": "cut_and_sew", "notes": "USA cotton hoodies, tees, activewear; cotton grown near NC facility; DTC brand", "prices": "See website", "source": "web", "source_url": "https://www.american-giant.com/pages/usa-cotton"},
    {"name": "US Blanks", "city": "Gardena", "state": "CA", "url": "https://usblanks.net/", "website": "https://usblanks.net/", "buy_link": "https://usblanks.net/pages/wholesale-application", "phone": "310-225-6774", "email": "info@usblanks.com", "type": "cut_and_sew", "notes": "100% USA-made; fabric at partner mill + in-house cut/sew; cotton & blends; wholesale; FL 321-253-3626", "prices": "Wholesale; apply for account", "source": "web", "source_url": "https://usblanks.net/"},
    {"name": "Cut and Sew Co", "city": "Santa Ana", "state": "CA", "url": "https://cutandsewco.com/", "website": "https://cutandsewco.com/", "buy_link": "https://cutandsewco.com/our-services/", "phone": "714-981-7244", "email": "info@cutandsewco.com", "type": "cut_and_sew", "notes": "Design, fabric sourcing, cut/sew, QC; startups to multinationals; can source USA cotton", "source": "web", "source_url": "https://cutandsewco.com/"},
    {"name": "Seam Apparel", "city": "Charlotte", "state": "NC", "url": "https://seamapparel.com/", "website": "https://seamapparel.com/", "buy_link": "https://seamapparel.com/contact-us/", "phone": "323-925-2859", "email": "sales@seamapparel.com", "type": "cut_and_sew", "notes": "Cut & sew; small-batch to scale; pattern, sample, production; Charlotte & LA", "source": "web", "source_url": "https://seamapparel.com/"},
    {"name": "Apparel USA Inc", "city": "Fairmont", "state": "NC", "url": "https://apparelusa.co/", "website": "https://apparelusa.co/", "buy_link": "https://apparelusa.co/", "phone": "", "email": "", "type": "cut_and_sew", "notes": "Men's dress/sport shirts; cotton oxford, twill, poplin, flannel; pattern, embroidery, wash; 3-wk turnaround", "source": "web", "source_url": "https://apparelusa.co/"},
    # Additional USA cotton garment makers
    {"name": "Spiritex", "city": "Asheville", "state": "NC", "url": "https://wholesale.spiritex.net/", "website": "https://wholesale.spiritex.net/", "buy_link": "https://wholesale.spiritex.net/", "phone": "", "email": "sales@spiritex.net", "type": "cut_and_sew", "notes": "Organic cotton wholesale apparel; TX-grown, Carolinas spun/knit/finished; men's, women's, kids; printing; low MOQ", "prices": "Wholesale; see website", "source": "web", "source_url": "https://wholesale.spiritex.net/"},
    {"name": "California Textile Group", "city": "Los Angeles", "state": "CA", "url": "https://californiatextilegroup.com/", "website": "https://californiatextilegroup.com/", "buy_link": "https://californiatextilegroup.com/pages/contact-us", "phone": "213-765-0555", "email": "aimee@californiagroupinc.com", "type": "cut_and_sew", "notes": "Woman-owned; 30+ yrs; circular knits, cut-and-sew; fabric to finished; gov/military compliance", "source": "web", "source_url": "https://californiatextilegroup.com/"},
    {"name": "Goodwear USA", "city": "Essex", "state": "MA", "url": "https://www.goodwear.com/", "website": "https://www.goodwear.com/", "buy_link": "https://www.goodwear.com/pages/wholesale-inquiries", "phone": "800-338-8895", "email": "sales@goodwear.com", "type": "cut_and_sew", "notes": "38+ yrs; 100% USA cotton field-to-garment; third-party verified; private label, full package", "prices": "Wholesale; resale ID required", "source": "web", "source_url": "https://www.goodwear.com/"},
    {"name": "All USA Clothing", "city": "Keego Harbor", "state": "MI", "url": "https://allusaclothing.com/", "website": "https://allusaclothing.com/", "buy_link": "https://allusaclothing.com/wholesale-account.html", "phone": "877-549-8721", "email": "info@allusaclothing.com", "type": "cut_and_sew", "notes": "Wholesale USA-made brands (American Apparel, Carhartt); customization, private label", "prices": "Wholesale; apply for account", "source": "web", "source_url": "https://allusaclothing.com/"},
    {"name": "Prime Blanks", "city": "California", "state": "CA", "url": "https://primeblanks.com/", "website": "https://primeblanks.com/", "buy_link": "https://primeblanks.com/get-quote", "phone": "", "email": "usamade@primeblanks.com", "type": "cut_and_sew", "notes": "USA-made custom & bulk blank t-shirts; cotton, hemp, recycled; CA facility; fast turnaround", "source": "web", "source_url": "https://primeblanks.com/"},
    {"name": "Volunteer Knit Apparel Inc", "city": "New Tazewell", "state": "TN", "url": "https://www.volunteer-knitwear.com/", "website": "https://www.volunteer-knitwear.com/", "buy_link": "https://www.volunteer-knitwear.com/", "phone": "423-626-7886", "email": "nora@volknit.com", "type": "cut_and_sew", "notes": "Family-owned since 1986; knit, bleach, cut, sew, pack; retail, private label, US Military", **COTTONWORKS_CUTSEW_SOURCE},
    # JOMEL KY facility (corporate in NJ)
    {"name": "JOMEL Seams Reasonable (Burkesville)", "city": "Burkesville", "state": "KY", "url": "https://jomel.net/", "website": "https://jomel.net/", "buy_link": "https://jomel.net/", "phone": "270-864-3898", "email": "", "type": "cut_and_sew", "notes": "Apparel, Home, PPE, Uniforms, Military; Cotton Inc cut & sew", **COTTONINC_SOURCE},
    # Georgia
    {"name": "Rally Apparel Co-Op", "city": "Sandersville", "state": "GA", "url": "https://www.rallyapparelco-op.com/", "website": "https://www.rallyapparelco-op.com/", "buy_link": "https://www.rallyapparelco-op.com/contact", "phone": "478-553-1919", "email": "info@rallyapparelco-op.com", "type": "cut_and_sew", "notes": "30+ yrs; 100% Made in America; athletic wear, USA cotton; cut/sew, garment dye, sublimation", "source": "web", "source_url": "https://www.rallyapparelco-op.com/"},
    {"name": "Lydia Design Studio", "city": "Atlanta", "state": "GA", "url": "https://www.lydiadesignstudio.com/", "website": "https://www.lydiadesignstudio.com/", "buy_link": "https://www.lydiadesignstudio.com/clothing-manufacturer", "phone": "470-514-5696", "email": "", "type": "cut_and_sew", "notes": "Made in USA; cut-and-sew MOQ 45; design, sampling, production; tees, leggings, jeans, hoodies", "source": "web", "source_url": "https://www.lydiadesignstudio.com/"},
    {"name": "FAM USA", "city": "Snellville", "state": "GA", "url": "https://famusa.co/", "website": "https://famusa.co/", "buy_link": "https://famusa.co/services/cut-sew/", "phone": "770-982-9913", "email": "sales@famusa.co", "type": "cut_and_sew", "notes": "Turn-key cut & sew; dye sublimation; athletic, corporate; no minimums; 4-wk lead", "source": "web", "source_url": "https://famusa.co/"},
    {"name": "Muscogee Mills", "city": "Columbus", "state": "GA", "url": "https://www.muscogeemills.com/", "website": "https://www.muscogeemills.com/", "buy_link": "https://www.muscogeemills.com/contact-us", "phone": "706-294-1738", "email": "customerservice@muscogeemills.com", "type": "cut_and_sew", "notes": "Since 1968; cut & sew, sourcing, warehousing; domestic textile", "source": "web", "source_url": "https://www.muscogeemills.com/"},
    {"name": "The Lab Factory ATL", "city": "Atlanta", "state": "GA", "url": "https://thelabfactoryatl.com/", "website": "https://thelabfactoryatl.com/", "buy_link": "https://thelabfactoryatl.com/pages/cut-sew", "phone": "470-783-2258", "email": "info@thelabfactoryatl.com", "type": "cut_and_sew", "notes": "Cut & sew, DTF, embroidery, sublimation; concept to creation 90 days", "source": "web", "source_url": "https://thelabfactoryatl.com/"},
    {"name": "Boxercraft", "city": "Mableton", "state": "GA", "url": "https://boxercraft.com/", "website": "https://boxercraft.com/", "buy_link": "https://wholesale.boxercraft.com/", "phone": "888-717-1985", "email": "customersuccess@boxercraft.com", "type": "cut_and_sew", "notes": "NCTO member; wholesale apparel; custom blanks", "source": "NCTO", "source_url": "https://ncto.org/"},
    # California
    {"name": "Newport Cut and Sew Services", "city": "Costa Mesa", "state": "CA", "url": "https://www.newportcutandsew.com/", "website": "https://www.newportcutandsew.com/", "buy_link": "https://www.newportcutandsew.com/contact-us", "phone": "", "email": "nas@newportcutandsew.com", "type": "cut_and_sew", "notes": "50-2,000 units/style; pattern, grading, fit, sampling; Makers Row", "source": "web", "source_url": "https://www.newportcutandsew.com/"},
    # Alabama
    {"name": "Higgins Sewing and Manufacturing", "city": "Lineville", "state": "AL", "url": "https://higgins-sewing-and-manufacturing-inc-al.hub.biz/", "website": "", "buy_link": "", "phone": "256-396-2704", "email": "", "type": "cut_and_sew", "notes": "Embroidery, contract sewing, screen print; full cut & sew; 15+ yrs", "source": "web", "source_url": "https://app.makersrow.com/"},
    {"name": "Jones Sportswear Company", "city": "Birmingham", "state": "AL", "url": "https://jonessportswearonline.com/", "website": "https://jonessportswearonline.com/", "buy_link": "https://www.jonestshirts.com/pages/contact", "phone": "205-326-6264", "email": "jonessportswear@gmail.com", "type": "cut_and_sew", "notes": "Family-owned since 1979; screen print, embroidery; custom apparel", "source": "web", "source_url": "https://jonessportswearonline.com/"},
    # Florida
    {"name": "MFG Merch", "city": "Jacksonville", "state": "FL", "url": "https://mfgmerch.com/", "website": "https://mfgmerch.com/", "buy_link": "https://mfgmerch.com/contact/", "phone": "904-677-9505", "email": "info@mfgmerch.com", "type": "cut_and_sew", "notes": "Full-service cut & sew; screen print, embroidery; custom apparel", "source": "web", "source_url": "https://mfgmerch.com/"},
    {"name": "Sew It All Miami", "city": "Miami", "state": "FL", "url": "https://sewitallmiami.com/", "website": "https://sewitallmiami.com/", "buy_link": "https://sewitallmiami.com/get-a-quote/", "phone": "305-339-0085", "email": "info@sewitallmiami.com", "type": "cut_and_sew", "notes": "Embroidery, screen print, DTG; custom apparel", "source": "web", "source_url": "https://sewitallmiami.com/"},
    # New York
    {"name": "Made X Hudson", "city": "Catskill", "state": "NY", "url": "https://madexhudson.com/", "website": "https://madexhudson.com/", "buy_link": "https://madexhudson.com/pages/contact", "phone": "518-203-3696", "email": "shop@madexhudson.com", "type": "cut_and_sew", "notes": "Non-profit factory; cut-and-sew wovens; MOQ 20; 1-2 wk sampling", "source": "web", "source_url": "https://www.makersrow.com/"},
    {"name": "Apparel Production Inc", "city": "New York", "state": "NY", "url": "https://apparelproductionny.com/", "website": "https://apparelproductionny.com/", "buy_link": "https://apparelproductionny.com/contact", "phone": "212-278-8362", "email": "teddyapparelprod@aol.com", "type": "cut_and_sew", "notes": "Since 1947; 75 operators; 125 min/style; Garment District", "source": "web", "source_url": "https://apparelproductionny.com/"},
    {"name": "Carina NY", "city": "New York", "state": "NY", "url": "https://www.carina-ny.com/", "website": "https://www.carina-ny.com/", "buy_link": "https://www.carina-ny.com/contact", "phone": "917-302-1894", "email": "paula@carina-ny.com", "type": "cut_and_sew", "notes": "Since 1996; leather, denim, cotton; MOQ 50; Garment District", "source": "web", "source_url": "https://www.carina-ny.com/"},
    {"name": "Triple Stitch NYC", "city": "New York", "state": "NY", "url": "https://www.triplestitch.nyc/", "website": "https://www.triplestitch.nyc/", "buy_link": "https://www.triplestitch.nyc/", "phone": "", "email": "", "type": "cut_and_sew", "notes": "33+ yrs; USA cut & sew; fabric sourcing, pattern, sample; knit & woven", "source": "web", "source_url": "https://www.triplestitch.nyc/"},
    {"name": "NYC Factory Inc", "city": "New York", "state": "NY", "url": "https://nycfactoryinc.com/", "website": "https://nycfactoryinc.com/", "buy_link": "https://nycfactoryinc.com/pages/contact", "phone": "212-302-4673", "email": "sales@nycfactoryinc.com", "type": "cut_and_sew", "notes": "100 min/design; product dev, sampling, production; Garment District", "source": "web", "source_url": "https://nycfactoryinc.com/"},
    # Tennessee
    {"name": "Prange Apparel", "city": "Nashville", "state": "TN", "url": "https://www.prangeapparel.com/", "website": "https://www.prangeapparel.com/", "buy_link": "https://www.prangeapparel.com/", "phone": "629-246-0885", "email": "hello@prangeapparel.com", "type": "cut_and_sew", "notes": "Since 2013; women's boutique; MOQ 25; 6K sq ft; pattern, cut, sew in-house", "source": "web", "source_url": "https://www.prangeapparel.com/"},
    {"name": "Nevear", "city": "Nashville", "state": "TN", "url": "https://nevear.com/", "website": "https://nevear.com/", "buy_link": "https://nevear.com/contact-us/", "phone": "248-605-5457", "email": "", "type": "cut_and_sew", "notes": "Since 2008; MOQ 100; 2-wk prototype; cut & sew, private label", "source": "web", "source_url": "https://nevear.com/"},
    # Wisconsin
    {"name": "Borah Teamwear", "city": "Coon Valley", "state": "WI", "url": "https://borahteamwear.com/", "website": "https://borahteamwear.com/", "buy_link": "https://borahteamwear.com/get-started/", "phone": "800-354-2825", "email": "", "type": "cut_and_sew", "notes": "Since 1997; cycling, skiing, triathlon; handcrafted WI; lifetime warranty", "source": "web", "source_url": "https://borahteamwear.com/"},
    # Minnesota
    {"name": "Clothier Design Source", "city": "St Paul", "state": "MN", "url": "https://www.clothierdesignsource.com/", "website": "https://www.clothierdesignsource.com/", "buy_link": "https://www.clothierdesignsource.com/contact-us", "phone": "651-225-8025", "email": "", "type": "cut_and_sew", "notes": "Since 2006; 35+ workers; athletic, medical, children's; in-house", "source": "web", "source_url": "https://www.clothierdesignsource.com/"},
    {"name": "K1 Sportswear", "city": "Cloquet", "state": "MN", "url": "https://www.k1sportswear.com/", "website": "https://www.k1sportswear.com/", "buy_link": "https://www.k1sportswear.com/", "phone": "800-345-0028", "email": "sales@k1sportswear.com", "type": "cut_and_sew", "notes": "Since 1987; hockey, baseball, lacrosse; jerseys, socks", "source": "web", "source_url": "https://www.k1sportswear.com/"},
    # Vermont & Massachusetts
    {"name": "Fourbital Factory", "city": "Burlington", "state": "VT", "url": "https://www.fourbitalfactory.com/", "website": "https://www.fourbitalfactory.com/", "buy_link": "https://www.fourbitalfactory.com/contact-us", "phone": "802-622-1572", "email": "info@fourbitalfactory.com", "type": "cut_and_sew", "notes": "USA beanies; low MOQ; Burlington; sustainable", "source": "web", "source_url": "https://www.fourbitalfactory.com/"},
    {"name": "Vermont Flannel", "city": "", "state": "VT", "url": "https://www.vermontflannel.com/", "website": "https://www.vermontflannel.com/", "buy_link": "https://www.vermontflannel.com/pages/wholesale-program", "phone": "", "email": "wholesale@vermontflannel.com", "type": "cut_and_sew", "notes": "Since 1991; handcrafted flannel; shirts, pants, pullovers; wholesale", "source": "web", "source_url": "https://www.vermontflannel.com/"},
    {"name": "Whalerknits", "city": "Fall River", "state": "MA", "url": "https://whalerknits.com/", "website": "https://whalerknits.com/", "buy_link": "https://whalerknits.com/", "phone": "508-916-6440", "email": "", "type": "cut_and_sew", "notes": "Since 1975; 100% cotton sweaters, hats, blankets; USA-made", "source": "web", "source_url": "https://whalerknits.com/"},
    {"name": "Commonwealth", "city": "Burlington", "state": "VT", "url": "https://wearcommonwealth.com/", "website": "https://wearcommonwealth.com/", "buy_link": "https://wearcommonwealth.com/", "phone": "", "email": "", "type": "cut_and_sew", "notes": "100% organic cotton hoodies, tees; wool pennants; fan apparel; USA-made", "source": "web", "source_url": "https://wearcommonwealth.com/"},
    # Ohio
    {"name": "SEAM (Sewing Experts Assembly Manufacturing)", "city": "Cleveland", "state": "OH", "url": "https://seamsewing.com/", "website": "https://seamsewing.com/", "buy_link": "https://seamsewing.com/", "phone": "", "email": "", "type": "cut_and_sew", "notes": "Since 2017; industrial cut & sew; pattern, prototype, small batch; 30+ yrs exp", "source": "web", "source_url": "https://seamsewing.com/"},
    {"name": "Cleveland Cut and Sew", "city": "Cleveland", "state": "OH", "url": "https://clevelandcutandsew.com/", "website": "https://clevelandcutandsew.com/", "buy_link": "https://clevelandcutandsew.com/contact/", "phone": "216-314-1314", "email": "clevelandcutandsew@gmail.com", "type": "cut_and_sew", "notes": "Cut & sew manufacturing; Cleveland", "source": "web", "source_url": "https://clevelandcutandsew.com/"},
    {"name": "The Sullivan Company", "city": "Westerville", "state": "OH", "url": "https://www.wearbrandmatters.com/", "website": "https://www.wearbrandmatters.com/", "buy_link": "https://wearbrandmatters.com/contact/", "phone": "614-898-9971", "email": "", "type": "cut_and_sew", "notes": "Since 1981; screen print, embroidery, DTG; corporate, restaurant uniforms", "source": "web", "source_url": "https://www.wearbrandmatters.com/"},
    # Michigan
    {"name": "Michigan Apparel Manufacturer", "city": "", "state": "MI", "url": "https://michiganapparelmanufacturer.com/", "website": "https://michiganapparelmanufacturer.com/", "buy_link": "https://michiganapparelmanufacturer.com/", "phone": "", "email": "", "type": "cut_and_sew", "notes": "Small batch; tech pack to production; pattern, sampling, grading", "source": "web", "source_url": "https://michiganapparelmanufacturer.com/"},
    {"name": "Michigan Fashion Proto", "city": "Lansing", "state": "MI", "url": "https://www.fashionproto.com/", "website": "https://www.fashionproto.com/", "buy_link": "https://www.fashionproto.com/hire-us", "phone": "517-367-7066", "email": "info@fashionproto.com", "type": "cut_and_sew", "notes": "MOQ 25; design, pattern, sample, production; 500+ via partners", "source": "web", "source_url": "https://www.fashionproto.com/"},
    {"name": "ISAIC (Industrial Sewing and Innovation Center)", "city": "Detroit", "state": "MI", "url": "https://www.isaic.org/", "website": "https://www.isaic.org/", "buy_link": "https://www.isaic.org/advanced-manufacturing-solutions", "phone": "", "email": "manufacturing@isaic.org", "type": "cut_and_sew", "notes": "Nonprofit; sustainable apparel; workforce dev; Carhartt Bldg; contract mfg", "source": "web", "source_url": "https://www.isaic.org/"},
    {"name": "Detroit Apparel Manufacturing", "city": "Detroit", "state": "MI", "url": "https://app.makersrow.com/detroit-apparel-mfg", "website": "https://app.makersrow.com/detroit-apparel-mfg", "buy_link": "https://app.makersrow.com/detroit-apparel-mfg", "phone": "", "email": "", "type": "cut_and_sew", "notes": "Small batch; pattern, sample, screen print, embroidery; Makers Row", "source": "web", "source_url": "https://app.makersrow.com/"},
    # Illinois
    {"name": "GIL Sewing Corp", "city": "Chicago", "state": "IL", "url": "https://gilsewing.com/", "website": "https://gilsewing.com/", "buy_link": "https://gilsewing.com/", "phone": "773-545-0990", "email": "admin@gilsewing.com", "type": "cut_and_sew", "notes": "Since 1993; women-owned; uniforms, tailored, technical; full package", "source": "web", "source_url": "https://gilsewing.com/"},
    # Arizona
    {"name": "Sonoran Stitch Factory", "city": "Tucson", "state": "AZ", "url": "https://www.sonoranstitch.com/", "website": "https://www.sonoranstitch.com/", "buy_link": "https://www.sonoranstitch.com/contact-1", "phone": "520-338-9738", "email": "sonoranstitch@gmail.com", "type": "cut_and_sew", "notes": "50-4K units/mo; design, pattern, prototype, sourcing; outdoor, activewear", "source": "web", "source_url": "https://www.sonoranstitch.com/"},
    {"name": "Arena Sewing", "city": "Phoenix", "state": "AZ", "url": "https://sewing.arena.com/", "website": "https://sewing.arena.com/", "buy_link": "https://sewing.arena.com/", "phone": "855-462-7362", "email": "", "type": "cut_and_sew", "notes": "40+ yrs; tactical, military, medical, industrial; contract cut & sew", "source": "web", "source_url": "https://sewing.arena.com/"},
    # Colorado
    {"name": "Freeride Systems", "city": "Leadville", "state": "CO", "url": "https://www.freeridesystems.com/", "website": "https://www.freeridesystems.com/", "buy_link": "https://www.freeridesystems.com/contact", "phone": "719-966-7149", "email": "", "type": "cut_and_sew", "notes": "Since 2010; technical outerwear; fleece, ski; made in CO", "source": "web", "source_url": "https://www.freeridesystems.com/"},
    {"name": "Corbeaux Clothing", "city": "Aspen", "state": "CO", "url": "https://corbeauxclothing.com/", "website": "https://corbeauxclothing.com/", "buy_link": "https://corbeauxclothing.com/pages/contact-corbeaux", "phone": "", "email": "info@corbeauxclothing.com", "type": "cut_and_sew", "notes": "Base layers, adventure apparel; USA-made MN & CO; recycled", "source": "web", "source_url": "https://corbeauxclothing.com/"},
    {"name": "Colorado Threads", "city": "Lakewood", "state": "CO", "url": "https://coloradothreads.com/", "website": "https://coloradothreads.com/", "buy_link": "https://coloradothreads.com/pages/contact", "phone": "", "email": "hello@coloradothreads.com", "type": "cut_and_sew", "notes": "Athletic, outdoor; yoga, tanks, tees, hoodies; USA-made; wholesale", "source": "web", "source_url": "https://coloradothreads.com/"},
    # Washington
    {"name": "NWT3K", "city": "Seattle", "state": "WA", "url": "https://nwt3k.com/", "website": "https://nwt3k.com/", "buy_link": "https://nwt3k.com/", "phone": "", "email": "", "type": "cut_and_sew", "notes": "Ski, snowboard, mountain bike; hand-built Seattle; 2 facilities", "source": "web", "source_url": "https://nwt3k.com/"},
    # North Carolina (additional)
    {"name": "Coville", "city": "Winston-Salem", "state": "NC", "url": "https://www.covilleinc.com/", "website": "https://www.covilleinc.com/", "buy_link": "https://www.covilleinc.com/Contact-Coville.html", "phone": "336-759-0115", "email": "info@covilleinc.com", "type": "cut_and_sew", "notes": "Since 1966; knit fabrics; cut & sew, CMT; full package", "source": "web", "source_url": "https://www.covilleinc.com/"},
    {"name": "Opportunity Threads", "city": "Morganton", "state": "NC", "url": "https://www.opportunitythreads.com/", "website": "https://www.opportunitythreads.com/", "buy_link": "https://www.opportunitythreads.com/contact", "phone": "", "email": "", "type": "cut_and_sew", "notes": "Worker-owned; t-shirts, apparel, pillows, bags; sustainable", "source": "web", "source_url": "https://www.opportunitythreads.com/"},
    {"name": "North Carolina Sewn", "city": "Morganton", "state": "NC", "url": "https://northcarolinasewn.com/", "website": "https://northcarolinasewn.com/", "buy_link": "https://northcarolinasewn.com/", "phone": "828-584-8000", "email": "northcarolinasewn@gmail.com", "type": "cut_and_sew", "notes": "Since 2015; sports uniforms, polos, yoga, medical; 150+ yrs combined exp", "source": "web", "source_url": "https://www.manufacturednc.com/"},
    # Virginia
    {"name": "Integrated Textile Solutions (ITS)", "city": "Salem", "state": "VA", "url": "https://www.intextile.com/", "website": "https://www.intextile.com/", "buy_link": "https://www.intextile.com/contact-us/", "phone": "540-389-8113", "email": "info@intextile.com", "type": "cut_and_sew", "notes": "Since 1936; Berry-compliant; tactical, military, industrial; DOD", "source": "web", "source_url": "https://www.intextile.com/"},
    # Maine
    {"name": "American Roots", "city": "Westbrook", "state": "ME", "url": "https://americanrootswear.com/", "website": "https://americanrootswear.com/", "buy_link": "https://americanrootswear.com/pages/contact-us", "phone": "207-854-4098", "email": "info@americanrootswear.com", "type": "cut_and_sew", "notes": "10 yrs; 100% USA materials; union-made; hoodies, apparel", "source": "web", "source_url": "https://americanrootswear.com/"},
    {"name": "ORIGIN", "city": "Farmington", "state": "ME", "url": "https://originusa.com/", "website": "https://originusa.com/", "buy_link": "https://originusa.com/pages/contact-us", "phone": "207-860-2626", "email": "", "type": "cut_and_sew", "notes": "Since 2011; workwear, jeans, hoodies, boots; USA-made; Franklin County", "source": "web", "source_url": "https://originusa.com/"},
    # From CFDA Production Directory, Textile Connect, ManufacturedNC
    {"name": "Sew Valley", "city": "Cincinnati", "state": "OH", "url": "https://sewvalley.org/", "website": "https://sewvalley.org/", "buy_link": "https://sewvalley.org/production-services-form", "phone": "", "email": "", "type": "cut_and_sew", "notes": "Nonprofit; sample dev, small batch 10-100; pattern, prototype; 4-6 wk", "source": "CFDA", "source_url": "https://cfda.com/resources/supply-chain-manufacturing/production-directory"},
    {"name": "Rightfully Sewn", "city": "Kansas City", "state": "MO", "url": "https://rightfullysewn.org/", "website": "https://rightfullysewn.org/", "buy_link": "https://rightfullysewn.org/production", "phone": "816-492-6009", "email": "info@rightfullysewn.org", "type": "cut_and_sew", "notes": "Nonprofit; 100-400 or 1000+ units; Navy contract; workforce dev", "source": "CFDA", "source_url": "https://cfda.com/resources/supply-chain-manufacturing/production-directory"},
    {"name": "Western Carolina Sewing Company (Sew Co)", "city": "Asheville", "state": "NC", "url": "https://www.wcsewco.com/", "website": "https://www.wcsewco.com/", "buy_link": "https://www.wcsewco.com/new-client-application", "phone": "", "email": "hello@wcsewco.com", "type": "cut_and_sew", "notes": "River Arts District; design studio, urban sewing factory; contract mfg", "source": "CFDA", "source_url": "https://cfda.com/resources/supply-chain-manufacturing/production-directory"},
    {"name": "Stitch Texas", "city": "Austin", "state": "TX", "url": "https://www.stitchtexas.com/", "website": "https://www.stitchtexas.com/", "buy_link": "https://www.stitchtexas.com/", "phone": "512-291-8234", "email": "hello@stitchtexas.com", "type": "cut_and_sew", "notes": "Since 2014; female-owned; pattern, sample, production; domestic & overseas", "source": "CFDA", "source_url": "https://cfda.com/resources/supply-chain-manufacturing/production-directory"},
    {"name": "The Factory Buffalo", "city": "Buffalo", "state": "NY", "url": "https://thefactorybuffalo.com/", "website": "https://thefactorybuffalo.com/", "buy_link": "https://thefactorybuffalo.com/contact", "phone": "716-348-2362", "email": "hello@thefactorybuffalo.com", "type": "cut_and_sew", "notes": "Design, develop, manufacture; cut & sew; contract sewing", "source": "CFDA", "source_url": "https://cfda.com/resources/supply-chain-manufacturing/production-directory"},
    {"name": "Brilliant You Denim", "city": "Greensboro", "state": "NC", "url": "https://brilliantyoudenim.com/", "website": "https://brilliantyoudenim.com/", "buy_link": "https://brilliantyoudenim.com/visit-our-facility/", "phone": "336-343-5535", "email": "customercare@brilliantyoudenim.com", "type": "cut_and_sew", "notes": "Premium jeans; design, manufacture, distribute; shelf ready & custom", "source": "ManufacturedNC", "source_url": "https://www.manufacturednc.com/"},
    {"name": "Ferrara Manufacturing", "city": "Queens", "state": "NY", "url": "https://ferrara-manufacturing.com/", "website": "https://ferrara-manufacturing.com/", "buy_link": "https://ferrara-manufacturing.com/", "phone": "212-643-9292", "email": "info@ferraramfg.com", "type": "cut_and_sew", "notes": "Since 1987; 200+ min; activewear, dresses, denim, tailored; full service", "source": "CFDA", "source_url": "https://cfda.com/resources/supply-chain-manufacturing/production-directory"},
    {"name": "American Technical Solutions (ATSI)", "city": "Walkertown", "state": "NC", "url": "https://www.atsi-online.com/", "website": "https://www.atsi-online.com/", "buy_link": "https://www.atsi-online.com/contactus.htm", "phone": "336-595-2763", "email": "sales@atsi-online.com", "type": "cut_and_sew", "notes": "Cut, sew, structure bonding; aviation, automotive, retail; ballistic, pet", "source": "ManufacturedNC", "source_url": "https://www.manufacturednc.com/"},
    {"name": "Indie Source", "city": "Los Angeles", "state": "CA", "url": "https://indiesource.com/", "website": "https://indiesource.com/", "buy_link": "https://indiesource.com/", "phone": "424-200-2027", "email": "info@indiesource.com", "type": "cut_and_sew", "notes": "Since 2011; 200-20K units; design, dev, mfg; downtown LA", "source": "CFDA", "source_url": "https://cfda.com/resources/supply-chain-manufacturing/production-directory"},
    # ManufacturedNC - NC cut & sew
    {"name": "Diamond Apparel", "city": "Advance", "state": "NC", "url": "https://www.diamondgolfshirts.com/", "website": "https://www.diamondgolfshirts.com/", "buy_link": "https://www.diamondgolfshirts.com/contact-us", "phone": "", "email": "", "type": "cut_and_sew", "notes": "20 yrs; mock turtlenecks, golf shirts; 100% USA-made NC", "source": "ManufacturedNC", "source_url": "https://www.manufacturednc.com/"},
    {"name": "Excelsior Sewing LLC", "city": "Fletcher", "state": "NC", "url": "https://excelsiorsewing.business.site/", "website": "https://excelsiorsewing.business.site/", "buy_link": "", "phone": "828-398-8056", "email": "russ@excelsiorsewing.com", "type": "cut_and_sew", "notes": "Since 2012; outdoor; tents, tarps, rain gear, hiking; small runs", "source": "ManufacturedNC", "source_url": "https://www.manufacturednc.com/"},
    {"name": "Fuller Specialty Co", "city": "Burlington", "state": "NC", "url": "https://claycreek.com/", "website": "https://claycreek.com/", "buy_link": "https://claycreek.com/", "phone": "336-226-5167", "email": "", "type": "cut_and_sew", "notes": "Since 1944; mesh bags, aprons, duffles, jerseys; screen print", "source": "ManufacturedNC", "source_url": "https://www.manufacturednc.com/"},
    {"name": "Grace Apparel Company", "city": "Asheville", "state": "NC", "url": "https://www.graceapparel.co/", "website": "https://www.graceapparel.co/", "buy_link": "https://www.graceapparel.co/create", "phone": "828-242-8172", "email": "info@graceapparel.co", "type": "cut_and_sew", "notes": "Veteran-owned; custom apparel; screen print, embroidery, DTG", "source": "ManufacturedNC", "source_url": "https://www.manufacturednc.com/"},
    {"name": "Firefly Studio", "city": "Clyde", "state": "NC", "url": "https://fireflysewing.com/", "website": "https://fireflysewing.com/", "buy_link": "https://fireflysewing.com/contact", "phone": "828-593-1075", "email": "fireflysewing@icloud.com", "type": "cut_and_sew", "notes": "Small run contract sewing; knit & woven; prototype, sample", "source": "ManufacturedNC", "source_url": "https://www.manufacturednc.com/"},
    {"name": "Hawk Distributors Inc", "city": "Sanford", "state": "NC", "url": "https://www.hawkdistributors.com/", "website": "https://www.hawkdistributors.com/", "buy_link": "https://www.hawkdistributors.com/contact-us/", "phone": "888-334-1307", "email": "sales@hawkdistributors.com", "type": "cut_and_sew", "notes": "Veteran-owned; hoodies, military gear; short runs; gov contractors", "source": "ManufacturedNC", "source_url": "https://www.manufacturednc.com/"},
    {"name": "Granite Knitwear (Cal Cru)", "city": "Granite Quarry", "state": "NC", "url": "https://www.calcru.com/", "website": "https://www.calcru.com/", "buy_link": "https://www.calcru.com/", "phone": "704-279-5526", "email": "info@calcru.com", "type": "cut_and_sew", "notes": "Since 1968; t-shirts, henleys, sweats; knit garments", "source": "ManufacturedNC", "source_url": "https://www.manufacturednc.com/"},
    {"name": "Industries of the Blind", "city": "Greensboro", "state": "NC", "url": "https://industriesoftheblind.com/", "website": "https://industriesoftheblind.com/", "buy_link": "https://industriesoftheblind.com/", "phone": "336-544-3700", "email": "", "type": "cut_and_sew", "notes": "Nonprofit; employs blind/visually impaired; Army/Navy apparel", "source": "ManufacturedNC", "source_url": "https://www.manufacturednc.com/"},
    {"name": "Mt. Gilead Cut & Sew", "city": "Mt. Gilead", "state": "NC", "url": "", "website": "", "buy_link": "", "phone": "", "email": "", "type": "cut_and_sew", "notes": "Small plant; clothing, mask, bags; small & large orders", "source": "ManufacturedNC", "source_url": "https://www.manufacturednc.com/"},
    {"name": "Domestic Fabrics and Blankets Corp", "city": "Kinston", "state": "NC", "url": "https://www.domesticfabrics.com/", "website": "https://www.domesticfabrics.com/", "buy_link": "https://www.domesticfabrics.com/contact-us.html", "phone": "252-523-7948", "email": "info@domesticfabrics.com", "type": "cut_and_sew", "notes": "Healthcare linens, blankets; cut & sew; USA military", "source": "ManufacturedNC", "source_url": "https://www.manufacturednc.com/"},
    {"name": "Mack and Mack Inc", "city": "Greensboro", "state": "NC", "url": "", "website": "", "buy_link": "", "phone": "", "email": "", "type": "cut_and_sew", "notes": "Design, cut, sew; better women's wear", "source": "ManufacturedNC", "source_url": "https://www.manufacturednc.com/"},
]

# US cotton apparel manufacturers & knitters - vertically integrated; buy cotton/yarn
# Source: CottonWorks, web research
BUYABLE_APPAREL_MANUFACTURERS = [
    {"name": "Delta Apparel", "city": "Duluth", "state": "GA", "url": "https://www.deltaapparelinc.com/", "website": "https://www.deltaapparelinc.com/", "buy_link": "https://www.deltaapparelinc.com/contact", "phone": "864-232-5200", "email": "", "type": "apparel_manufacturer", "notes": "100% US cotton lines; Delta Ring-Spun, Delta Soft; USA facilities in NC; CottonWorks knitter", "source": "CottonWorks", "source_url": "https://cottonworks.com/sourcing/find-us-suppliers/"},
    {"name": "Beverly Knits", "city": "Gastonia", "state": "NC", "url": "https://www.beverlyknits.com/", "website": "https://www.beverlyknits.com/", "buy_link": "https://www.beverlyknits.com/contact", "phone": "704-861-1536", "email": "info@beverlyknits.com", "type": "apparel_manufacturer", "notes": "Largest US circular knitter; cotton & synthetic; 450K sq ft; apparel, bedding, industrial; CottonWorks", "source": "CottonWorks", "source_url": "https://cottonworks.com/sourcing/find-us-suppliers/"},
]

# Cotton fabric wholesalers - buy cotton yarn/fabric; sell to brands
# Source: web research
BUYABLE_FABRIC_WHOLESALERS = [
    {"name": "Fabric Finders Inc", "city": "Florence", "state": "AL", "url": "https://www.fabricfindersinc.com/", "website": "https://www.fabricfindersinc.com/", "buy_link": "https://www.fabricfindersinc.com/new-wholesale-account-application/", "phone": "256-767-7615", "email": "info@fabricfindersinc.com", "type": "fabric_wholesaler", "notes": "100% cotton wholesale; batiste, broadcloth, denim, flannel, pique, seersucker", "source": "web", "source_url": "https://www.fabricfindersinc.com/"},
    {"name": "David Textiles Inc", "city": "City of Commerce", "state": "CA", "url": "https://davidtextilesinc.com/", "website": "https://davidtextilesinc.com/", "buy_link": "https://davidtextilesinc.com/contact", "phone": "323-728-3231", "email": "sales@davidtextiles.net", "type": "fabric_wholesaler", "notes": "Wholesale cotton prints, flannel, digital collections", "source": "web", "source_url": "https://davidtextilesinc.com/"},
    {"name": "Robert Kaufman Fabrics", "city": "Los Angeles", "state": "CA", "url": "https://www.robertkaufman.com/", "website": "https://www.robertkaufman.com/", "buy_link": "https://www.robertkaufman.com/contact_robert_kaufman_fabrics/", "phone": "800-877-2066", "email": "info@robertkaufman.com", "type": "fabric_wholesaler", "notes": "Cotton solids, digital printing; finished package programs", "source": "web", "source_url": "https://www.robertkaufman.com/"},
    {"name": "Nature's Fabrics", "city": "", "state": "", "url": "https://naturesfabrics.com/", "website": "https://naturesfabrics.com/", "buy_link": "https://naturesfabrics.com/pages/contact-us", "phone": "814-734-7137", "email": "", "type": "fabric_wholesaler", "notes": "USA-grown cotton fabric; retail and wholesale", "source": "web", "source_url": "https://naturesfabrics.com/"},
]

# Growers with known direct corporate sales (from our list)
BUYABLE_GROWERS = [
    {
        "name": "Bridgeforth Farms",
        "city": "Tanner",
        "state": "AL",
        "url": "https://www.bridgeforthcotton.net/",
        "website": "https://www.bridgeforthcotton.net/",
        "buy_link": "https://www.bridgeforthcotton.net/",
        "phone": "",
        "email": "",
        "type": "grower_direct",
        "notes": "Sells to Target, Victoria's Secret; ~50K-65K bales/yr to VS; bridgeforthcotton.net",
        "prices": "See website for apparel; contact for B2B cotton",
        "source": "web",
        "source_url": "https://www.bridgeforthcotton.net/",
    },
]


class BuyableSource:
    """Cotton sources you can buy from - coops, merchants, direct-sale brands."""

    def __init__(self, include_scraped: bool = False, scraped_path: str | Path | None = None):
        """
        Args:
            include_scraped: If True, also yield from data/scraped_usa.csv (run scrape_all_usa.py first).
            scraped_path: Override path to scraped CSV; default data/scraped_usa.csv.
        """
        self.include_scraped = include_scraped
        self.scraped_path = Path(scraped_path) if scraped_path else Path(__file__).resolve().parent.parent.parent / "data" / "scraped_usa.csv"

    def _yield_enriched(self, items: list, default_prices: str = "Contact for quote") -> Iterator[dict]:
        """Yield records with email, phone, website, buy_link, prices populated."""
        for r in items:
            yield _enrich_record(r, default_prices)

    def fetch_all(self) -> Iterator[dict]:
        """Yield all buyable sources."""
        for r in self._yield_enriched(BUYABLE_COOPERATIVES):
            yield r
        for r in self._yield_enriched(BUYABLE_MERCHANTS):
            yield r
        for r in self._yield_enriched(BUYABLE_PRIMARY_BUYERS):
            yield r
        for r in self._yield_enriched(BUYABLE_DIRECT_SALE, "See website"):
            yield r
        for r in self._yield_enriched(BUYABLE_MILLS):
            yield r
        for r in self._yield_enriched(BUYABLE_US_SUPPLIERS):
            yield r
        for r in self._yield_enriched(BUYABLE_ORGANIC_MILLS, "See website"):
            yield r
        for r in self._yield_enriched(BUYABLE_APPAREL_MANUFACTURERS):
            yield r
        for r in self._yield_enriched(BUYABLE_CUT_AND_SEW, "Contact for quote"):
            yield r
        for r in self._yield_enriched(BUYABLE_FABRIC_WHOLESALERS, "See website"):
            yield r
        for r in self._yield_enriched(BUYABLE_ICE_WAREHOUSES):
            yield r
        for r in self._yield_enriched(BUYABLE_WAREHOUSES):
            yield r
        for r in self._yield_enriched(BUYABLE_ADDITIONAL_WAREHOUSES):
            yield r
        for r in self._yield_enriched(BUYABLE_ASSOCIATIONS):
            yield r
        for r in self._yield_enriched(BUYABLE_GROWERS, "Contact for B2B; see bridgeforthcotton.net for retail"):
            yield r
        if self.include_scraped and self.scraped_path.exists():
            import csv
            with open(self.scraped_path, encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    if "_error" not in r:
                        yield _enrich_record(dict(r), "Contact for quote")

    def fetch_cooperatives(self) -> Iterator[dict]:
        """Yield cooperatives only."""
        yield from self._yield_enriched(BUYABLE_COOPERATIVES)

    def fetch_merchants(self) -> Iterator[dict]:
        """Yield merchants only."""
        yield from self._yield_enriched(BUYABLE_MERCHANTS)

    def fetch_primary_buyers(self) -> Iterator[dict]:
        """Yield primary buyers / mill service agents."""
        yield from self._yield_enriched(BUYABLE_PRIMARY_BUYERS)

    def fetch_direct_sale(self) -> Iterator[dict]:
        """Yield direct-sale brands."""
        yield from self._yield_enriched(BUYABLE_DIRECT_SALE, "See website")

    def fetch_warehouses(self) -> Iterator[dict]:
        """Yield cotton warehouses / compresses."""
        yield from self._yield_enriched(BUYABLE_ICE_WAREHOUSES)
        yield from self._yield_enriched(BUYABLE_WAREHOUSES)
        yield from self._yield_enriched(BUYABLE_ADDITIONAL_WAREHOUSES)

    def fetch_ice_warehouses(self) -> Iterator[dict]:
        """Yield ICE Cotton No. 2 licensed warehouses."""
        yield from self._yield_enriched(BUYABLE_ICE_WAREHOUSES)

    def fetch_mills(self) -> Iterator[dict]:
        """Yield US cotton yarn/fabric mills that purchase cotton fiber."""
        yield from self._yield_enriched(BUYABLE_MILLS)
        yield from self._yield_enriched(BUYABLE_US_SUPPLIERS)
        yield from self._yield_enriched(BUYABLE_ORGANIC_MILLS, "See website")
        yield from self._yield_enriched(BUYABLE_APPAREL_MANUFACTURERS)
        yield from self._yield_enriched(BUYABLE_FABRIC_WHOLESALERS, "See website")

    def fetch_us_suppliers(self) -> Iterator[dict]:
        """Yield CottonWorks US suppliers (spinners & weavers)."""
        yield from self._yield_enriched(BUYABLE_US_SUPPLIERS)

    def fetch_cut_and_sew(self) -> Iterator[dict]:
        """Yield USA cut & sew garment manufacturers (make garments from USA cotton)."""
        yield from self._yield_enriched(BUYABLE_CUT_AND_SEW, "Contact for quote")

    def fetch_associations(self) -> Iterator[dict]:
        """Yield associations / platforms."""
        yield from self._yield_enriched(BUYABLE_ASSOCIATIONS)

    def fetch_growers(self) -> Iterator[dict]:
        """Yield growers with known direct corporate sales."""
        yield from self._yield_enriched(BUYABLE_GROWERS, "Contact for B2B; see bridgeforthcotton.net for retail")

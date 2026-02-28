"""
USA wool industry sources - growers to fabric makers to sellers to manufacturers.

From sheep/wool growers through wool buyers, processors, mills, fabric makers,
and manufacturers of wool products. Complete USA supply chain.
"""

import re
from pathlib import Path
from typing import Iterator

CONTACT_FIELDS = ("email", "phone", "website", "buy_link", "prices", "products", "production")

# Product-like terms to recognize in wool notes (case-insensitive)
_NOTES_WOOL_TERMS = (
    "scouring", "carding", "spinning", "yarn", "roving", "batting", "felting", "dyeing",
    "combing", "weaving", "worsted", "woolen", "fleece", "raw wool", "wool brokerage",
    "alpaca", "mohair", "fiber processing", "blankets", "apparel", "socks", "hats",
    "fabric", "textile", "merino", "responsible wool", "rws", "organic wool",
)

TYPE_PRODUCTS = {
    "wool_grower": "Wool; raw fleece; sheep",
    "wool_buyer": "Wool; raw fleece; wool brokerage",
    "wool_pool": "Wool; pooled marketing",
    "wool_warehouse": "Wool storage; warehousing",
    "wool_mill": "Wool yarn; roving; batting; scoured wool",
    "wool_processor": "Scouring; carding; spinning; dyeing; felting",
    "wool_fabric": "Wool fabric; worsted; woolen",
    "wool_apparel": "Wool apparel; blankets; home goods",
    "wool_manufacturer": "Wool products; apparel; textiles",
    "association": "Industry directory; referrals",
}

ASI_SOURCE = {"source": "ASI", "source_url": "https://www.sheepusa.org/contacts/wool-pelt"}


def _products_from_notes(notes: str) -> str:
    """Extract product-like terms from wool notes when no explicit products given."""
    if not notes:
        return ""
    notes_lower = notes.lower()
    # ASI: "Scouring; Carding; Spinning; Yarn; Roving; Batting"
    m = re.search(r"(?:ASI|Wool and Fiber Arts)[:\s]+([^;]+(?:;[^;]+){0,7})", notes, re.I)
    if m:
        parts = [p.strip() for p in re.split(r"[;]", m.group(1)) if 3 <= len(p.strip()) <= 50]
        if parts:
            return "; ".join(parts[:10])
    # Extract known wool product terms
    found = []
    for term in _NOTES_WOOL_TERMS:
        if term in notes_lower and term not in found:
            found.append(term.title())
    if found:
        return "; ".join(found[:12])
    return ""


def _production_from_notes(notes: str) -> str:
    """Extract production/volume indicators from wool notes."""
    if not notes:
        return ""
    # "X lbs/year", "X fleece/yr", "X million lbs"
    m = re.search(r"[\d\s,\.\-+KkMm]+(?:\s*(?:lbs?|fleece|pounds?|tons?)\s*(?:/|per)\s*(?:yr|year)|million\s*(?:lbs?|pounds?))", notes, re.I)
    if m:
        return m.group(0).strip()[:50]
    # "X+ employees", "since YYYY" (proxy for scale)
    m = re.search(r"([\d,\.]+)\+?\s*(?:employees?|growers?|members?)", notes, re.I)
    if m:
        return m.group(0).strip()[:50]
    m = re.search(r"since\s+(\d{4})", notes, re.I)
    if m:
        return "Est. " + m.group(1)
    return ""


def _enrich_record(r: dict, default_prices: str = "Contact for quote") -> dict:
    """Add defaults for contact fields; extract products and production from notes."""
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


# Wool buyers - buy raw wool from growers; ASI directory
WOOL_BUYERS = [
    {"name": "Pozzi Ranch & Wool Company", "city": "Valley Ford", "state": "CA", "phone": "707-486-0094", "email": "pozziwool@pozziwool.com", "url": "https://www.pozziwool.com/", "website": "https://www.pozziwool.com/", "buy_link": "https://www.pozziwool.com/", "type": "wool_buyer", "notes": "ASI wool buyer; Sonoma County CA; heritage breeds; raw fleece + roving; family ranch", **ASI_SOURCE},
    {"name": "Roswell Wool Brokers", "city": "Bakersfield", "state": "CA", "phone": "661-363-3260", "url": "https://www.roswellwool.com/", "type": "wool_buyer", "notes": "ASI; largest independent wool broker in USA; offices in CA, NM, SD; buying, warehousing, marketing wool + mohair", **ASI_SOURCE},
    {"name": "Groenewold Fur & Wool Co", "city": "Foreston", "state": "IL", "phone": "815-938-2381", "url": "https://www.gfwco.com/", "type": "wool_buyer", "notes": "ASI; buying raw wool + pelts; Midwest buyer", **ASI_SOURCE},
    {"name": "Bartlettyarns, Inc", "city": "Harmony", "state": "ME", "phone": "207-683-2251", "url": "https://bartlettyarns.com/", "type": "wool_buyer", "notes": "ASI; also mill; since 1821; America's oldest yarn manufacturer; mule spun woolen yarns; domestic east coast wools; 4oz skeins", "production": "Est. 1821", "prices": "4oz skeins ~$16; yarns, roving, fiber", **ASI_SOURCE},
    {"name": "Ramblers Way Farm – Wool Supply", "city": "Kennebunk", "state": "ME", "phone": "207-467-8118", "url": "https://www.ramblersway.com/", "type": "wool_buyer", "notes": "ASI; also Ramblers Way apparel brand", **ASI_SOURCE},
    {"name": "R.H. Lindsay Company", "city": "Boston", "state": "MA", "phone": "617-571-4473", "url": "https://www.rhlindsaywool.com/", "type": "wool_buyer", "notes": "ASI; wool broker/dealer; New England; raw wool buying + selling", **ASI_SOURCE},
    {"name": "Michell International", "city": "Boston", "state": "MA", "phone": "781-582-0254", "url": "https://www.michell.com.au/", "type": "wool_buyer", "notes": "ASI; global wool top-maker; Australian parent; Boston US office", **ASI_SOURCE},
    {"name": "Center of the Nation Wool", "city": "Billings", "state": "MT", "phone": "406-245-9112", "type": "wool_buyer", "notes": "ASI; MT/WY/SD region; raw wool buying + warehousing", **ASI_SOURCE},
    {"name": "Tri-State Wool Marketing", "city": "Alzada", "state": "MT", "phone": "406-828-4523", "url": "https://tristatewool.wordpress.com/", "type": "wool_buyer", "notes": "ASI; MT/WY/SD pooled marketing; cooperative buying", **ASI_SOURCE},
    {"name": "International Textile Group (Burlington)", "city": "Greensboro", "state": "NC", "phone": "336-379-2096", "type": "wool_buyer", "notes": "ASI; parent of Cone Denim + Burlington Industries; woven fabrics; military + commercial", **ASI_SOURCE},
    {"name": "Bowman Wool", "city": "Bowman", "state": "ND", "phone": "406-581-7772", "type": "wool_buyer", "notes": "ASI; Northern Plains wool buyer", **ASI_SOURCE},
    {"name": "Columbia Wool Scouring Mill (Pendleton)", "city": "Portland", "state": "OR", "phone": "503-289-3642", "url": "https://www.pendleton-usa.com/", "type": "wool_buyer", "notes": "ASI; Pendleton subsidiary; raw wool scouring; supplies Pendleton mills in OR + WA", "production": "Pendleton supply chain", **ASI_SOURCE},
    {"name": "Bollman Industries", "city": "Adamstown", "state": "PA", "phone": "717-484-4361", "url": "https://www.bollmanhats.com/", "type": "wool_buyer", "notes": "ASI; raw wool buyer for hat manufacturing; also operates wool scouring plant in San Angelo TX", **ASI_SOURCE},
    {"name": "TradeWell International, Inc", "city": "North Kingstown", "state": "RI", "phone": "401-667-0500", "type": "wool_buyer", "notes": "ASI; international wool trading", **ASI_SOURCE},
    {"name": "Chargeurs Wool (USA) Inc", "city": "Jamestown", "state": "SC", "phone": "843-257-4569", "url": "https://chargeurswoolusa.com/", "type": "wool_buyer", "notes": "ASI; top 3 global wool processor; scouring, carbonizing, combing; French parent Chargeurs SA", "production": "Top 3 global processor", **ASI_SOURCE},
    {"name": "Textile Fibers International", "city": "Lake City", "state": "SC", "phone": "843-394-7718", "type": "wool_buyer", "notes": "ASI; specialty fiber buying; South Carolina", **ASI_SOURCE},
    {"name": "Center of the Nation Wool", "city": "Belle Fourche", "state": "SD", "phone": "605-892-6311", "type": "wool_buyer", "notes": "ASI; SD/MT wool buying + warehousing", **ASI_SOURCE},
    {"name": "Anodyne, Inc", "city": "San Angelo", "state": "TX", "phone": "325-653-3061", "url": "https://www.anodynewool.com/", "type": "wool_buyer", "notes": "ASI; wool + mohair buyer; West Texas", **ASI_SOURCE},
    {"name": "Blackwell Enterprises", "city": "Goldthwaite", "state": "TX", "phone": "325-648-3103", "type": "wool_buyer", "notes": "ASI; wool + mohair buyer; Central Texas", **ASI_SOURCE},
    {"name": "Entrenos Inc", "city": "San Angelo", "state": "TX", "phone": "325-651-2665", "type": "wool_buyer", "notes": "ASI; wool buyer; San Angelo TX", **ASI_SOURCE},
    {"name": "Keese International LLC", "city": "Brady", "state": "TX", "phone": "325-456-8662", "type": "wool_buyer", "notes": "ASI; wool + mohair buyer; Brady TX", **ASI_SOURCE},
    {"name": "Wool Partners Inc", "city": "Sonora", "state": "TX", "phone": "325-413-1200", "type": "wool_buyer", "notes": "ASI; wool + mohair buyer; West Texas rangelands; Sonora TX", **ASI_SOURCE},
    {"name": "Utah Wool Marketing Association", "city": "Tooele", "state": "UT", "phone": "435-843-4284", "url": "https://utahwool.net/", "type": "wool_buyer", "notes": "ASI; wool pool/marketing cooperative for UT growers", **ASI_SOURCE},
    {"name": "Cestari Sheep & Wool Co", "city": "Churchville", "state": "VA", "phone": "540-337-7282", "url": "https://www.cestarisheep.com/", "type": "wool_buyer", "notes": "ASI; sheep ranch + wool buyer; Virginia Shenandoah Valley; raw wool, roving, yarn", **ASI_SOURCE},
    {"name": "Great Plains Wool Company", "city": "Big Horn", "state": "WY", "phone": "307-674-4504", "type": "wool_buyer", "notes": "ASI; WY wool buyer + dealer; Big Horn Basin", **ASI_SOURCE},
]

# Large commercial wool processors & mills
WOOL_PROCESSORS = [
    {"name": "American Woolen Company", "city": "Stafford Springs", "state": "CT", "url": "https://americanwoolen.com/", "phone": "860-684-2766", "email": "info@americanwoolen.com", "type": "wool_fabric", "notes": "Fine worsted and woolen fabrics; 40 looms; ~25 workers; 480 yd min; 7-35 oz/yd; RWS-certified wool, mohair, alpaca, bison; since 1899", "production": "Est. 1899; 40 looms; 25 employees", "prices": "Commission weaving; 480 yd minimum", "source": "web", "source_url": "https://americanwoolen.com/"},
    {"name": "Worsted Spinning New England (Mill Wool)", "city": "Uxbridge", "state": "MA", "url": "https://millwool.com/", "type": "wool_mill", "notes": "100+ yr old 60,000 sqft worsted spinning mill; acquired 2019; bulky-to-lace weight yarns; USA + breed-specific wools; serves large industrial + small wholesale (min 3-lb cones)", "production": "100+ years; 60,000 sqft mill", "prices": "B2B wholesale; 3-lb cone minimum", "source": "web", "source_url": "https://millwool.com/"},
    {"name": "Crescent Woolen Mills", "city": "Two Rivers", "state": "WI", "url": "https://www.crescentwoolenmills.com/", "phone": "920-793-3331", "email": "marketing@crescentwoolenmills.com", "type": "wool_mill", "notes": "Since 1923; family-owned; woolen-spun + open-end spinning; wool, alpaca, angora, silk, mohair, camel, synthetics; blending, carding, spinning, winding, twisting; Berry Amendment compliant; also Owen Glove Lining subsidiary", "production": "Est. 1923; family-owned", "prices": "B2B/wholesale; contact for quote", "source": "web", "source_url": "https://www.crescentwoolenmills.com/"},
    {"name": "Kentwool Manufacturing", "city": "Pickens", "state": "SC", "url": "https://kentwoolyarn.com/", "phone": "864-878-6367", "type": "wool_mill", "notes": "Since 1843; worsted Merino yarn; RWS certified; USTERIZED (only US mill); 56 employees; $12.9M rev; Kim Kent CEO; also Kentwool socks brand; custom fiber blends", "production": "Est. 1843; 56 employees; $12.9M rev", "prices": "B2B yarn + retail socks $20-$22/pair", "source": "web", "source_url": "https://kentwoolyarn.com/"},
    {"name": "Carolina Mills", "city": "Maiden", "state": "NC", "url": "https://www.carolinamills.com/", "email": "info@carolinamills.com", "type": "wool_mill", "notes": "Since 1928; specialty + innovative spun yarns; wool, synthetic, COOLMAX, REPREVE recycled, SORBTEK; natural + technical fiber blends; global customers", "production": "Est. 1928; 90+ years", "prices": "B2B/wholesale", "source": "web", "source_url": "https://www.carolinamills.com/"},
    {"name": "Pendleton Woolen Mills", "city": "Portland", "state": "OR", "url": "https://www.pendleton-usa.com/", "phone": "877-996-6599", "email": "pendletoncustomerservice@penwool.com", "type": "wool_apparel", "notes": "Since 1863; 6th-gen family; Oregon + Washougal mills; ~2M yards fabric/yr; blankets, shirts, apparel; NP collection; iconic American brand; 220 NW Broadway Portland HQ", "production": "~2M yards fabric/yr; Est. 1863; 2 mills", "prices": "Throws $99-$199; bed blankets $269-$369; shirts $89-$249", "source": "web", "source_url": "https://www.pendleton-usa.com/"},
    {"name": "Columbia Wool Scouring Mill", "city": "Portland", "state": "OR", "url": "https://www.pendleton-usa.com/", "type": "wool_processor", "notes": "Pendleton; wool scouring; processes for Pendleton mills", "production": "Pendleton supply chain", **ASI_SOURCE},
]

# Wool growers and ranches - direct wool producers
WOOL_GROWERS = [
    {"name": "Imperial Stock Ranch / Shaniko Wool Company", "city": "Shaniko", "state": "OR", "url": "https://www.shanikowoolcompany.com/", "website": "https://www.shanikowoolcompany.com/", "buy_link": "https://www.shanikowoolcompany.com/", "phone": "541-395-2507", "email": "jeanne@shanikowoolcompany.com", "type": "wool_grower", "notes": "30,000+ acres; Merino/Rambouillet; first RWS + NATIVA dual-certified ranch worldwide; supplied Ralph Lauren for 2014 Olympics Team USA; est. 1871; Jeanne Carver", "production": "30,000+ acres; Est. 1871", "prices": "Certified wool; contact for wholesale", "source": "web", "source_url": "https://www.shanikowoolcompany.com/"},
    {"name": "Helle Rambouillet Ranch (Duckworth)", "city": "Dillon", "state": "MT", "url": "https://www.duckworthco.com/pages/sheep-to-shelf", "website": "https://www.duckworthco.com/", "buy_link": "https://www.duckworthco.com/", "type": "wool_grower", "notes": "4th-gen Montana Merino Rambouillet ranch; sole source for Duckworth apparel; sheep-to-shelf vertically integrated; Beaverhead Valley MT", "production": "4th generation ranch; sole Duckworth source", "source": "web", "source_url": "https://www.duckworthco.com/"},
    {"name": "Montana Wool Company", "city": "Billings", "state": "MT", "url": "https://www.mtwool.com/", "website": "https://www.mtwool.com/", "buy_link": "https://www.mtwool.com/shop/", "email": "info@mtwool.com", "type": "wool_grower", "notes": "Brent & Tracie Roeder; 100% virgin Targhee wool blankets; Targhee breed developed by USDA in Idaho; Montana-grown, USA-made; est. 2017; free shipping", "production": "Family ranch; Est. 2017", "prices": "Baby blankets $130-$140; full blankets $350", "source": "web", "source_url": "https://www.mtwool.com/"},
    {"name": "Pozzi Ranch & Wool Company", "city": "Valley Ford", "state": "CA", "phone": "707-486-0094", "email": "pozziwool@pozziwool.com", "url": "https://www.pozziwool.com/", "website": "https://www.pozziwool.com/", "buy_link": "https://www.pozziwool.com/", "type": "wool_grower", "notes": "Sonoma County CA ranch; raw fleece, roving, yarn; heritage breeds; family-run", "production": "Sonoma County family ranch", "prices": "Raw fleece, roving; see website", "source": "ASI", "source_url": "https://www.sheepusa.org/contacts/wool-pelt"},
    {"name": "Cestari Sheep & Wool Co", "city": "Churchville", "state": "VA", "phone": "540-337-7282", "url": "https://www.cestarisheep.com/", "website": "https://www.cestarisheep.com/", "buy_link": "https://www.cestarisheep.com/", "type": "wool_grower", "notes": "Shenandoah Valley VA; sheep ranch; raw wool, roving, yarn; heritage breeds; family operation", "production": "Family ranch; Shenandoah Valley", "prices": "Raw wool, roving, yarn; see website", "source": "ASI", "source_url": "https://www.sheepusa.org/contacts/wool-pelt"},
]

# Wool pools and marketing associations
WOOL_POOLS = [
    {"name": "Utah Wool Marketing Association", "city": "Tooele", "state": "UT", "phone": "435-843-4284", "url": "https://utahwool.net/", "website": "https://utahwool.net/", "buy_link": "https://utahwool.net/", "type": "wool_pool", "notes": "ASI; pooled marketing for UT growers", "source": "ASI", "source_url": "https://www.sheepusa.org/contacts/wool-pelt"},
    {"name": "Tri-State Wool Marketing", "city": "Alzada", "state": "MT", "phone": "406-828-4523", "url": "https://tristatewool.wordpress.com/", "website": "https://tristatewool.wordpress.com/", "buy_link": "https://tristatewool.wordpress.com/", "type": "wool_pool", "notes": "MT/WY/SD region; pooled marketing", "source": "ASI", "source_url": "https://www.sheepusa.org/contacts/wool-pelt"},
    {"name": "Center of the Nation Wool", "city": "Belle Fourche", "state": "SD", "phone": "605-892-6311", "type": "wool_pool", "notes": "SD/MT wool pool; buying and marketing", "source": "ASI", "source_url": "https://www.sheepusa.org/contacts/wool-pelt"},
    {"name": "California Wool Growers Association", "city": "Sacramento", "state": "CA", "url": "https://californiawoolgrowers.org/", "website": "https://californiawoolgrowers.org/", "buy_link": "https://californiawoolgrowers.org/industry-contacts/member-directory/", "type": "wool_pool", "notes": "CA grower association; member directory; marketing, advocacy", "source": "web", "source_url": "https://californiawoolgrowers.org/"},
]

# Direct-sale brands - sell wool apparel/products direct to consumer
WEB_SOURCE = {"source": "web", "source_url": ""}
WOOL_DIRECT_SALE = [
    {"name": "Ramblers Way", "city": "Kennebunk", "state": "ME", "url": "https://www.ramblersway.com/", "website": "https://www.ramblersway.com/", "buy_link": "https://www.ramblersway.com/", "phone": "888-793-9665", "email": "customerservice@ramblersway.com", "type": "wool_apparel", "notes": "100% American Rambouillet Merino; traceable to ranch; worsted compacted superfine; stores in Kennebunk ME + Portland ME; Tom Chappell (Tom's of Maine)", "production": "Traceable American wool; ME manufactured", "prices": "Sweaters $99-$200; polos $130; quarter-zips $150", "source": "web", "source_url": "https://www.ramblersway.com/"},
    {"name": "Duckworth", "city": "Bozeman", "state": "MT", "url": "https://www.duckworthco.com/", "website": "https://www.duckworthco.com/", "buy_link": "https://www.duckworthco.com/", "phone": "406-922-3825", "email": "info@duckworthco.com", "type": "wool_apparel", "notes": "100% Montana-grown Merino; sheep-to-shelf; hoodies, jackets, socks, base layers; Helle family ranch", "production": "Vertically integrated ranch-to-retail", "prices": "Base layers $85; hoodies $169-$175; jackets $339-$599", "source": "web", "source_url": "https://www.duckworthco.com/"},
    {"name": "WeatherWool", "city": "Elmer", "state": "NJ", "url": "https://weatherwool.com/", "website": "https://weatherwool.com/", "buy_link": "https://weatherwool.com/", "phone": "831-704-1776", "type": "wool_apparel", "notes": "100% USA materials, labor, ownership; sources from top American breeders; outerwear, anoraks, CPO shirts, vests, pants; Merino Jacquard; family-owned since 2010; weaving in PA", "production": "Est. 2010; 100% USA; woven in PA", "prices": "CPO shirts $495-$722; HoodOrak $795; anoraks $700+", "source": "web", "source_url": "https://weatherwool.com/"},
    {"name": "Ibex", "city": "White River Junction", "state": "VT", "url": "https://ibex.com/", "website": "https://ibex.com/", "buy_link": "https://ibex.com/", "phone": "800-773-9647", "type": "wool_apparel", "notes": "Merino wool outdoor apparel; hiking, skiing, cycling; USA-made collection; founded 1997 VT, relaunched 2019; Woolies 250 base layers, TENCEL blends", "production": "Founded 1997; relaunched 2019", "prices": "Base layers $135-$145; beanies $45; hoodies $200+", "source": "web", "source_url": "https://ibex.com/"},
    {"name": "Minus33 Merino Wool Clothing", "city": "Ashland", "state": "NH", "url": "https://minus33.com/", "website": "https://minus33.com/", "buy_link": "https://minus33.com/", "type": "wool_apparel", "notes": "USA-made 100% Merino base layers in lightweight/midweight/heavyweight; hoodies, pants, crew tops; historic 1840 mill; founded by L.W. Packard engineers", "production": "Historic 1840 mill", "prices": "Base layers $60-$130; hoodies $100+", "source": "web", "source_url": "https://minus33.com/"},
    {"name": "Voormi", "city": "Pagosa Springs", "state": "CO", "url": "https://voormi.com/", "website": "https://voormi.com/", "buy_link": "https://voormi.com/", "phone": "970-264-2724", "email": "customerservice@voormi.com", "type": "wool_apparel", "notes": "Technical Merino outdoor apparel; proprietary Core Construction; retail in Pagosa Springs + Bozeman MT", "production": "CO + MT operations", "prices": "Base layers from $119; jackets $200+", "source": "web", "source_url": "https://voormi.com/"},
    {"name": "WURU Wool Co", "city": "Salt Lake City", "state": "UT", "url": "https://wuruwool.com/", "website": "https://wuruwool.com/", "buy_link": "https://wuruwool.com/", "email": "customerservice@wuruwool.com", "type": "wool_apparel", "notes": "100% USA-made merino wool apparel; tops, hoodies, base layers, boxer briefs, socks, hats, gaiters; Salt Lake City UT", "production": "USA manufactured", "prices": "Socks $15-$25; base layers $60-$120; hoodies $100+", "source": "web", "source_url": "https://wuruwool.com/"},
]

# Wool outerwear and heritage brands
WOOL_OUTERWEAR = [
    {"name": "Filson", "city": "Seattle", "state": "WA", "url": "https://www.filson.com/", "website": "https://www.filson.com/", "buy_link": "https://www.filson.com/", "phone": "206-622-3147", "type": "wool_apparel", "notes": "Since 1897; Mackinaw wool cruiser jackets, coats, vests; made in Seattle; heritage outdoor brand", "production": "Est. 1897; Seattle factory", "prices": "Wool vests $195-$275; cruiser jackets $400+", "source": "web", "source_url": "https://www.filson.com/"},
    {"name": "Woolrich", "city": "Woolrich", "state": "PA", "url": "https://www.woolrich.com/", "website": "https://www.woolrich.com/", "buy_link": "https://www.woolrich.com/", "phone": "551-307-0033", "type": "wool_apparel", "notes": "Since 1830; oldest outdoor clothing company in USA; wool shirts, jackets, blankets", "production": "Est. 1830; oldest US outdoor brand", "prices": "Overshirts $95-$545; jackets $249-$1,400", "source": "web", "source_url": "https://www.woolrich.com/"},
    {"name": "Stormy Kromer", "city": "Ironwood", "state": "MI", "url": "https://www.stormykromer.com/", "website": "https://www.stormykromer.com/", "buy_link": "https://www.stormykromer.com/", "phone": "888-455-2253", "type": "wool_apparel", "notes": "Since 1903; wool caps, Mackinaw coats, jackets; made in Ironwood MI; Jacquart Fabric Products; lifetime warranty", "production": "Est. 1903; Ironwood MI factory", "prices": "Caps $36-$48; shirt jacks $150-$360; Mackinaw coats $400-$510", "source": "web", "source_url": "https://www.stormykromer.com/"},
    {"name": "Johnson Woolen Mills", "city": "Johnson", "state": "VT", "url": "https://www.johnsonwoolenmills.com/", "website": "https://www.johnsonwoolenmills.com/", "buy_link": "https://www.johnsonwoolenmills.com/", "phone": "802-635-2271", "email": "info@johnsonwoolenmills.com", "type": "wool_apparel", "notes": "Since 1842; Merino wool hoodies, bib overalls, hunting apparel, beanies; family-owned VT mill", "production": "Est. 1842; family-owned", "prices": "Beanies $28; hunting pants/coats $200-$590", "source": "web", "source_url": "https://www.johnsonwoolenmills.com/"},
    {"name": "Bollman Hat Company", "city": "Adamstown", "state": "PA", "url": "https://www.bollmanhats.com/", "website": "https://www.bollmanhats.com/", "buy_link": "https://hats.com/bollman", "phone": "800-959-4287", "email": "contact@bollmanhats.com", "type": "wool_apparel", "notes": "Since 1868; America's oldest hat maker; wool felt hats; Kangol, Bailey, Hats.com brands; employee-owned ESOP; also operates wool scouring plant in San Angelo TX; 16-micron superfine wool", "production": "Est. 1868; ~200 employees; ESOP", "prices": "Wool felt fedoras $150-$200", "source": "web", "source_url": "https://www.bollmanhats.com/"},
    {"name": "Hardwick Clothes", "city": "Cleveland", "state": "TN", "url": "https://hardwickandcompany.com/", "website": "https://hardwickandcompany.com/", "buy_link": "https://hardwickandcompany.com/", "phone": "844-427-3942", "email": "customerservice@hardwickclothes.com", "type": "wool_apparel", "notes": "Since 1880; oldest US tailored clothing maker; 100% wool suits, blazers, tuxedos; 175K sqft facility", "production": "Est. 1880; 175K sqft", "prices": "Pants from $145; suits/coats from $350", "source": "web", "source_url": "https://hardwickandcompany.com/"},
    {"name": "Hart Schaffner Marx", "city": "New York", "state": "NY", "url": "https://hartschaffnermarx.com/", "website": "https://hartschaffnermarx.com/", "buy_link": "https://hartschaffnermarx.com/", "type": "wool_apparel", "notes": "Since 1887; worsted wool suits made in USA; Chicago/NY/LA fits; Dillard's, Nordstrom, Bloomingdale's; pioneers of modern suiting", "production": "Est. 1887", "prices": "Suits $716-$895; sport coats $400+", "source": "web", "source_url": "https://hartschaffnermarx.com/"},
    {"name": "Hertling", "city": "Fall River", "state": "MA", "url": "https://www.hertlingusa.com/", "website": "https://www.hertlingusa.com/", "buy_link": "https://www.hertlingusa.com/", "phone": "646-812-3000", "email": "justin@hertlingusa.com", "type": "wool_apparel", "notes": "Since 1925; handcrafted wool trousers, dress pants; originally Brooklyn NY; now Fall River MA; CFDA listed; Super 120s wool", "production": "Est. 1925", "prices": "Wool trousers $398-$498", "source": "web", "source_url": "https://www.hertlingusa.com/"},
    {"name": "FORLOH", "city": "Whitefish", "state": "MT", "url": "https://forloh.com/", "website": "https://forloh.com/", "buy_link": "https://forloh.com/", "phone": "833-791-0091", "email": "support@forloh.com", "type": "wool_apparel", "notes": "100% USA made; technical merino wool hunting + outdoor apparel; hi-loft wool insulation; first US company to hand-lay merino before quilting; lifetime warranty; since 2020; retail in Whitefish MT + Austin TX", "production": "Est. 2020; Whitefish MT + Austin TX", "prices": "Base layers $80-$150; jackets $300-$600", "source": "web", "source_url": "https://forloh.com/"},
    {"name": "The Checkroom", "city": "Chicago", "state": "IL", "url": "https://www.coatcheckroom.com/", "website": "https://www.coatcheckroom.com/", "buy_link": "https://www.coatcheckroom.com/", "email": "liz@coatcheckchicago.com", "type": "wool_apparel", "notes": "American-made wool coats; RWS + NATIVA certified Shaniko wool; scouring SC, woven by American Woolen CT, assembled Chicago; 16.5 micron; made to order 2-3 wk; designer Liz Williams", "production": "Full USA supply chain; made to order", "prices": "Coats $425-$1,250; made to order 2-3 wks", "source": "web", "source_url": "https://www.coatcheckroom.com/"},
]

# Wool sock manufacturers
WOOL_SOCKS = [
    {"name": "Darn Tough Vermont (Cabot Hosiery Mills)", "city": "Northfield", "state": "VT", "url": "https://darntough.com/", "website": "https://darntough.com/", "buy_link": "https://darntough.com/", "phone": "877-327-6883", "email": "support@darntough.com", "type": "wool_manufacturer", "notes": "Merino wool socks; lifetime guarantee; made in VT; Cabot Hosiery est. 1978; Darn Tough brand since 2004", "production": "Est. 1978; Northfield VT mill", "prices": "~$30/pair; hiking, ski, tactical, work styles", "source": "web", "source_url": "https://darntough.com/"},
    {"name": "Farm to Feet (Nester Hosiery)", "city": "Mount Airy", "state": "NC", "url": "https://www.farmtofeet.com/", "website": "https://www.farmtofeet.com/", "buy_link": "https://www.farmtofeet.com/", "phone": "336-789-0026", "type": "wool_manufacturer", "notes": "100% American materials; wool processed in SC, spun in NC, knit in Mount Airy; ~200 employees; Bluesign certified; acquired Fox River Mills 2025; US Army contracts", "production": "~200 employees; 100% US supply chain", "prices": "$22-$27/pair; lightweight to full cushion", "source": "web", "source_url": "https://www.farmtofeet.com/"},
    {"name": "Wigwam Mills", "city": "Sheboygan", "state": "WI", "url": "https://www.wigwam.com/", "website": "https://www.wigwam.com/", "buy_link": "https://www.wigwam.com/", "phone": "920-457-5551", "email": "support@wigwam.com", "type": "wool_manufacturer", "notes": "Since 1905; American-made wool socks; Sheboygan WI; domestic yarn spinners; AWC certified", "production": "Est. 1905; Sheboygan WI factory", "prices": "$17-$21/pair; hiking, outdoor, everyday", "source": "web", "source_url": "https://www.wigwam.com/"},
    {"name": "Cloudline Apparel", "city": "Seattle", "state": "WA", "url": "https://www.cloudlineapparel.com/", "website": "https://www.cloudlineapparel.com/", "buy_link": "https://www.cloudlineapparel.com/", "phone": "206-658-3086", "type": "wool_manufacturer", "notes": "Merino wool hiking socks; knit in Fort Payne AL; lifetime guarantee; carbon-neutral shipping; ultralight to full cushion", "production": "Knit in Fort Payne AL", "prices": "~$15-$20/pair; 3-packs available", "source": "web", "source_url": "https://www.cloudlineapparel.com/"},
    {"name": "Hippy Feet", "city": "Minneapolis", "state": "MN", "url": "https://hippyfeet.com/", "website": "https://hippyfeet.com/", "buy_link": "https://hippyfeet.com/", "type": "wool_manufacturer", "notes": "60% Merino wool crew socks; B Corp; 50% profits to homeless orgs; knit in NC; heavy-duty 2x yarn; antimicrobial", "production": "B Corp; knit in NC", "prices": "4-pack $84-$104; ~$21-$26/pair", "source": "web", "source_url": "https://hippyfeet.com/"},
    {"name": "Smartwool", "city": "Steamboat Springs", "state": "CO", "url": "https://www.smartwool.com/", "website": "https://www.smartwool.com/", "buy_link": "https://www.smartwool.com/", "phone": "888-879-9665", "email": "customerservice@smartwool.com", "type": "wool_manufacturer", "notes": "Since 1994; performance Merino wool socks + apparel; socks designed/constructed in USA; pioneer of merino sport socks", "production": "Est. 1994; socks made in USA", "prices": "$21-$30/pair; hiking, ski, run, everyday", "source": "web", "source_url": "https://www.smartwool.com/"},
    {"name": "Point6", "city": "Steamboat Springs", "state": "CO", "url": "https://point6.com/", "website": "https://point6.com/", "buy_link": "https://point6.com/", "phone": "970-871-1055", "type": "wool_manufacturer", "notes": "Compact-spun Merino wool socks + base layers; lifetime guarantee; family-owned since 2008; ~16 employees; ultra light to heavy cushion", "production": "Est. 2008; family-owned", "prices": "~$18-$28/pair; 40% off everyday pricing", "source": "web", "source_url": "https://point6.com/"},
    {"name": "Maggie's Organics", "city": "Ypsilanti", "state": "MI", "url": "https://maggiesorganics.com/", "website": "https://maggiesorganics.com/", "buy_link": "https://maggiesorganics.com/", "phone": "800-609-8593", "email": "maggies@organicclothes.com", "type": "wool_manufacturer", "notes": "Organic Merino wool socks; knit in USA since 1992; certified organic; sustainable practices", "production": "Knitting in USA since 1992", "source": "web", "source_url": "https://maggiesorganics.com/"},
    {"name": "Fox River (Nester Hosiery)", "city": "Mount Airy", "state": "NC", "url": "https://foxsox.com/", "website": "https://foxsox.com/", "buy_link": "https://foxsox.com/", "type": "wool_manufacturer", "notes": "Founded 1900 Osage IA; acquired by Nester Hosiery 2025; Merino wool hiking, military, work socks; Red Heel socks; made in USA", "production": "Est. 1900; now Mount Airy NC", "prices": "$12-$20/pair; hiking, military, work", "source": "web", "source_url": "https://foxsox.com/"},
    {"name": "Kentwool", "city": "Pickens", "state": "SC", "url": "https://www.kentwool.com/", "website": "https://www.kentwool.com/", "buy_link": "https://www.kentwool.com/", "type": "wool_manufacturer", "notes": "Since 1843; world's best golf sock; Super Fine Merino; PGA/LPGA Tour; Lifetime Blister-Free Guarantee; made in USA", "production": "Est. 1843; Pickens SC mill", "prices": "Golf socks $20-$22/pair", "source": "web", "source_url": "https://www.kentwool.com/"},
]

# Wool blanket and home goods makers
WOOL_HOME_GOODS = [
    {"name": "Faribault Mill", "city": "Faribault", "state": "MN", "url": "https://www.faribaultmill.com/", "website": "https://www.faribaultmill.com/", "buy_link": "https://www.faribaultmill.com/", "phone": "507-412-5534", "email": "customerservice@faribaultmill.com", "type": "wool_apparel", "notes": "Since 1865; wool blankets, throws, scarves; made in USA; featured in Vogue, NYT, Gear Patrol; AWC certified", "production": "Est. 1865; Faribault MN mill", "prices": "Throws $169-$245; bed blankets $269+", "source": "web", "source_url": "https://www.faribaultmill.com/"},
    {"name": "Chatham Manufacturing Company", "city": "Elkin", "state": "NC", "url": "https://www.chathammfg.com/", "website": "https://www.chathammfg.com/", "buy_link": "https://www.chathammfg.com/", "type": "wool_apparel", "notes": "Since 1877; 100% pure wool heritage blankets; reissued original 1890s patterns; Elkin NC; Blue Stripe $250; Merino/mohair plaids $395; camp blankets $350; all USA-made; free shipping", "production": "Est. 1877; Elkin NC factory", "prices": "Blue Stripe $250; plaids $350-$395", "source": "web", "source_url": "https://www.chathammfg.com/"},
    {"name": "Tuscarora Mills", "city": "Bedford", "state": "PA", "url": "https://tuscaroramills.com/", "website": "https://tuscaroramills.com/", "buy_link": "https://tuscaroramills.com/", "phone": "814-285-8594", "email": "tuscamills@gmail.com", "type": "wool_apparel", "notes": "Heirloom wool & Supima cotton blankets; vintage Crompton-Knowles shuttle looms; selvedge fabric; American-grown wool; no petroleum synthetics; 'Real American Heirlooms'; showroom Bedford PA, mill Red Lion PA", "production": "Vintage loom manufacturing", "prices": "Heirloom blankets; contact for pricing", "source": "web", "source_url": "https://tuscaroramills.com/"},
    {"name": "Frankenmuth Woolen Mill", "city": "Frankenmuth", "state": "MI", "url": "https://wool-bedding.com/", "website": "https://wool-bedding.com/", "buy_link": "https://wool-bedding.com/", "phone": "888-497-4534", "email": "matt@wool-bedding.com", "type": "wool_manufacturer", "notes": "Since 1894; largest US wool bedding maker; Climate Beneficial Wool; organic cotton cover; hand-knotted batting; pillows, comforters, toppers", "production": "Est. 1894; largest US wool bedding", "prices": "Comforters from $199; sets $350-$385", "source": "web", "source_url": "https://wool-bedding.com/"},
    {"name": "Swans Island Company", "city": "Northport", "state": "ME", "url": "https://swansislandcompany.com/", "website": "https://swansislandcompany.com/", "buy_link": "https://swansislandcompany.com/", "phone": "888-526-9526", "email": "info@swansislandcompany.com", "type": "wool_apparel", "notes": "Handwoven wool blankets, throws; Maine; monogramming, custom design; heirloom quality", "production": "Handwoven in Maine", "prices": "Throws $495-$725; limited editions $995", "source": "web", "source_url": "https://swansislandcompany.com/"},
    {"name": "Shepherd's Dream", "city": "Ashland", "state": "OR", "url": "https://shepherdsdream.com/", "website": "https://shepherdsdream.com/", "buy_link": "https://shepherdsdream.com/", "phone": "541-708-5540", "type": "wool_manufacturer", "notes": "30+ years; all-wool mattresses, toppers, comforters, pillows; handmade in Ashland OR; EcoWool batting; 2-3 wk production", "production": "30+ years; handmade to order", "prices": "Mattresses $1,550-$3,100; systems $1,811-$3,613", "source": "web", "source_url": "https://shepherdsdream.com/"},
    {"name": "Holy Lamb Organics", "city": "Oakville", "state": "WA", "url": "https://www.holylamborganics.com/", "website": "https://www.holylamborganics.com/", "buy_link": "https://www.holylamborganics.com/", "phone": "360-819-6047", "type": "wool_manufacturer", "notes": "Certified organic wool bedding; mattress toppers, pillows, comforters; handmade in WA", "production": "Handmade in WA", "prices": "Toppers $649-$1,199; pillows from $100+", "source": "web", "source_url": "https://www.holylamborganics.com/"},
    {"name": "Havelock Wool", "city": "Reno", "state": "NV", "url": "https://www.havelockwool.com/", "website": "https://www.havelockwool.com/", "buy_link": "https://www.havelockwool.com/", "phone": "775-971-4870", "email": "sales@havelockwool.com", "type": "wool_manufacturer", "notes": "100% sheep wool building insulation; thermal + acoustic; batt, blown-in, van; Lowe's, Home Depot; Reno NV factory; ships from stock", "production": "Reno NV factory; sold at Lowe's + Home Depot", "prices": "Batts $2.33-$2.44/sqft; loose fill $1.58-$4.18/sqft by R-value", "source": "web", "source_url": "https://www.havelockwool.com/"},
]

# Wool yarn brands and specialty spinners
WOOL_YARN_BRANDS = [
    {"name": "Brooklyn Tweed", "city": "Portland", "state": "OR", "url": "https://brooklyntweed.com/", "website": "https://brooklyntweed.com/", "buy_link": "https://brooklyntweed.com/", "email": "info@brooklyntweed.com", "type": "wool_mill", "notes": "Breed-specific American Targhee-Columbia wool yarns; sourced, dyed, spun in USA; woolen + worsted; AWC certified; since 2010", "production": "100% USA sourced/spun", "prices": "Skeins ~$14-$20 (Shelter 140yd, Loft 275yd)", "source": "web", "source_url": "https://brooklyntweed.com/"},
    {"name": "Mountain Meadow Wool", "city": "Buffalo", "state": "WY", "url": "https://mountainmeadowwool.com/", "website": "https://mountainmeadowwool.com/", "buy_link": "https://mountainmeadowwool.com/", "phone": "307-684-5775", "email": "info@mountainmeadowwool.com", "type": "wool_mill", "notes": "Full-service wool mill; 60,000+ lbs/yr; 23 yarn types; ranch-traceable; custom processing; apparel, throws", "production": "60,000+ lbs/yr", "prices": "See website", "source": "web", "source_url": "https://mountainmeadowwool.com/"},
    {"name": "Green Mountain Spinnery", "city": "Putney", "state": "VT", "url": "https://www.spinnery.com/", "website": "https://www.spinnery.com/", "buy_link": "https://www.spinnery.com/", "phone": "802-387-4528", "email": "spinnery@spinnery.com", "type": "wool_mill", "notes": "Since 1981; Certified Organic wool; vintage equipment; North American fibers only; custom processing min 35 lbs", "production": "Est. 1981; Certified Organic", "prices": "See website", "source": "web", "source_url": "https://www.spinnery.com/"},
    {"name": "Jagger Spun", "city": "Springvale", "state": "ME", "url": "https://www.jaggeryarn.com/", "website": "https://www.jaggeryarn.com/", "buy_link": "https://www.jaggeryarn.com/", "type": "wool_mill", "notes": "Since 1898; worsted spun yarns; Maine Line 100% wool; Mousam Falls; cones + skeins; wholesale + retail", "production": "Est. 1898; ME mill", "prices": "Skeins $13-$40; Superfine Merino $16/50g", "source": "web", "source_url": "https://www.jaggeryarn.com/"},
    {"name": "Bellwether Wool Company", "city": "Blodgett", "state": "OR", "url": "https://bellwetherwool.com/", "website": "https://bellwetherwool.com/", "buy_link": "https://bellwetherwool.com/", "type": "wool_grower", "notes": "Two farms in Oregon coastal foothills; Cormo, Wensleydale, Leicester breeds; roving, yarn, fleece direct", "production": "Oregon farms", "prices": "See website", "source": "web", "source_url": "https://bellwetherwool.com/"},
    {"name": "Cactus Hill Farm", "city": "La Veta", "state": "CO", "url": "https://www.cactushillfarm.com/", "website": "https://www.cactushillfarm.com/", "buy_link": "https://www.cactushillfarm.com/wool", "type": "wool_grower", "notes": "Southern CO; certified organic pastures; Merino, Wensleydale, CVM, BFL, Teeswater; fleeces, roving, yarn, pelts", "production": "Certified organic", "prices": "See website", "source": "web", "source_url": "https://www.cactushillfarm.com/"},
]

# Additional mills/processors with known capabilities
WOOL_ADDITIONAL_MILLS = [
    {"name": "Zeilinger Wool Company", "city": "Frankenmuth", "state": "MI", "url": "https://www.zwool.com/", "website": "https://www.zwool.com/", "buy_link": "https://www.zwool.com/", "phone": "989-652-2920", "email": "info@zwool.com", "type": "wool_mill", "notes": "Custom fiber processing; 175,000 lbs raw fiber/yr; wool, alpaca, angora, camel, llama, yak, buffalo; yarn, socks, mattress pads, quilts, blankets; Tue-Fri 9-5", "production": "175,000 lbs/yr custom processing", "prices": "Custom processing; contact for quote", "source": "Wool and Fiber Arts", "source_url": "https://woolandfiberarts.com/"},
    {"name": "Mendocino Wool and Fiber", "city": "Ukiah", "state": "CA", "url": "https://www.mendowool.com/", "website": "https://www.mendowool.com/", "buy_link": "https://www.mendowool.com/", "type": "wool_mill", "notes": "Family-owned fiber processing mill; custom processing locally sourced animal fiber; yarn, roving, woven goods; shearing, spinning, weaving; classes/workshops; retail store on-site; Fibershed member", "production": "Custom processing; Fibershed member", "prices": "Custom processing; retail store", "source": "web", "source_url": "https://www.mendowool.com/"},
    {"name": "Pendleton Woolen Mills (Washougal)", "city": "Washougal", "state": "WA", "url": "https://www.pendleton-usa.com/", "website": "https://www.pendleton-usa.com/", "buy_link": "https://www.pendleton-usa.com/", "phone": "360-835-1118", "type": "wool_mill", "notes": "Since 1912; worsted + woolen fabrics; blankets, apparel fabric; 190 employees; 3 shifts/day; free mill tours", "production": "190 employees; 3 shifts/day", "source": "web", "source_url": "https://www.pendleton-usa.com/"},
    {"name": "Pendleton Woolen Mills (Pendleton)", "city": "Pendleton", "state": "OR", "url": "https://www.pendleton-usa.com/", "website": "https://www.pendleton-usa.com/", "buy_link": "https://www.pendleton-usa.com/", "phone": "541-276-6911", "type": "wool_mill", "notes": "Since 1909; jacquard blanket weaving; carding, spinning, weaving; one of 4 remaining US woolen mills; 14K visitors/yr", "production": "One of 4 remaining US woolen mills", "source": "web", "source_url": "https://www.pendleton-usa.com/"},
    {"name": "Ranching Tradition Fiber", "city": "Whitehall", "state": "MT", "url": "https://www.ranchingtraditionfiber.com/", "website": "https://www.ranchingtraditionfiber.com/", "buy_link": "https://www.ranchingtraditionfiber.com/", "email": "ranchingtraditionfiber@gmail.com", "type": "wool_mill", "notes": "Montana ranch fiber processing; wool industry blog + advocacy; connecting ranchers to mills; raw wool, dyed/undyed fiber, yarns", "source": "web", "source_url": "https://www.ranchingtraditionfiber.com/"},
    {"name": "Battenkill Fibers", "city": "Greenwich", "state": "NY", "url": "https://www.battenkillfibers.com/", "website": "https://www.battenkillfibers.com/", "buy_link": "https://www.battenkillfibers.com/", "phone": "518-692-2700", "email": "mjpacker@battenkillfibers.com", "type": "wool_mill", "notes": "Since 2009; worsted spinning; 100-150 lbs artisan yarn daily; heritage + rare breed wools; farmers get own fiber back; semi-worsted process", "production": "Est. 2009; 100-150 lbs/day", "prices": "Custom processing; contact for quote", "source": "web", "source_url": "https://www.battenkillfibers.com/"},
    {"name": "Kraemer Yarns", "city": "Nazareth", "state": "PA", "url": "https://patternsbykraemer.com/", "website": "https://patternsbykraemer.com/", "buy_link": "https://patternsbykraemer.com/", "phone": "800-759-5601", "email": "info@kraemeryarns.com", "type": "wool_mill", "notes": "American yarn manufacturer; domestic wool; supplied L.L. Bean + Remington; produced yarns for 2014 US Olympic team; wool + fiber blends", "production": "US manufacturer; Olympic supplier", "prices": "Skeins $9-$16; wholesale available", "source": "web", "source_url": "https://patternsbykraemer.com/"},
    {"name": "Oregon Wool & Fiber Mill", "city": "Creswell", "state": "OR", "url": "https://www.oregonwoolandfibermill.com/", "website": "https://www.oregonwoolandfibermill.com/", "buy_link": "https://www.oregonwoolandfibermill.com/", "email": "ORwoolandfibermill@gmail.com", "type": "wool_mill", "notes": "Woman-owned small batch mill; custom fiber processing; wool, alpaca; scour, card, roving, batts; by appointment", "production": "Small batch custom", "prices": "Scour $12/lb; carding $25-$26/lb; min 2 lbs", "source": "web", "source_url": "https://www.oregonwoolandfibermill.com/"},
    {"name": "Columbia Custom Carding", "city": "Deer Island", "state": "OR", "url": "https://www.cccarding.com/", "website": "https://www.cccarding.com/", "buy_link": "https://www.cccarding.com/", "phone": "503-410-3152", "type": "wool_mill", "notes": "Full-service mill; scouring, carding, spinning; wool + fiber processing; Deer Island OR", "production": "Custom processing", "prices": "Custom processing; contact for quote", "source": "web", "source_url": "https://www.cccarding.com/"},
    {"name": "Blackberry Ridge Woolen Mill", "city": "Mount Horeb", "state": "WI", "url": "https://www.blackberry-ridge.com/", "website": "https://www.blackberry-ridge.com/", "buy_link": "https://www.blackberry-ridge.com/", "type": "wool_mill", "notes": "Family-owned spinnery; custom washing, carding, spinning; min 2 lbs; WI", "production": "Family-owned custom mill", "prices": "Carding $9.50-$10/lb; spinning extra", "source": "web", "source_url": "https://www.blackberry-ridge.com/"},
    {"name": "Four Winds Farm", "city": "Quincy", "state": "CA", "url": "https://www.fourwindswool.com/", "website": "https://www.fourwindswool.com/", "buy_link": "https://www.fourwindswool.com/", "type": "wool_grower", "notes": "Plumas County CA; Jacob sheep; handspun yarns in natural colors; dyed with forest + garden dyes", "production": "Small farm", "prices": "Handspun yarns, fleeces", "source": "web", "source_url": "https://www.fourwindswool.com/"},
    {"name": "Lamb and Wool (lambandwool.com)", "city": "Ennis", "state": "MT", "url": "https://www.lambandwool.com/", "website": "https://www.lambandwool.com/", "buy_link": "https://www.lambandwool.com/fleece", "type": "wool_grower", "notes": "Montana; certified organic; mostly-Romney flock; raw fleeces, washed fleece, roving, batts, felt, finished yarn", "production": "Certified organic", "prices": "Individual fleeces $8/lb", "source": "web", "source_url": "https://www.lambandwool.com/"},
    {"name": "Authenticity50", "city": "Portland", "state": "OR", "url": "https://authenticity50.com/", "website": "https://authenticity50.com/", "buy_link": "https://authenticity50.com/", "type": "wool_apparel", "notes": "Seed-to-Stitch USA bedding; Northwest Wool Throw woven at Pendleton; Oregon-sourced wool; 4000+ 5-star reviews; Heritage Blankets made in ME", "production": "Sheep-to-Stitch USA", "prices": "Throws from $149; blankets from $199", "source": "web", "source_url": "https://authenticity50.com/"},
]

# Associations
WOOL_ASSOCIATIONS = [
    {"name": "American Sheep Industry Association (ASI)", "city": "Englewood", "state": "CO", "url": "https://www.sheepusa.org/", "phone": "303-771-3500", "type": "association", "notes": "Wool & pelt contacts; shearers, buyers, mills, warehouses", "source": "ASI", "source_url": "https://www.sheepusa.org/contacts/wool-pelt"},
    {"name": "American Wool", "city": "", "state": "", "url": "https://www.americanwool.org/", "type": "association", "notes": "Finished products featuring American wool", "source": "ASI", "source_url": "https://www.americanwool.org/"},
    {"name": "National Mill Inventory", "city": "", "state": "", "url": "https://nationalmillinventory.com/", "type": "association", "notes": "Fibershed; fiber mills by location, fiber type, services", "source": "web", "source_url": "https://nationalmillinventory.com/"},
    {"name": "Wool and Fiber Arts", "city": "", "state": "", "url": "https://woolandfiberarts.com/pages/us-mill-directory", "type": "association", "notes": "US Mill Directory by state; searchable database of fiber mills, processors; listings include services, fiber types, contact info", "source": "web", "source_url": "https://woolandfiberarts.com/pages/us-mill-directory"},
    {"name": "Fibershed", "city": "San Geronimo", "state": "CA", "url": "https://fibershed.org/", "website": "https://fibershed.org/", "buy_link": "https://fibershed.org/producer-directory/", "type": "association", "notes": "Regional fiber systems; producer directory; Climate Beneficial wool; Northern/Central CA focus", "source": "web", "source_url": "https://fibershed.org/"},
    {"name": "American Wool Assurance (AWA)", "city": "", "state": "", "url": "https://www.americanwoolassurance.org/", "website": "https://www.americanwoolassurance.org/", "buy_link": "https://www.americanwoolassurance.org/", "type": "association", "notes": "Voluntary 3-level certification for wool growers; animal care + welfare standards", "source": "web", "source_url": "https://www.americanwoolassurance.org/"},
]


class WoolSource:
    """USA wool industry sources - growers, buyers, processors, mills, manufacturers."""

    def __init__(self, include_scraped: bool = False, scraped_path: str | Path | None = None):
        self.include_scraped = include_scraped
        self.scraped_path = Path(scraped_path) if scraped_path else Path(__file__).resolve().parent.parent.parent / "data" / "scraped_wool.csv"

    def _yield_enriched(self, items: list, default_prices: str = "Contact for quote") -> Iterator[dict]:
        for r in items:
            yield _enrich_record(r, default_prices)

    def fetch_all(self) -> Iterator[dict]:
        """Yield all wool sources."""
        for r in self._yield_enriched(WOOL_GROWERS):
            yield r
        for r in self._yield_enriched(WOOL_POOLS):
            yield r
        for r in self._yield_enriched(WOOL_BUYERS):
            yield r
        for r in self._yield_enriched(WOOL_PROCESSORS):
            yield r
        for r in self._yield_enriched(WOOL_DIRECT_SALE):
            yield r
        for r in self._yield_enriched(WOOL_OUTERWEAR):
            yield r
        for r in self._yield_enriched(WOOL_SOCKS):
            yield r
        for r in self._yield_enriched(WOOL_HOME_GOODS):
            yield r
        for r in self._yield_enriched(WOOL_YARN_BRANDS, "See website"):
            yield r
        for r in self._yield_enriched(WOOL_ADDITIONAL_MILLS):
            yield r
        for r in self._yield_enriched(WOOL_ASSOCIATIONS):
            yield r
        if self.include_scraped and self.scraped_path.exists():
            import csv
            with open(self.scraped_path, encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    if "_error" not in r:
                        yield _enrich_record(dict(r), "Contact for quote")

    def fetch_wool_growers(self) -> Iterator[dict]:
        """Yield wool growers and ranches."""
        yield from self._yield_enriched(WOOL_GROWERS)

    def fetch_wool_pools(self) -> Iterator[dict]:
        """Yield wool pools and marketing associations."""
        yield from self._yield_enriched(WOOL_POOLS)

    def fetch_wool_buyers(self) -> Iterator[dict]:
        yield from self._yield_enriched(WOOL_BUYERS)

    def fetch_wool_processors(self) -> Iterator[dict]:
        yield from self._yield_enriched(WOOL_PROCESSORS)

    def fetch_wool_apparel(self) -> Iterator[dict]:
        """Yield all wool apparel brands (direct sale, outerwear, socks)."""
        yield from self._yield_enriched(WOOL_DIRECT_SALE)
        yield from self._yield_enriched(WOOL_OUTERWEAR)
        yield from self._yield_enriched(WOOL_SOCKS)

    def fetch_wool_home_goods(self) -> Iterator[dict]:
        """Yield wool blanket and home goods makers."""
        yield from self._yield_enriched(WOOL_HOME_GOODS)

    def fetch_wool_yarn(self) -> Iterator[dict]:
        """Yield wool yarn brands and specialty spinners."""
        yield from self._yield_enriched(WOOL_YARN_BRANDS, "See website")

    def fetch_associations(self) -> Iterator[dict]:
        yield from self._yield_enriched(WOOL_ASSOCIATIONS)

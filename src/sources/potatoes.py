"""
USA organic potato industry sources - farms, processors, and sellers.

Organic and certified organic potato growers, seed suppliers, and direct-sale
retailers located in the USA. Includes seed potatoes and table potatoes.
"""

import re
from pathlib import Path
from typing import Iterator

CONTACT_FIELDS = ("email", "phone", "website", "buy_link", "prices", "products", "production")

_NOTES_POTATO_TERMS = (
    "seed potatoes", "table potatoes", "yukon gold", "russet", "red norland",
    "fingerling", "purple", "organic", "certified organic", "ccof", "usda organic",
    "csa", "farm stand", "farmers market", "wholesale", "retail",
    "heirloom", "blue tag", "storage", "fresh",
)

TYPE_PRODUCTS = {
    "potato_farm": "Organic potatoes; seed or table; farm direct",
    "potato_processor": "Potato packing; distribution; processing",
    "potato_retailer": "Organic potatoes; online retail; farm stand",
    "potato_wholesale": "Wholesale organic potatoes; food service",
    "association": "Industry directory; advocacy; certification",
}


def _products_from_notes(notes: str) -> str:
    if not notes:
        return ""
    notes_lower = notes.lower()
    found = []
    for term in _NOTES_POTATO_TERMS:
        if term in notes_lower and term not in found:
            found.append(term.title())
    if found:
        return "; ".join(found[:12])
    return ""


def _production_from_notes(notes: str) -> str:
    if not notes:
        return ""
    m = re.search(r"([\d,\.]+)\+?\s*(?:acres?|lbs?|pounds?)\s*(?:/|per)\s*(?:yr|year)", notes, re.I)
    if m:
        return m.group(0).strip()[:50]
    m = re.search(r"([\d,\.]+)\+?\s*(?:employees?|growers?|farms?)", notes, re.I)
    if m:
        return m.group(0).strip()[:50]
    m = re.search(r"(?:since|est\.?|founded)\s+(\d{4})", notes, re.I)
    if m:
        return "Est. " + m.group(1)
    return ""


def _enrich_record(r: dict, default_prices: str = "Contact for pricing") -> dict:
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


# ---------------------------------------------------------------------------
# Organic potato farms (direct-to-consumer)
# ---------------------------------------------------------------------------
POTATO_ORGANIC_FARMS = [
    {
        "name": "Wood Prairie Family Farm",
        "city": "Bridgewater", "state": "ME",
        "url": "https://www.woodprairie.com/",
        "website": "https://www.woodprairie.com/",
        "buy_link": "https://www.woodprairie.com/",
        "phone": "207-429-9765",
        "email": "orders@woodprairie.com",
        "type": "potato_farm",
        "notes": "49 years; certified organic seed potatoes + fresh; ships all 50 states; Yukon Gold, Dark Red Norland, 40+ varieties; 49 Kinney Rd Bridgewater ME; M-F 8-5; flexible shipping dates",
        "production": "49 years; Bridgewater ME",
        "prices": "Seed potatoes from $8.49; ships year-round",
        "certification": "certified_organic",
        "source": "web", "source_url": "https://www.woodprairie.com/",
    },
    {
        "name": "Grand Teton Organics",
        "city": "Idaho Falls", "state": "ID",
        "url": "https://www.grandtetonorganics.com/",
        "website": "https://www.grandtetonorganics.com/",
        "buy_link": "https://www.grandtetonorganics.com/Catalog/home.aspx",
        "phone": "208-313-7303",
        "email": "joolhgna@msn.com",
        "type": "potato_farm",
        "notes": "77 years; 50+ varieties; CCOF + Idaho Blue Tag; 5000+ acres; bulk 50lb bags; free ship; bulk discount 500+ lb; Parkinson family; Russet Burbank, Yukon Gold, fingerlings, heirloom",
        "production": "77 years; 5000+ acres; Idaho Falls ID",
        "prices": "50+ varieties; bulk 50lb+; free ship; discount 500+ lb",
        "certification": "certified_organic",
        "source": "web", "source_url": "https://www.grandtetonorganics.com/",
    },
    {
        "name": "Sprout Mountain Farms",
        "city": "Kingsport", "state": "TN",
        "url": "https://www.sproutmountainfarms.com/",
        "website": "https://www.sproutmountainfarms.com/",
        "buy_link": "https://www.sproutmountainfarms.com/store",
        "phone": "252-292-8271",
        "email": "growersupport@sproutmountainfarms.com",
        "type": "potato_farm",
        "notes": "Certified organic seed potatoes + sweet potato slips; East TN; ships from NC; variety mixes; filter by season; PO Box 5235 Kingsport TN; M-F 9-5",
        "production": "East TN; ships from NC",
        "prices": "Seed potatoes $29-$125; variety mixes",
        "certification": "certified_organic",
        "source": "web", "source_url": "https://www.sproutmountainfarms.com/",
    },
    {
        "name": "Ronnigers Organics",
        "city": "Moyie Springs", "state": "ID",
        "url": "https://www.ronnigersorganics.com/",
        "website": "https://www.ronnigersorganics.com/",
        "buy_link": "https://www.ronnigersorganics.com/",
        "phone": "208-627-8181",
        "email": "ronnigersorganics@gmail.com",
        "type": "potato_farm",
        "notes": "David Ronniger founded first organic seed potato catalog; 200+ varieties; seed potatoes + root crops; 7312 Perkins Lake Rd Moyie Springs ID; farm store daylight hours; Sandpoint Farmers Market Sa Aug-Oct; Real Organic Project certified",
        "production": "100,000+ lbs produce/yr; root cellar storage",
        "prices": "Seed potatoes; farm store + farmers market",
        "certification": "certified_organic",
        "source": "web", "source_url": "https://www.ronnigersorganics.com/",
    },
    {
        "name": "Jones Farms Organics",
        "city": "Hooper", "state": "CO",
        "url": "http://www.jonesfarmsorganics.com/",
        "website": "http://www.jonesfarmsorganics.com/",
        "buy_link": "http://www.jonesfarmsorganics.com/",
        "phone": "719-378-2299",
        "email": "organics@jonesfarmsorganics.com",
        "type": "potato_farm",
        "notes": "4th generation since 1925; organic since 2005; 600 acres San Luis Valley; nutrient-dense; organic potatoes; 11221 E County Rd 110 N Hooper CO; sustainable soil health",
        "production": "600 acres; 4th generation; San Luis Valley CO",
        "prices": "Contact for direct sales",
        "certification": "certified_organic",
        "source": "web", "source_url": "http://www.jonesfarmsorganics.com/",
    },
    {
        "name": "Fresh by 4Roots",
        "city": "Orlando", "state": "FL",
        "url": "https://freshby4roots.com/",
        "website": "https://freshby4roots.com/",
        "buy_link": "https://freshby4roots.com/products/organic-red-potatoes",
        "type": "potato_farm",
        "notes": "4Roots Farm Campus; 57 FL producers; USDA organic red potatoes $2.99/lb; tri-color $5.25/lb; 1918 W Princeton St Orlando pickup Tu-F 10-3; 2nd Sat farmers market; 15% off first order",
        "production": "4Roots Farm Campus; Orlando FL",
        "prices": "Organic red $2.99/lb; tri-color $5.25/lb; subscribe 15% off",
        "certification": "certified_organic",
        "source": "web", "source_url": "https://freshby4roots.com/",
    },
    {
        "name": "Enka:ri Farm",
        "city": "Marion", "state": "NY",
        "url": "https://enkarifarm.com/",
        "website": "https://enkarifarm.com/",
        "buy_link": "https://enkarifarm.com/membership/",
        "phone": "315-333-2594",
        "email": "jennie.brant@gmail.com",
        "type": "potato_farm",
        "notes": "Certified organic CSA; 30 acres; no-till; Walworth-Marion Rd Marion NY; seasonal produce including potatoes; $100 membership + 5 free bags; Th 3-6pm pickup; SNAP/EBT accepted",
        "production": "30 acres; no-till; Marion NY",
        "prices": "CSA $100 membership; 5 free bags; SNAP no fee",
        "certification": "certified_organic",
        "source": "web", "source_url": "https://enkarifarm.com/",
    },
    {
        "name": "Dynamite Harvest",
        "city": "Greenwood", "state": "WI",
        "url": "https://dynamiteharvest.com/",
        "website": "https://dynamiteharvest.com/",
        "buy_link": "https://dynamiteharvest.com/product/bulk-potatoes-naturally-grown-freshly-dug-50-pounds",
        "phone": "715-727-3386",
        "email": "tntharvest@gmail.com",
        "type": "potato_farm",
        "notes": "CHEAPEST: 50lb bulk $50 ($1/lb!!!); naturally grown, organically-approved methods; Austrian Crescent fingerlings, German Butterball, Dark Red Norland, Kennebec, Adirondack Red/Blue; free delivery 10mi Greenwood WI; Tu/F 9am-noon pickup",
        "production": "Family farm; Greenwood WI",
        "prices": "50lb $50 ($1/lb); free delivery 10mi",
        "certification": "organic",
        "source": "web", "source_url": "https://dynamiteharvest.com/",
    },
    {
        "name": "Bibb Forest Farm",
        "city": "Louisa", "state": "VA",
        "url": "https://bibbforestfarm.com/",
        "website": "https://bibbforestfarm.com/",
        "buy_link": "https://bibbforestfarm.com/product/bulk-potatoes",
        "phone": "804-240-5797",
        "email": "info@bibbforestfarm.com",
        "type": "potato_farm",
        "notes": "CCOF certified organic; regenerative; bulk 4.5lb $12 ($2.67/lb); Red Gold 1.5lb $6.50; Mountain Rose 1.5lb $6.50; 3320 Bibb Store Rd Louisa VA; online store Th 8pm-Mon; Charlottesville/Richmond delivery; Charlottesville City Market",
        "production": "Regenerative organic; Louisa VA",
        "prices": "Bulk 4.5lb $12 ($2.67/lb); 1.5lb bags $6.50",
        "certification": "certified_organic",
        "source": "web", "source_url": "https://bibbforestfarm.com/",
    },
    {
        "name": "Willow Pond Farm",
        "city": "Sabattus", "state": "ME",
        "url": "https://www.willowpf.com/",
        "website": "https://willowpf.csaware.com/",
        "buy_link": "https://willowpf.csaware.com/winter-2025-2026-C29431",
        "phone": "207-375-6662",
        "email": "Willowpondfarm89@gmail.com",
        "type": "potato_farm",
        "notes": "First CSA in Maine 1989; MOFGA/USDA certified organic; winter CSA $100 half share, $160 full; storage crops potatoes onions carrots garlic cabbage squash; 395 Middle Rd Sabattus ME",
        "production": "Est. 1989; first Maine CSA",
        "prices": "Winter CSA half $100; full $160; potatoes in storage share",
        "certification": "certified_organic",
        "source": "web", "source_url": "https://www.willowpf.com/",
    },
    {
        "name": "House in the Woods Farm",
        "city": "Adamstown", "state": "MD",
        "url": "https://houseinthewoods.com/",
        "website": "https://houseinthewoods.com/",
        "buy_link": "https://houseinthewoods.csaware.com/store",
        "phone": "301-461-6575",
        "email": "ilene@houseinthewoods.com",
        "type": "potato_farm",
        "notes": "25 yrs certified organic CSA; 7mi S Frederick; potatoes sweet potatoes heirloom varieties; $38/wk full 24wk or $24/wk half; Phil & Ilene Freedman; U-Pick farm activities",
        "production": "25 years; Adamstown MD",
        "prices": "CSA $38/wk full; $24/wk half; May-Oct",
        "certification": "certified_organic",
        "source": "web", "source_url": "https://houseinthewoods.com/",
    },
    {
        "name": "Soda Springs Solar Gardens",
        "city": "Soda Springs", "state": "ID",
        "url": "https://www.seed-potatoes.com/",
        "website": "https://www.seed-potatoes.com/",
        "buy_link": "https://www.seed-potatoes.com/certified-potato-seed",
        "type": "potato_farm",
        "notes": "Organic certification expected spring 2026; FY1 certified seed; fingerlings colored specialty; gravity drip; no pesticides/chemicals; regenerative no-till; Jester $12/lb; ships lower 48 USPS",
        "production": "Small ID farm; organic cert 2026",
        "prices": "Seed potatoes from $12/lb; ships lower 48",
        "certification": "certified_organic",
        "source": "web", "source_url": "https://www.seed-potatoes.com/",
    },
    {
        "name": "Viva Farms",
        "city": "Burlington", "state": "WA",
        "url": "https://vivafarms.org/",
        "website": "https://vivafarms.org/",
        "buy_link": "https://vivafarms.org/contact/",
        "phone": "360-969-7191",
        "type": "potato_farm",
        "notes": "Non-profit farm business incubator; certified organic; Skagit + King County; CSA wholesale farm-to-school; 15366 Ovenell Rd Burlington WA; independent farmers grow organic produce",
        "production": "Farm incubator; Burlington WA",
        "prices": "Contact for CSA/wholesale",
        "certification": "certified_organic",
        "source": "web", "source_url": "https://vivafarms.org/",
    },
    {
        "name": "Ten Fold Farm",
        "city": "Bellingham", "state": "WA",
        "url": "https://www.tenfoldfarm.com/",
        "website": "https://www.tenfoldfarm.com/",
        "buy_link": "https://www.tenfoldfarm.com/shop",
        "phone": "360-220-7391",
        "type": "potato_farm",
        "notes": "Certified Naturally Grown; 120+ heirloom varieties; GMO-free seeds; no chemicals; Whatcom County delivery/pickup; Fri 3-6pm farm pickup; subscription boxes",
        "production": "Family farm; Bellingham WA",
        "prices": "Contact for produce boxes; CSA temp canceled",
        "certification": "organic",
        "source": "web", "source_url": "https://www.tenfoldfarm.com/",
    },
    {
        "name": "Wild Hare Organic Farm",
        "city": "Tacoma", "state": "WA",
        "url": "https://www.wildhareorganicfarm.com/",
        "website": "https://www.wildhareorganicfarm.com/",
        "buy_link": "https://www.wildhareorganicfarm.com/what-is-a-csa",
        "phone": "253-778-6257",
        "email": "info@wildhareorganicfarm.com",
        "type": "potato_farm",
        "notes": "Year-round organic CSA; 4 seasons; large $35/wk small $25/wk; 10% full-year discount; 4520 River Rd E Tacoma; Tu/W/Sa pickup; 10% farm stand discount; Katie & Mark Green",
        "production": "Family farm; Tacoma WA",
        "prices": "CSA large $35/wk; small $25/wk; 10% full-year off",
        "certification": "certified_organic",
        "source": "web", "source_url": "https://www.wildhareorganicfarm.com/",
    },
    {
        "name": "Farm on the River",
        "city": "Springfield", "state": "VT",
        "url": "https://www.farmontheriver.com/",
        "website": "https://www.farmontheriver.com/",
        "buy_link": "https://www.farmontheriver.com/csa-2025",
        "phone": "802-881-0234",
        "email": "hello@farmontheriver.com",
        "type": "potato_farm",
        "notes": "30+ yrs USDA certified organic CSA; 8-11 veggies/week; potatoes mid-Oct gourmet European reds/yellows; $37.50/wk 22wk or $38.36 bi-weekly; 987 Connecticut River Rd Springfield VT; pickup VT or Walpole NH",
        "production": "30+ years; Springfield VT",
        "prices": "CSA $37.50/wk; $850 full season; potatoes from mid-Oct",
        "certification": "certified_organic",
        "source": "web", "source_url": "https://www.farmontheriver.com/",
    },
    {
        "name": "Tolt River Farm",
        "city": "Carnation", "state": "WA",
        "url": "https://www.localharvest.org/tolt-river-farm-M10301",
        "website": "https://toltriverfarm.com/",
        "phone": "425-333-6886",
        "type": "potato_farm",
        "notes": "Certified organic; potatoes arugula beets broccoli cabbage carrots garlic kale lettuce spinach; FarmGirl collective CSA $450 18wk Jun-Oct; pickup Wallingford Phinney Ridge Ballard farmers markets; 5405 Tolt River Rd NE Carnation WA",
        "production": "Small organic farm; Carnation WA",
        "prices": "CSA $450 18 weeks; Jun-Oct",
        "certification": "certified_organic",
        "source": "web", "source_url": "https://www.localharvest.org/tolt-river-farm-M10301",
    },
    {
        "name": "Flatwater Farms",
        "city": "Buchanan", "state": "MI",
        "url": "https://www.flatwaterfarms.com/",
        "website": "https://www.flatwaterfarms.com/",
        "buy_link": "https://www.flatwaterfarms.com/csa-signup",
        "type": "potato_farm",
        "notes": "USDA certified organic; 40+ varieties potatoes sweet potatoes carrots beets beans; CSA $400-$480; Green City Market Chicago Sat; farm stand Buchanan Tue 4-6 Sat 11-2; 15475 Walton Rd Buchanan MI; Chicago delivery",
        "production": "Certified organic; Buchanan MI",
        "prices": "CSA $400-$480; market style",
        "certification": "certified_organic",
        "source": "web", "source_url": "https://www.flatwaterfarms.com/",
    },
    {
        "name": "Growing Family Farms",
        "city": "Spencerport", "state": "NY",
        "url": "https://www.growingfamilyfarms.com/",
        "website": "https://www.growingfamilyfarms.com/",
        "phone": "585-301-5926",
        "email": "growingfamilyfarms@gmail.com",
        "type": "potato_farm",
        "notes": "USDA certified organic 6 acres; vegetables fruits eggs chicken; CSA 12wk Jun-Aug + extended Sep-Nov; pickup Hilton Rochester Brighton; 602 Peck Rd Spencerport NY",
        "production": "6 acres certified organic; Spencerport NY",
        "prices": "CSA 12wk main + 10wk extended; contact for pricing",
        "certification": "certified_organic",
        "source": "web", "source_url": "https://www.localharvest.org/growing-family-farms-M67938",
    },
    {
        "name": "Miolea Organic Farm",
        "city": "Adamstown", "state": "MD",
        "url": "https://www.mioleafarm.com/",
        "website": "https://www.mioleafarm.com/",
        "phone": "301-437-8958",
        "email": "Miolea@aol.com",
        "type": "potato_farm",
        "notes": "USDA certified organic since 2007; 183 yrs working farm; Caribou Russet potatoes Aug; by appointment; Catoctin Mountain foothills Frederick County",
        "production": "183 years; Frederick County MD",
        "prices": "Contact for availability; potatoes from Aug",
        "certification": "certified_organic",
        "source": "web", "source_url": "https://www.mioleafarm.com/",
    },
    {
        "name": "Uncommon Acres",
        "city": "Firth", "state": "ID",
        "url": "https://www.localharvest.org/uncommon-acres-M74238",
        "website": "https://www.localharvest.org/uncommon-acres-M74238",
        "type": "potato_farm",
        "notes": "3-acre organic farm since 2015; organic seeds pesticide-free; potatoes beets carrots beans greens; CSA $85/mo half-bushel Wed delivery Idaho Falls late May-Oct",
        "production": "3 acres; Firth ID",
        "prices": "CSA $85/mo; late May-Oct",
        "certification": "organic",
        "source": "web", "source_url": "https://www.localharvest.org/uncommon-acres-M74238",
    },
    {
        "name": "Lake Breeze Organics",
        "city": "Benton Harbor", "state": "MI",
        "url": "https://www.localharvest.org/lake-breeze-organics-M26604",
        "website": "https://lakebreezeorganics.com/",
        "phone": "269-762-0992",
        "type": "potato_farm",
        "notes": "Certified organic; potatoes carrots broccoli onions garlic; CSA $550 Jun-Sep; Chicago Evanston Stevensville pickup; Evanston farmers market Sat; heirloom tomatoes 50+ varieties",
        "production": "Certified organic; Benton Harbor MI",
        "prices": "CSA $550 full share; Jun-Sep",
        "certification": "certified_organic",
        "source": "web", "source_url": "https://www.localharvest.org/lake-breeze-organics-M26604",
    },
    {
        "name": "Alcantar Organics",
        "city": "Carpinteria", "state": "CA",
        "url": "https://www.localharvest.org/alcantar-organics-M78187",
        "website": "https://www.localharvest.org/alcantar-organics-M78187",
        "type": "potato_farm",
        "notes": "Santa Barbara County certified organic; year-round CSA $30/wk no minimum; Sherman Oaks Thousand Oaks Ventura Malibu Brentwood pickup; supplies schools restaurants farmers markets",
        "production": "Certified organic; Carpinteria CA",
        "prices": "CSA $30/wk; year-round",
        "certification": "certified_organic",
        "source": "web", "source_url": "https://www.localharvest.org/alcantar-organics-M78187",
    },
    {
        "name": "Lakestone Family Farm",
        "city": "Farmington", "state": "NY",
        "url": "https://www.localharvest.org/lakestone-family-farm-M62964",
        "website": "https://lakestonefamilyfarm.com/",
        "type": "potato_farm",
        "notes": "Certified organic Finger Lakes; CSA market-pick style; large $600/20wk small $400/20wk; Brighton Canandaigua farmers markets; summer fall shares; 50 shares",
        "production": "Family farm since 2011; Farmington NY",
        "prices": "CSA large $600 small $400; 20 weeks",
        "certification": "certified_organic",
        "source": "web", "source_url": "https://www.localharvest.org/lakestone-family-farm-M62964",
    },
    {
        "name": "Full Circle Farm",
        "city": "Three Rivers", "state": "MI",
        "url": "https://www.localharvest.org/full-circle-farm-M73164",
        "website": "https://www.fullcircle.farm/",
        "type": "potato_farm",
        "notes": "Certified Naturally Grown; regenerative; carrots beans garlic leeks microgreens mushrooms; CSA 7-9 items Jun-Oct + fall/winter; HUSS Portage farmers markets; 50 shares",
        "production": "Certified Naturally Grown; Three Rivers MI",
        "prices": "CSA main + fall/winter; contact for pricing",
        "certification": "organic",
        "source": "web", "source_url": "https://www.localharvest.org/full-circle-farm-M73164",
    },
    {
        "name": "Long Valley Farm",
        "city": "Kalamazoo", "state": "MI",
        "url": "https://www.localharvest.org/long-valley-farm-M45461",
        "website": "https://www.longvalleyfarm.com/",
        "phone": "269-903-7706",
        "type": "potato_farm",
        "notes": "Regenerative sustainable chemical-free; 18wk CSA Jun-mid-Oct single 5 items family 10 items; Kalamazoo Farmers Market Sat/Tue; SNAP $6/wk; 1616 Alamo Ave Wed pickup",
        "production": "Under 2 acres; east Kalamazoo",
        "prices": "CSA 18wk; SNAP $6/wk available",
        "certification": "organic",
        "source": "web", "source_url": "https://www.localharvest.org/long-valley-farm-M45461",
    },
    {
        "name": "Wiley Veggie Shed & Farm",
        "city": "Schoolcraft", "state": "MI",
        "url": "https://www.localharvest.org/wiley-veggie-shed-farm-M62651",
        "website": "https://www.localharvest.org/wiley-veggie-shed-farm-M62651",
        "phone": "269-679-5511",
        "type": "potato_farm",
        "notes": "Family farm since 1956; high tunnels extend season; U-Pick farm stand; 1335 W U Ave Schoolcraft MI; contact for organic potato availability",
        "production": "Family farm since 1956; Schoolcraft MI",
        "prices": "Contact for farm stand pricing",
        "certification": "",
        "source": "web", "source_url": "https://www.localharvest.org/wiley-veggie-shed-farm-M62651",
    },
]
# ---------------------------------------------------------------------------
# Processors and retailers
# ---------------------------------------------------------------------------
POTATO_PROCESSORS = [
    {
        "name": "EarthFresh (New Crop Organics)",
        "city": "", "state": "",
        "url": "https://www.earthfreshfoods.com/",
        "website": "https://www.earthfreshfoods.com/",
        "buy_link": "https://www.earthfreshfoods.com/newcroporganics/",
        "phone": "800-565-4915",
        "email": "info@earthfreshfoods.com",
        "type": "potato_processor",
        "notes": "Southern organic potatoes; red, yellow, russet, mini; 1.5-10 lb packs; Pro-Cert + USDA organic; Burlington ON, Houston TX, Idaho Falls ID; year-round retail packs",
        "production": "Multi-facility; 600K lb/day capacity Burlington",
        "prices": "1.5-10 lb packs; retail distribution",
        "certification": "certified_organic",
        "source": "web", "source_url": "https://www.earthfreshfoods.com/",
    },
    {
        "name": "Long Acres Potato Farms",
        "city": "Tionesta", "state": "PA",
        "url": "https://longacresfarms.com/",
        "website": "https://longacresfarms.com/",
        "phone": "814-744-8454",
        "email": "laaron@longacresfarms.com",
        "type": "potato_processor",
        "notes": "Bulk wholesale; table stock potatoes; 4th gen family farm; contact for organic availability; Tionesta PA",
        "production": "4th generation; Tionesta PA",
        "prices": "Contact for bulk wholesale",
        "certification": "",
        "source": "web", "source_url": "https://longacresfarms.com/",
    },
]
POTATO_WHOLESALE = [
    {
        "name": "Regional Access (Williams Farms)",
        "city": "Marion", "state": "NY",
        "url": "https://regionalaccess.net/",
        "website": "https://regionalaccess.net/",
        "phone": "607-319-5150",
        "email": "info@regionalaccess.net",
        "type": "potato_wholesale",
        "notes": "Williams Farms organic 50lb red; 750 acres USDA organic; Marion NY; Regional Access distributes; contact for price",
        "production": "Williams Farms 750 acres organic; Marion NY",
        "prices": "50lb organic red; contact for price",
        "certification": "certified_organic",
        "source": "web", "source_url": "https://regionalaccess.net/",
    },
    {
        "name": "Alsum Farms",
        "city": "Friesland", "state": "WI",
        "url": "https://www.alsum.com/",
        "website": "https://www.alsum.com/",
        "phone": "920-348-5127",
        "email": "sales@Alsum.com",
        "type": "potato_wholesale",
        "notes": "50lb organic russet red gold; food service wholesale; Friesland WI; contact for pricing",
        "production": "WI potato grower; Friesland",
        "prices": "50lb organic russet/red/gold; contact for price",
        "certification": "certified_organic",
        "source": "web", "source_url": "https://www.alsum.com/",
    },
    {
        "name": "Pacific Coast Fresh",
        "city": "", "state": "",
        "url": "https://www.pcfreshco.com/",
        "website": "https://www.pcfreshco.com/",
        "buy_link": "https://www.pcfreshco.com/vegetables/potato/",
        "phone": "800-423-4945",
        "type": "potato_wholesale",
        "notes": "50lb organic red gold potatoes; wholesale food service; account required for pricing; ships",
        "production": "Wholesale produce distributor",
        "prices": "50lb organic red/gold; contact for price",
        "certification": "certified_organic",
        "source": "web", "source_url": "https://www.pcfreshco.com/",
    },
]
POTATO_RETAILERS = [
    {
        "name": "Lancaster Farm Fresh Cooperative",
        "city": "", "state": "PA",
        "url": "https://lancasterfarmfresh.com/",
        "website": "https://lancasterfarmfresh.com/",
        "buy_link": "https://lancasterfarmfresh.com/csa-store/organic-gold-potatoes-10-lbs/",
        "phone": "717-656-3533",
        "email": "csa@lancasterfarmfresh.com",
        "type": "potato_retailer",
        "notes": "CHEAP CERTIFIED ORGANIC: 90+ certified organic PA farms; organic gold potatoes 10lb $17.99 ($1.80/lb); non-profit cooperative; Lancaster/Chester counties; CSA + add-ons; order deadlines by pickup day",
        "production": "90+ certified organic farms; PA cooperative",
        "prices": "Organic gold 10lb $17.99 ($1.80/lb); sweet potatoes 10lb $21.99",
        "certification": "certified_organic",
        "source": "web", "source_url": "https://lancasterfarmfresh.com/",
    },
    {
        "name": "Chatham Farm Supply (Country Farm & Home)",
        "city": "Pittsboro", "state": "NC",
        "url": "https://chathamfarmsupply.com/",
        "website": "https://chathamfarmsupply.com/",
        "buy_link": "https://chathamfarmsupply.com/seasonal-orders/2026-organic-seed-potato-orders-open",
        "type": "potato_retailer",
        "notes": "Organic seed potatoes from Grand Teton Organics; 40+ varieties; 2026 orders open; 50% deposit 50+ lb; Carolina delivery routes; Yukon Baby, Masquerade, Purple Violet fingerling",
        "production": "Farm supply; Pittsboro NC",
        "prices": "Seasonal; 40 varieties; 50% deposit 50+ lb",
        "certification": "certified_organic",
        "source": "web", "source_url": "https://chathamfarmsupply.com/",
    },
    {
        "name": "Good Box Organics",
        "city": "Granada Hills", "state": "CA",
        "url": "https://goodboxorganics.com/",
        "website": "https://goodboxorganics.com/",
        "buy_link": "https://goodboxorganics.com/order",
        "email": "goodboxorganics@gmail.com",
        "type": "potato_retailer",
        "notes": "100% organic LA area delivery; produce boxes $20.95-$55.95; potatoes in seasonal boxes; Granada Hills CA",
        "production": "Organic delivery; LA area",
        "prices": "Boxes $20.95-$55.95; potatoes in seasonal mix",
        "certification": "certified_organic",
        "source": "web", "source_url": "https://goodboxorganics.com/",
    },
    {
        "name": "Costco",
        "city": "", "state": "",
        "url": "https://www.costco.com/",
        "website": "https://www.costco.com/",
        "type": "potato_retailer",
        "notes": "Membership required; organic gold 10lb ~$5-8; organic russet 10lb ~$3-8; location-dependent; limited stock at some warehouses",
        "production": "National warehouse club",
        "prices": "Organic 10lb ~$3-8; varies by location",
        "certification": "certified_organic",
        "source": "web", "source_url": "https://www.costco.com/",
    },
    {
        "name": "Aldi",
        "city": "", "state": "",
        "url": "https://www.aldi.us/",
        "website": "https://www.aldi.us/",
        "type": "potato_retailer",
        "notes": "Retail; Simply Nature organic yellow potatoes; organic sweet potatoes; prices vary by region",
        "production": "National discount grocer",
        "prices": "Organic yellow ~$3.49-3.99; varies by location",
        "certification": "certified_organic",
        "source": "web", "source_url": "https://www.aldi.us/",
    },
    {
        "name": "Sam's Club",
        "city": "", "state": "",
        "url": "https://www.samsclub.com/",
        "website": "https://www.samsclub.com/",
        "buy_link": "https://www.samsclub.com/p/organic-potatoes-5-lbs/prod4500238",
        "type": "potato_retailer",
        "notes": "Membership required; organic potatoes 5lb; organic sweet potatoes 5lb ~$5.86; organic fingerling 5lb; availability varies",
        "production": "National warehouse club",
        "prices": "Organic 5lb; sweet potato 5lb ~$5.86",
        "certification": "certified_organic",
        "source": "web", "source_url": "https://www.samsclub.com/",
    },
    {
        "name": "Good Eggs",
        "city": "San Francisco", "state": "CA",
        "url": "https://www.goodeggs.com/",
        "website": "https://www.goodeggs.com/",
        "buy_link": "https://www.goodeggs.com/produce/potatoes",
        "type": "potato_retailer",
        "notes": "Bulk organic russet 3lb 5lb; CA Bay Area delivery; local farmers Veritable Vegetable; multiple delivery days",
        "production": "Online grocery; CA delivery",
        "prices": "Bulk organic russet 3lb 5lb; browse for current",
        "certification": "certified_organic",
        "source": "web", "source_url": "https://www.goodeggs.com/",
    },
]
# ---------------------------------------------------------------------------
# Associations
# ---------------------------------------------------------------------------
POTATO_ASSOCIATIONS = [
    {
        "name": "National Potato Council",
        "city": "Washington", "state": "DC",
        "url": "https://www.nationalpotatocouncil.org/",
        "website": "https://www.nationalpotatocouncil.org/",
        "phone": "202-682-9456",
        "email": "info@nationalpotatocouncil.org",
        "type": "association",
        "notes": "Founded 1948; national advocacy for US potato growers; policy, trade, research, labor; 50 F St NW Suite 900 Washington DC",
        "production": "National advocacy; DC",
        "source": "web", "source_url": "https://www.nationalpotatocouncil.org/",
    },
    {
        "name": "Potatoes USA",
        "city": "Denver", "state": "CO",
        "url": "https://potatoesusa.com/",
        "website": "https://potatoesusa.com/",
        "phone": "303-369-7783",
        "email": "Media@PotatoesUSA.com",
        "type": "association",
        "notes": "Certified seed grower directory; state programs AK CA CO ID ME MI MN MT NY ND OR WA WI; 3675 Wynkoop St Denver CO",
        "production": "National potato board; Denver CO",
        "source": "web", "source_url": "https://potatoesusa.com/",
    },
]


class PotatoSource:
    """USA organic potato industry sources - farms, processors, retailers."""

    def __init__(self):
        pass

    def _yield_enriched(self, items: list, default_prices: str = "Contact for pricing") -> Iterator[dict]:
        for r in items:
            yield _enrich_record(r, default_prices)

    def fetch_all(self) -> Iterator[dict]:
        """Yield all potato sources."""
        for r in self._yield_enriched(POTATO_ORGANIC_FARMS):
            yield r
        for r in self._yield_enriched(POTATO_WHOLESALE):
            yield r
        for r in self._yield_enriched(POTATO_PROCESSORS):
            yield r
        for r in self._yield_enriched(POTATO_RETAILERS):
            yield r
        for r in self._yield_enriched(POTATO_ASSOCIATIONS):
            yield r

    def fetch_organic(self) -> Iterator[dict]:
        """Yield only certified organic sources."""
        for r in self.fetch_all():
            if r.get("certification") == "certified_organic":
                yield r

    def fetch_farms(self) -> Iterator[dict]:
        yield from self._yield_enriched(POTATO_ORGANIC_FARMS)

    def fetch_processors(self) -> Iterator[dict]:
        yield from self._yield_enriched(POTATO_PROCESSORS)

    def fetch_retailers(self) -> Iterator[dict]:
        yield from self._yield_enriched(POTATO_RETAILERS)

    def fetch_associations(self) -> Iterator[dict]:
        yield from self._yield_enriched(POTATO_ASSOCIATIONS)

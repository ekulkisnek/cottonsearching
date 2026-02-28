# Buyable Cotton & Apparel Sources – Data Collection

All valid options from these directories, with contact data (email, phone, website, buy_link, prices).

## Primary Sources

| Source | URL | Coverage | Notes |
|-------|-----|----------|-------|
| **Cotton Incorporated** | https://www.cottoninc.com/quality-products/textile-sourcing/cut-and-sew/ | Cut & sew by state | Filter: Apparel, CMT, Denim, Home, Knits, Uniforms, Wovens |
| **CottonWorks** | https://cottonworks.com/sourcing/find-us-suppliers/ | U.S. Supplier List PDF | Spinners, knitters, weavers, dyers, cut & sew |
| **CFDA Production Directory** | https://cfda.com/resources/supply-chain-manufacturing/production-directory | 380+ U.S. fashion manufacturers | Filter by category, location, minimums |
| **Textile Connect** | https://textileconnect.com/directory/ | 855 apparel/product mfg | 186 cut & sew mfg, 115 contractors; strong NC |
| **ManufacturedNC** | https://www.manufacturednc.com/ | 199 NC manufacturers | Search NAICS 313, 314, 315 |
| **NCTO** | https://ncto.org/about/members/ | Textile industry members | Finished Textile & Apparel council |
| **Makers Row** | https://app.makersrow.com/ | 3000+ USA manufacturers | Cut & sew, apparel; requires signup to message |

## Contact Fields (per record)

- `email` – primary contact email
- `phone` – main phone
- `website` – company website
- `buy_link` – where to purchase / contact for quote
- `prices` – "Contact for quote", "See website", or specific info

## Scraping (bulk import)

```bash
# Scrape all USA directories (Textile Connect, Cotton Inc, CFDA, ManufacturedNC, NCTO, CottonWorks PDF)
python scripts/scrape_all_usa.py --output data/scraped_usa.csv

# Include CottonWorks PDF (downloads and parses U.S. Supplier List)
python scripts/scrape_all_usa.py --sources textile,cotton,cfda,mnc,ncto,cottonworks --output data/scraped_usa.csv

# Quick test (limited pages)
python scripts/scrape_all_usa.py --quick --output data/scraped_usa_quick.csv

# Merge scraped data with existing buyable
python scripts/merge_scraped_into_buyable.py --output data/buyable_merged.csv

# Fetch buyable with scraped data included
python -m src.cli fetch-buyable --include-scraped --output data/buyable_all.csv

## Products enrichment

Add what each company produces/sells. Scrapers now capture:
- **Textile Connect**: Category + excerpt (e.g. "Textile Manufacturing; Embroidery")
- **Cotton Inc**: Product types (Apparel, CMT, Denim, Home, Knits, Uniforms, Wovens)
- **CottonWorks PDF**: Capabilities from listing
- **CFDA**: Products, Services, Categories from detail pages
- **NCTO**: Council type (Yarn, Fabric, Finished Textile & Apparel)
- **ManufacturedNC**: Apparel; Textiles

Enrich from company websites when products is empty:
```bash
python scripts/enrich_products.py --input data/buyable_merged.csv --output data/buyable_with_products.csv
```

## Price enrichment

Check each manufacturer website for price info (MOQ, $ amounts, wholesale, etc.):

```bash
python scripts/enrich_prices.py --input data/buyable_merged.csv --output data/buyable_with_prices.csv

# Test with first 20 records
python scripts/enrich_prices.py --limit 20 --delay 1.5
```
```

## Export

```bash
python -m src.cli fetch-buyable --output data/buyable.csv
python scripts/collect_buyable_sources.py  # writes data/buyable_all.csv
```

## Cut & Sew Only

```bash
python -m src.cli fetch-buyable --type cut_and_sew --output data/cut_and_sew.csv
```

# USA Wool Industry Data Sources

Complete list from growers to fabric makers to manufacturers.

## Pipeline

```bash
# 1. Scrape wool directories
python scripts/scrape_all_wool.py -o data/scraped_wool.csv

# 2. Merge with curated wool sources
python scripts/merge_scraped_into_wool.py -o data/wool_merged.csv

# 3. (Optional) Enrich products/production from websites
python scripts/enrich_products_wool.py -i data/wool_merged.csv -o data/wool_with_products.csv

# 4. Fetch via CLI
python -m src.cli fetch-wool --include-scraped -o data/wool_full.csv
```

## Sources

### Curated (in src/sources/wool.py)

- **Wool buyers** – ASI directory: 25+ buyers across CA, TX, MT, ME, MA, NC, SC, SD, OR, PA, RI, UT, VA, WY
- **Large processors** – American Woolen, Mill Wool, Crescent Woolen Mills, Kentwool, Carolina Mills, Pendleton
- **Direct sale** – Ramblers Way (traceable American wool apparel)
- **Additional mills** – Zeilinger Wool (MI), Mendocino Wool and Fiber (CA)
- **Associations** – ASI, American Wool, National Mill Inventory, Wool and Fiber Arts

### Scraped

- **ASI (American Sheep Industry)** – sheepusa.org/contacts/wool-pelt
  - Wool buyers
  - Small & midsize mills (scouring, carding, spinning, dyeing, felting, etc.)
- **Wool and Fiber Arts** – woolandfiberarts.com/pages/us-mill-directory
  - US Mill Directory by state
  - 100+ fiber mills (wool, alpaca, etc.)

## Types

| Type | Description |
|------|-------------|
| wool_buyer | Buy raw wool from growers |
| wool_mill | Process wool: yarn, roving, batting |
| wool_processor | Scouring, carding, spinning, dyeing |
| wool_fabric | Wool fabric; worsted; woolen |
| wool_apparel | Wool apparel; blankets; home goods |
| association | Industry directory |

## Related

- **National Mill Inventory** – nationalmillinventory.com (Fibershed)
- **American Wool** – americanwool.org (finished products)
- **Textile Connect** – textileconnect.com (includes wool manufacturers)

# Cotton Searching

Locate cotton growers in the USA by integrating all available data routes from USDA and industry sources. Also includes curated data for **organic potatoes**, **wool** (growers to fabric to clothing), **veal** (pasture-raised/grass-fed bones, tallow, suet), and **cotton** (buyable products, growers, ginners).

## Data Files (data/)

| File | Records | Description |
|------|---------|-------------|
| `buyable_merged.csv` | ~3,060 | Cotton products, t-shirts, fabric, manufacturers (merged) |
| `potatoes_merged.csv` | 41 | Organic potato farms, wholesalers, retailers, CSAs |
| `veal_merged.csv` | ~95 | Pasture-raised/grass-fed veal, beef bones, tallow, suet |
| `wool_merged.csv` | ~237 | Wool growers, fabric makers, clothing manufacturers |
| `cotton_complete.csv` | ~510 | Cotton growers + gins + associations |
| `cotton_industry.csv` | ~95 | Cotton industry data |
| `wool_full.csv` | ~178 | Full wool dataset |
| `buyable_full.csv` | ~2,673 | Full buyable cotton products |
| `growers.csv` | ~191 | Cotton growers |
| `cut_and_sew.csv` | ~87 | Cut-and-sew manufacturers |
| `scraped_*.csv` | varies | Scraped data from various sources |

## Quick Start - Get Data Now

```bash
# Get 14 actual cotton growers (farm names from EWG subsidy data)
python -m src.cli fetch-growers --output cotton_growers.csv

# Get 260+ cotton gins and cooperatives (cottongins.org + FSA)
python -m src.cli fetch-ginners --output cotton_gins.csv

# Get everything: growers + gins + associations (285+ entries)
python -m src.cli fetch-all --output cotton_complete.csv
```

**Data breakdown:**
- **14 growers** – Actual farm names (Parker Brothers Farm, Isbell Farms, Fann Farms, etc.) from EWG Farm Subsidy Database
- **252 gins/co-ops** – Full state lists from cottongins.org (AL, AZ, AR, CA, FL, GA, LA, MS, NC, OK, SC, TN, TX, VA)
- **19 associations** – State cotton producer associations

## Data Routes Implemented

| Route | Source | CLI Command | Notes |
|-------|--------|-------------|-------|
| 4 | Master Cotton Ginners List | `fetch-ginners` | **252 gins/co-ops** (cottongins.org) |
| EWG | Farm Subsidy Database | `fetch-growers` | **14 actual cotton growers** (farm names) |
| 8 | State Cotton Associations | `fetch-associations` | 19 state associations |
| 1 | FSA Farm Programs Payments | `fetch-fsa` | Grower names (requires manual Excel download) |
| 5 | NASS QuickStats API | `fetch-nass` | County/state stats (requires API key) |

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

For NASS QuickStats API (optional):
1. Get API key at https://quickstats.nass.usda.gov/api/
2. Set `NASS_API_KEY` environment variable

## Usage

### Fetch cotton growers from FSA (primary source)

```bash
# Download FSA payment files and filter for cotton (2024 data)
python -m src.cli fetch-fsa --year 2024 --output cotton_growers.csv

# Test with single file first (faster)
python -m src.cli fetch-fsa --year 2023 --limit 1 --output growers.csv

# Use cached files only (after manual or prior download)
python -m src.cli fetch-fsa --no-download --output growers.csv

# 2023 files (direct .xlsx URLs, ~12-37MB each)
python -m src.cli fetch-fsa --year 2023 --output growers.csv
```

Note: FSA files are large (12-40MB each). For slow connections, download manually from [FSA Payment Files](https://www.fsa.usda.gov/tools/informational/freedom-information-act-foia/electronic-reading-room/frequently-requested/payment-files) into `data/fsa/`.

### Fetch NASS cotton statistics

```bash
export NASS_API_KEY=your_key_here
python -m src.cli fetch-nass --output cotton_stats.csv
```

### Fetch state associations

```bash
python -m src.cli fetch-associations --output associations.json
```

### Search cached growers

```bash
python -m src.cli search --state TX --name "Smith" --output results.csv
```

### Export cached data

```bash
python -m src.cli export --format json --output growers.json
```

## Data Sources

- **FSA Farm Programs Payments**: https://www.fsa.usda.gov/tools/informational/freedom-information-act-foia/electronic-reading-room/frequently-requested/payment-files
- **NASS QuickStats**: https://quickstats.nass.usda.gov/api (This product uses the NASS API but is not endorsed or certified by NASS.)
- **Master Cotton Ginners**: https://www.fsa.usda.gov/media/11107

## Cotton-Producing States (17)

Alabama, Arizona, Arkansas, California, Florida, Georgia, Kansas, Louisiana, Mississippi, Missouri, New Mexico, North Carolina, Oklahoma, South Carolina, Tennessee, Texas, Virginia

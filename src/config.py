"""Configuration for cotton grower data sources."""

import os

# Cotton-producing states (17) per USDA
COTTON_PRODUCING_STATES = [
    "Alabama", "Arizona", "Arkansas", "California", "Florida", "Georgia",
    "Kansas", "Louisiana", "Mississippi", "Missouri", "New Mexico",
    "North Carolina", "Oklahoma", "South Carolina", "Tennessee", "Texas", "Virginia"
]

# Keywords to identify cotton-related programs/commodities in FSA payment data
COTTON_KEYWORDS = [
    "cotton", "upland cotton", "upland", "pima cotton", "extra long staple",
    "els cotton", "cottonseed"
]

# FSA Payment Files base URL
FSA_PAYMENT_FILES_BASE = "https://www.fsa.usda.gov"

# NASS QuickStats API
NASS_API_BASE = "https://quickstats.nass.usda.gov/api"

# Data directory for cached downloads
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CACHE_DIR = os.path.join(DATA_DIR, "cache")

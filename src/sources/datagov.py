"""
Data.gov cotton datasets source.

Documents the Data.gov catalog for cotton-related federal datasets.
No programmatic API - use for discovery of additional data sources.

Source: https://catalog.data.gov/dataset?organization_type=Federal+Government&q=Cotton
"""

DATA_GOV_COTTON_URL = (
    "https://catalog.data.gov/dataset"
    "?organization_type=Federal+Government&q=Cotton"
)


class DataGovSource:
    """Data.gov cotton datasets - discovery/catalog reference."""

    def get_info(self) -> dict:
        """Return metadata about Data.gov cotton datasets."""
        return {
            "url": DATA_GOV_COTTON_URL,
            "description": "Federal government cotton-related datasets catalog",
            "use": "Discover additional cotton datasets (payments, production, etc.)",
            "source": "Data.gov",
        }

"""
NASS QuickStats API data source.

Fetches county/state-level cotton statistics (acreage, production) for
regional context and validation. Does not provide individual grower names.

Source: https://quickstats.nass.usda.gov/api
API Key: Required - get from https://quickstats.nass.usda.gov/api/
"""

import os
from typing import Iterator

import httpx

from ..config import COTTON_PRODUCING_STATES, NASS_API_BASE


class NASSSource:
    """NASS QuickStats API - cotton statistics by county/state."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("NASS_API_KEY", "")

    def _request(self, params: dict) -> dict:
        """Make API request to NASS QuickStats."""
        if not self.api_key:
            raise ValueError(
                "NASS API key required. Set NASS_API_KEY env var or pass api_key. "
                "Get key at https://quickstats.nass.usda.gov/api/"
            )
        params["key"] = self.api_key
        params["format"] = params.get("format", "JSON")
        with httpx.Client(timeout=60) as client:
            resp = client.get(f"{NASS_API_BASE}/api_GET", params=params)
            resp.raise_for_status()
            return resp.json()

    def get_counts(self, commodity_desc: str = "COTTON", year__ge: int = 2020) -> int:
        """Get record count before full query (max 50k per request)."""
        params = {
            "commodity_desc": commodity_desc,
            "year__GE": year__ge,
            "format": "JSON",
        }
        with httpx.Client(timeout=30) as client:
            resp = client.get(
                f"{NASS_API_BASE}/get_counts",
                params={**params, "key": self.api_key},
            )
            resp.raise_for_status()
            data = resp.json()
            return int(data.get("count", 0))

    def fetch_cotton_statistics(
        self,
        commodity_desc: str = "COTTON",
        years: list[int] | None = None,
        states: list[str] | None = None,
    ) -> Iterator[dict]:
        """
        Fetch cotton statistics (acreage, production) by state/county.

        Yields dicts with: state, county, year, statistic, value, unit, source
        """
        years = years or [2023, 2024]
        states = states or COTTON_PRODUCING_STATES

        for year in years:
            for state in states:
                state_alpha = self._state_to_alpha(state)
                if not state_alpha:
                    continue
                try:
                    data = self._request({
                        "commodity_desc": commodity_desc,
                        "year": year,
                        "state_alpha": state_alpha,
                        "format": "JSON",
                    })
                    for row in data.get("data", []):
                        yield {
                            "state": row.get("state_name", state),
                            "state_alpha": row.get("state_alpha", state_alpha),
                            "county": row.get("county_name", ""),
                            "year": row.get("year", year),
                            "statistic": row.get("statisticcat_desc", ""),
                            "short_desc": row.get("short_desc", ""),
                            "value": row.get("Value", ""),
                            "unit": row.get("unit_desc", ""),
                            "source": "NASS QuickStats",
                        }
                except Exception as e:
                    print(f"Warning: NASS query failed for {state} {year}: {e}")

    def _state_to_alpha(self, state: str) -> str | None:
        """Convert state name to 2-letter code."""
        state_map = {
            "alabama": "AL", "arizona": "AZ", "arkansas": "AR", "california": "CA",
            "florida": "FL", "georgia": "GA", "kansas": "KS", "louisiana": "LA",
            "mississippi": "MS", "missouri": "MO", "new mexico": "NM",
            "north carolina": "NC", "oklahoma": "OK", "south carolina": "SC",
            "tennessee": "TN", "texas": "TX", "virginia": "VA",
        }
        return state_map.get(state.lower().strip())

"""
State cotton producer association data source.

Integrates known state-level cotton associations. Most do not publish
public member directories; this module provides contact/organization
info for manual follow-up and documents available routes.

Source: NCC Certified Interest Orgs, plan Route 8
"""

from typing import Iterator

from ..config import COTTON_PRODUCING_STATES

# State cotton associations - org info (no public grower lists for most)
STATE_ASSOCIATIONS = {
    "Texas": [
        {"name": "Texas Cotton Association", "url": "https://www.tca-cotton.org/", "has_directory": True},
        {"name": "Texas Cotton Ginners' Association", "url": "https://www.tcga.org/", "has_directory": False},
    ],
    "Georgia": [
        {"name": "Georgia Cotton Commission", "url": "https://www.georgiacottoncommission.org/", "has_directory": False},
    ],
    "California": [
        {"name": "California Ginners and Growers Association", "location": "Fresno", "has_directory": False},
        {"name": "SJV Quality Cotton Growers Association", "location": "Stratford", "has_directory": False},
    ],
    "Alabama": [{"name": "Alabama Cotton Commission", "has_directory": False}],
    "Arizona": [{"name": "Arizona Cotton Growers Association", "has_directory": False}],
    "Arkansas": [{"name": "Arkansas Cotton Growers Association", "has_directory": False}],
    "Florida": [{"name": "Florida Cotton Growers", "has_directory": False}],
    "Kansas": [{"name": "Kansas Cotton Association", "has_directory": False}],
    "Louisiana": [{"name": "Louisiana Cotton Producers", "has_directory": False}],
    "Mississippi": [{"name": "Mississippi Cotton Producers Association", "has_directory": False}],
    "Missouri": [{"name": "Missouri Cotton Council", "has_directory": False}],
    "New Mexico": [{"name": "New Mexico Cotton Growers", "has_directory": False}],
    "North Carolina": [{"name": "North Carolina Cotton Producers Association", "has_directory": False}],
    "Oklahoma": [{"name": "Oklahoma Cotton Council", "has_directory": False}],
    "South Carolina": [{"name": "South Carolina Cotton Board", "has_directory": False}],
    "Tennessee": [{"name": "Tennessee Cotton Growers Association", "has_directory": False}],
    "Virginia": [{"name": "Virginia Cotton Growers", "has_directory": False}],
}


class StateAssociationSource:
    """State cotton associations - org contacts for supplemental data."""

    def fetch_associations(
        self,
        states: list[str] | None = None,
    ) -> Iterator[dict]:
        """
        Yield state association info (not individual growers).

        Use for: manual outreach, validating coverage, gin code lists.
        """
        states = states or COTTON_PRODUCING_STATES
        for state in states:
            for org in STATE_ASSOCIATIONS.get(state, []):
                yield {
                    "state": state,
                    "organization": org.get("name", ""),
                    "url": org.get("url", ""),
                    "location": org.get("location", ""),
                    "has_member_directory": org.get("has_directory", False),
                    "source": "State Cotton Associations",
                }

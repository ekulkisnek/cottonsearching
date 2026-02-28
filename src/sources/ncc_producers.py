"""
National Cotton Council - American Cotton Producers (ACP).

Elected cotton producer leaders from across the Cotton Belt - all are active growers.
Source: https://www.cotton.org/about/acp.cfm
"""

from typing import Iterator

# 2026 American Cotton Producers - state chairs and regional directors (all cotton growers)
NCC_ACP_PRODUCERS = [
    # Officers
    ("Daniel W. Baxley", "Dillon", "SC"),
    ("Clinton James Dunn", "Itta Bena", "MS"),
    ("Gerald A. Rovey", "Buckeye", "AZ"),
    # State Producer Chairman
    ("Shane Isbell", "Cherokee", "AL"),
    ("Nick R. McMichen", "Centre", "AL"),
    ("Jesse Cooper Flye", "Jonesboro", "AR"),
    ("Dean Everett Rovey", "Buckeye", "AZ"),
    ("Dean R. Wells", "Casa Grande", "AZ"),
    ("Bryan Bone", "Bakersfield", "CA"),
    ("Nicholas Marshall", "Baker", "FL"),
    ("Lee Cromley", "Brooklet", "GA"),
    ("Bart Davis, Jr.", "Doerun", "GA"),
    ("Stuart C. Briggeman", "Pratt", "KS"),
    ("Stephen E. Logan", "Gilliam", "LA"),
    ("Russell Y. Ratcliff, III", "Saint Joseph", "LA"),
    ("Barry B. Bean", "Gideon", "MO"),
    ("Ted H. Kendall, IV", "Bolton", "MS"),
    ("Eric K. Cahoon", "Engelhard", "NC"),
    ("Chris Sawyer", "Greenville", "NC"),
    ("Dean Calvani", "Carlsbad", "NM"),
    ("Philip Ray Bohl", "Faxon", "OK"),
    ("Mark Nichols", "Altus", "OK"),
    ("Cecil Eaddy, Jr.", "Manning", "SC"),
    ("James H. Johnson", "Mayesville", "SC"),
    ("Jason R. Luckey", "Humboldt", "TN"),
    ("William R. Walker", "Somerville", "TN"),
    ("Brent Coker", "Lubbock", "TX"),
    ("Stacy W. Smith", "Wilson", "TX"),
    ("James W. Jones, Jr.", "Windsor", "VA"),
    # Regional Producer Directors
    ("Jon R. Whatley", "Odem", "TX"),
    ("Jason T. Condrey", "Lake Providence", "LA"),
    ("Madison C. Coley", "Vienna", "GA"),
    ("James Sutton Page", "Avoca", "TX"),
    ("Garold Joe Martin", "Firebaugh", "CA"),
]


class NCCProducersSource:
    """NCC American Cotton Producers - elected grower leaders."""

    def fetch_growers(self) -> Iterator[dict]:
        """Yield cotton growers from NCC ACP."""
        for name, city, state in NCC_ACP_PRODUCERS:
            yield {
                "name": name,
                "city": city,
                "state": state,
                "type": "grower",
                "email": "",
                "phone": "",
                "website": "",
                "buy_link": "",
                "prices": "Contact for quote",
                "source": "NCC American Cotton Producers",
            }

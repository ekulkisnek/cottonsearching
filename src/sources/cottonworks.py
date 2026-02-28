"""
CottonWorks U.S. Supplier List data source.

Downloads and parses the CottonWorks U.S. Supplier List PDF.
Source: cottonworks.com/sourcing/find-us-suppliers/

Contains: yarn spinners, knit/woven fabric mills, dyers, finishers, cut & sew.
Spinners and weavers are cotton fiber buyers; others are downstream.
"""

import re
from io import BytesIO
from pathlib import Path
from typing import Iterator

import httpx
from pypdf import PdfReader

COTTONWORKS_PDF_URL = "https://cottonworks.com/wp-content/uploads/2026/01/US-Supplier-List-high-rez-2.pdf"


class CottonWorksSource:
    """Parse CottonWorks U.S. Supplier List PDF."""

    def __init__(self, pdf_path: str | Path | None = None):
        """
        Args:
            pdf_path: Local PDF path. If None, downloads from CottonWorks.
        """
        self.pdf_path = Path(pdf_path) if pdf_path else None

    def _get_pdf_bytes(self) -> bytes:
        """Fetch PDF content from URL or local file."""
        if self.pdf_path and self.pdf_path.exists():
            return self.pdf_path.read_bytes()
        with httpx.Client(follow_redirects=True) as client:
            r = client.get(COTTONWORKS_PDF_URL)
            r.raise_for_status()
            return r.content

    def fetch_suppliers(self) -> Iterator[dict]:
        """
        Yield US cotton suppliers from the PDF.
        Focus on spinners and weavers (cotton fiber buyers).
        """
        raw = self._get_pdf_bytes()
        reader = PdfReader(BytesIO(raw))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""

        # Parse SPINNERS and WEAVERS sections
        sections = ["SPINNERS", "WEAVERS"]
        for section in sections:
            pattern = rf"{section}\s*\n(.*?)(?=\n[A-Z][A-Z\s]+\s*\n|AMERICA'S COTTON|$)"
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if not match:
                continue
            block = match.group(1)
            for entry in self._parse_entries(block, section.lower()[:-1]):
                entry["source"] = "CottonWorks"
                entry["source_url"] = "https://cottonworks.com/sourcing/find-us-suppliers/"
                yield entry

    def _parse_entries(self, block: str, category: str) -> Iterator[dict]:
        """Parse supplier entries from a section block."""
        # Pattern: Company Name   Phone: (...)   City, State   Website: ...   Capabilities: ...
        lines = block.strip().split("\n")
        i = 0
        while i < len(lines):
            line = lines[i]
            if not line.strip():
                i += 1
                continue
            # First line is company name (may have "Phone:" on same line)
            name_part = line
            phone = None
            city = ""
            state = ""
            url = ""
            capabilities = []

            # Extract phone if on same line
            phone_match = re.search(r"Phone:\s*\(?([^)]+)\)?\s*([^\s,]+)?", name_part)
            if phone_match:
                phone = phone_match.group(1).strip()
                name_part = name_part[: phone_match.start()].strip()

            name = name_part.strip()
            if not name or len(name) < 2:
                i += 1
                continue

            # Next line(s): City, State and/or Website
            i += 1
            while i < len(lines):
                next_line = lines[i]
                if re.match(r"^[A-Z][a-z]+,\s*[A-Z]{2}\s*$", next_line.strip()):
                    parts = next_line.strip().split(",")
                    if len(parts) >= 2:
                        city = parts[0].strip()
                        state = parts[1].strip()[:2]
                    i += 1
                    break
                if "Website:" in next_line:
                    url_match = re.search(r"Website:\s*(\S+)", next_line)
                    if url_match:
                        url = url_match.group(1).strip()
                if "Capabilities:" in next_line:
                    cap_text = next_line.split("Capabilities:")[-1].strip()
                    if cap_text:
                        capabilities.append(cap_text)
                    i += 1
                    # Continue reading capability lines (wrapped)
                    while i < len(lines) and lines[i].strip() and not re.match(
                        r"^[A-Z][a-z]+,\s*[A-Z]{2}", lines[i]
                    ):
                        capabilities.append(lines[i].strip())
                        i += 1
                    break
                i += 1
                if "Capabilities:" in next_line:
                    break

            if name and (city or state):
                yield {
                    "name": name,
                    "city": city,
                    "state": state,
                    "url": url or None,
                    "phone": phone,
                    "type": "us_supplier",
                    "category": category,
                    "notes": "; ".join(capabilities)[:200] if capabilities else f"CottonWorks {category}",
                }

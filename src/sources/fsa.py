"""
FSA Farm Programs Payments data source.

Downloads FSA payment files from the FOIA Electronic Reading Room and filters
for cotton-related programs/commodities to identify cotton growers.

Source: https://www.fsa.usda.gov/tools/informational/freedom-information-act-foia/electronic-reading-room/frequently-requested/payment-files
"""

import os
import re
from pathlib import Path
from typing import Iterator

import pandas as pd
import requests

from ..config import COTTON_KEYWORDS, DATA_DIR


# FSA Payment file URLs by year (2025 - most recent)
# Format: state ranges with direct document links
FSA_PAYMENT_URLS_2025 = [
    "https://www.fsa.usda.gov/documents/state-wv-wyfoianapmt25finaldt25365",
    "https://www.fsa.usda.gov/documents/state-tx-wafoianapmt25finaldt25365",
    "https://www.fsa.usda.gov/documents/state-tnfoianapmt25finaldt25365",
    "https://www.fsa.usda.gov/documents/state-ne-ncfoianapmt25finaldt25365",
    "https://www.fsa.usda.gov/documents/state-nd-okfoianapmt25finaldt25365",
    "https://www.fsa.usda.gov/documents/state-ms-mtfoianapmt25finaldt25365",
    "https://www.fsa.usda.gov/documents/state-la-mnfoianapmt25finaldt25365",
    "https://www.fsa.usda.gov/documents/state-ks-kyfoianapmt25finaldt25365",
    "https://www.fsa.usda.gov/documents/state-il-infoianapmt25finaldt25365",
    "https://www.fsa.usda.gov/documents/name-payment-address-iowa-2025",
    "https://www.fsa.usda.gov/documents/name-address-payment-alabama-idaho-2025",
]

# 2024 files
FSA_PAYMENT_URLS_2024 = [
    "https://www.fsa.usda.gov/documents/state-ia-mifoianapmt24finaldt25002",
    "https://www.fsa.usda.gov/documents/state-tx-wyfoianapmt24finaldt25002",
    "https://www.fsa.usda.gov/documents/state-nd-tnfoianapmt24finaldt25002",
    "https://www.fsa.usda.gov/documents/state-mn-ncfoianapmt24finaldt25002",
    "https://www.fsa.usda.gov/documents/state-al-infoianapmt24finaldt25002",
]

# 2023 files (direct .xlsx URLs - more reliable for download)
# UT-WY is smallest (~12MB); AL-IN has key cotton states
FSA_PAYMENT_URLS_2023 = [
    "https://www.fsa.usda.gov/sites/default/files/documents/STATE-UT-WY.FOIA.NA.PMT23.FINAL.DT24006.xlsx",
    "https://www.fsa.usda.gov/sites/default/files/documents/STATE-AL-IN.FOIA.NA.PMT23.FINAL.DT24006.xlsx",
    "https://www.fsa.usda.gov/sites/default/files/documents/STATE-IA-KY.FOIA.NA.PMT23.FINAL.DT24006.xlsx",
    "https://www.fsa.usda.gov/sites/default/files/documents/STATE-LA-MT.FOIA.NA.PMT23.FINALDT24006.xlsx",
    "https://www.fsa.usda.gov/sites/default/files/documents/STATE-NE-OK.FOIA.NA.PMT23.FINAL.DT24006.xlsx",
    "https://www.fsa.usda.gov/sites/default/files/documents/STATE-OR-TX.FOIA.NA.PMT23.FINAL.DT24006.xlsx",
]


class FSAPaymentSource:
    """FSA Farm Programs Payments - primary source for cotton grower names."""

    def __init__(self, cache_dir: str | None = None, year: int = 2024):
        self.cache_dir = Path(cache_dir or os.path.join(DATA_DIR, "fsa"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.year = year
        url_map = {
            2023: FSA_PAYMENT_URLS_2023,
            2024: FSA_PAYMENT_URLS_2024,
            2025: FSA_PAYMENT_URLS_2025,
        }
        self.urls = url_map.get(year, FSA_PAYMENT_URLS_2024)

    def _is_cotton_related(self, value: str) -> bool:
        """Check if a program/commodity string is cotton-related."""
        if pd.isna(value) or not isinstance(value, str):
            return False
        val_lower = value.lower()
        return any(kw in val_lower for kw in COTTON_KEYWORDS)

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names for flexible matching."""
        df = df.copy()
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
        return df

    def _find_cotton_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter dataframe for cotton-related payments."""
        df = self._normalize_columns(df)
        # Common FSA column names (vary by year)
        program_cols = [c for c in df.columns if "program" in c or "commodity" in c or "crop" in c]
        name_cols = [c for c in df.columns if "name" in c or "payee" in c or "recipient" in c]
        address_cols = [c for c in df.columns if "address" in c or "city" in c or "state" in c]

        if not program_cols:
            # Try first few columns as fallback
            program_cols = list(df.columns[:5])

        mask = pd.Series([False] * len(df))
        for col in program_cols:
            if col in df.columns:
                mask = mask | df[col].apply(self._is_cotton_related)

        return df[mask]

    def _download_file(self, url: str) -> Path:
        """Download FSA payment file to cache."""
        filename = url.split("/")[-1]
        if not filename.lower().endswith(".xlsx"):
            filename = filename + ".xlsx"
        filepath = self.cache_dir / filename

        if filepath.exists():
            return filepath

        resp = requests.get(url, timeout=300, stream=True, allow_redirects=True)
        resp.raise_for_status()
        # Use content-disposition filename if present
        cd = resp.headers.get("content-disposition", "")
        if "filename=" in cd:
            m = re.search(r'filename="?([^";\n]+)"?', cd)
            if m:
                filename = m.group(1).strip()
                filepath = self.cache_dir / filename
        filepath.write_bytes(resp.content)
        return filepath

    def _read_excel(self, filepath: Path) -> pd.DataFrame:
        """Read Excel file, handling multiple sheets."""
        try:
            xl = pd.ExcelFile(filepath)
            dfs = []
            for sheet in xl.sheet_names:
                df = pd.read_excel(xl, sheet_name=sheet, header=0)
                if len(df) > 0 and len(df.columns) > 2:
                    dfs.append(df)
            return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
        except Exception as e:
            print(f"Warning: Could not read {filepath}: {e}")
            return pd.DataFrame()

    def fetch_cotton_growers(
        self,
        download: bool = True,
        urls: list[str] | None = None,
    ) -> Iterator[dict]:
        """
        Fetch cotton growers from FSA payment files.

        Yields dicts with: name, address, city, state, program, amount, year, source
        """
        urls = urls or self.urls
        seen = set()

        for url in urls:
            try:
                if download:
                    filepath = self._download_file(url)
                else:
                    filepath = self.cache_dir / (url.split("/")[-1] + ".xlsx")
                    if not filepath.exists():
                        continue

                df = self._read_excel(filepath)
                cotton_df = self._find_cotton_rows(df)

                for _, row in cotton_df.iterrows():
                    # Build grower record
                    name = ""
                    for col in ["payee_name", "recipient_name", "name", "payee"]:
                        if col in row and pd.notna(row.get(col)):
                            name = str(row[col]).strip()
                            break
                    if not name:
                        name = str(row.get(list(row.index)[0], ""))

                    addr = str(row.get("address", row.get("street", "")) or "")
                    city = str(row.get("city", "")) or ""
                    state = str(row.get("state", "")) or ""
                    program = str(row.get("program") or row.get("commodity") or "")
                    amount = row.get("amount", row.get("payment", ""))

                    key = (name, addr, state)
                    if key in seen:
                        continue
                    seen.add(key)

                    yield {
                        "name": name,
                        "address": addr,
                        "city": city,
                        "state": state,
                        "program": program,
                        "amount": amount,
                        "year": self.year,
                        "source": "FSA Farm Programs Payments",
                    }
            except Exception as e:
                print(f"Error processing {url}: {e}")
                continue

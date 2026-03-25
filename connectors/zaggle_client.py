"""
Zaggle connector stub.

This first-step adapter reads Zaggle-style transaction exports from a local
CSV or JSON file and normalizes them into the CFO-OS transaction schema.
"""
from __future__ import annotations

import os
from typing import Dict, Optional

import pandas as pd


class ZaggleClient:
    """Load and normalize Zaggle-style transaction exports."""

    DATE_ALIASES = ["date", "transaction_date", "txn_date", "posted_date"]
    AMOUNT_ALIASES = ["amount", "txn_amount", "transaction_amount", "gross_amount"]
    VENDOR_ALIASES = ["vendor", "merchant", "merchant_name", "vendor_name"]
    CATEGORY_ALIASES = ["category", "expense_category", "merchant_category", "gl_category"]

    CATEGORY_MAP = {
        "cloud": "tech",
        "software": "tech",
        "it": "tech",
        "tech": "tech",
        "payroll": "payroll",
        "salary": "payroll",
        "benefits": "payroll",
        "office": "operations",
        "operations": "operations",
        "facilities": "operations",
        "utilities": "operations",
        "maintenance": "operations",
        "travel": "operations",
        "advertising": "marketing",
        "media": "marketing",
        "marketing": "marketing",
        "promotion": "marketing",
    }

    def __init__(self, export_path: Optional[str] = None):
        self.export_path = export_path or os.getenv("ZAGGLE_EXPORT_PATH")

    def load_transactions(self) -> pd.DataFrame:
        """Load Zaggle export into the normalized CFO-OS schema."""
        if not self.export_path:
            raise FileNotFoundError("No Zaggle export path configured.")
        if not os.path.exists(self.export_path):
            raise FileNotFoundError(f"Zaggle export not found: {self.export_path}")

        if self.export_path.lower().endswith(".json"):
            raw_df = pd.read_json(self.export_path)
        else:
            raw_df = pd.read_csv(self.export_path)

        return self.normalize_transactions(raw_df)

    def normalize_transactions(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """Map Zaggle-style fields to the schema expected by the platform."""
        raw_df = raw_df.copy()
        if raw_df.empty:
            return pd.DataFrame(columns=["date", "category", "amount", "vendor"])

        date_col = self._find_column(raw_df, self.DATE_ALIASES)
        amount_col = self._find_column(raw_df, self.AMOUNT_ALIASES)
        vendor_col = self._find_column(raw_df, self.VENDOR_ALIASES)
        category_col = self._find_column(raw_df, self.CATEGORY_ALIASES)

        if not date_col or not amount_col or not vendor_col:
            raise ValueError(
                "Zaggle export is missing required fields. "
                "Expected date, amount, and vendor-style columns."
            )

        if not category_col:
            category_series = raw_df.get(vendor_col, pd.Series(["operations"] * len(raw_df))).astype(str)
        else:
            category_series = raw_df[category_col].astype(str)

        normalized = pd.DataFrame(
            {
                "date": pd.to_datetime(raw_df[date_col], errors="coerce"),
                "amount": pd.to_numeric(raw_df[amount_col], errors="coerce").abs(),
                "vendor": raw_df[vendor_col].fillna("Unknown Vendor").astype(str).str.strip(),
                "category": category_series.fillna("operations").astype(str).map(self._map_category),
            }
        )
        normalized = normalized.dropna(subset=["date", "amount"])
        normalized = normalized[normalized["amount"] > 0].reset_index(drop=True)
        return normalized

    def _find_column(self, df: pd.DataFrame, aliases):
        lookup = {str(col).strip().lower(): col for col in df.columns}
        for alias in aliases:
            if alias in lookup:
                return lookup[alias]
        return None

    def _map_category(self, raw_category: str) -> str:
        category = raw_category.strip().lower()
        for key, mapped in self.CATEGORY_MAP.items():
            if key in category:
                return mapped
        return "operations"


def load_zaggle_transactions(export_path: Optional[str] = None) -> pd.DataFrame:
    """Convenience loader for Zaggle-style exports."""
    client = ZaggleClient(export_path=export_path)
    return client.load_transactions()

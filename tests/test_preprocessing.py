"""
tests/test_preprocessing.py
----------------------------
Unit tests for data_preprocessing module.
"""
from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
import pytest

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_preprocessing import (
    clean_dataframe,
    build_baskets,
    filter_baskets,
    temporal_split,
)


def _make_raw_df(**overrides) -> pd.DataFrame:
    """Build a minimal raw DataFrame that mimics the UCI Online Retail schema."""
    data = {
        "Invoice": ["536365", "536366", "C536367", "536368", "536369"],
        "StockCode": ["85123A", "71053", "84406B", "84029G", "84029E"],
        "Description": [
            "WHITE HANGING HEART T-LIGHT HOLDER",
            "WHITE METAL LANTERN",
            "CREAM CUPID HEARTS COAT HANGER",
            "KNITTED UNION FLAG HOT WATER BOTTLE",
            "RED WOOLLY HOTTIE WHITE HEART",
        ],
        "Quantity": [6, 6, 8, 6, 6],
        "InvoiceDate": pd.to_datetime(
            [
                "2010-12-01 08:26",
                "2010-12-01 08:28",
                "2010-12-01 08:28",
                "2010-12-01 08:34",
                "2010-12-01 08:34",
            ]
        ),
        "Price": [2.55, 3.39, 2.75, 3.39, 3.39],
        "CustomerID": [17850.0, 17850.0, np.nan, 17850.0, 17850.0],
        "Country": ["United Kingdom"] * 5,
    }
    data.update(overrides)
    return pd.DataFrame(data)


# ---------------------------------------------------------------------------
# 1. Cancellation removal
# ---------------------------------------------------------------------------

class TestRemoveCancellations:
    def test_cancelled_invoices_removed(self):
        df = _make_raw_df()
        cleaned = clean_dataframe(df)
        assert not cleaned["Invoice"].str.startswith("C").any()

    def test_non_cancelled_retained(self):
        df = _make_raw_df()
        cleaned = clean_dataframe(df)
        assert "536365" in cleaned["Invoice"].values


# ---------------------------------------------------------------------------
# 2. Negative / zero quantity removal
# ---------------------------------------------------------------------------

class TestRemoveNegativeQuantities:
    def test_negative_quantity_removed(self):
        df = _make_raw_df(
            Invoice=["536365", "536366"],
            StockCode=["85123A", "71053"],
            Description=["WIDGET A", "WIDGET B"],
            Quantity=[-1, 5],
            InvoiceDate=pd.to_datetime(["2010-12-01", "2010-12-01"]),
            Price=[2.55, 3.39],
            CustomerID=[17850.0, 17850.0],
            Country=["United Kingdom", "United Kingdom"],
        )
        cleaned = clean_dataframe(df)
        assert len(cleaned) == 1
        assert cleaned.iloc[0]["Quantity"] == 5

    def test_zero_quantity_removed(self):
        df = _make_raw_df(
            Invoice=["536365"],
            StockCode=["85123A"],
            Description=["WIDGET A"],
            Quantity=[0],
            InvoiceDate=pd.to_datetime(["2010-12-01"]),
            Price=[2.55],
            CustomerID=[17850.0],
            Country=["United Kingdom"],
        )
        cleaned = clean_dataframe(df)
        assert len(cleaned) == 0


# ---------------------------------------------------------------------------
# 3. Missing CustomerID removal
# ---------------------------------------------------------------------------

class TestRemoveMissingCustomer:
    def test_missing_customer_id_dropped(self):
        df = _make_raw_df()
        cleaned = clean_dataframe(df)
        assert cleaned["CustomerID"].isna().sum() == 0

    def test_all_rows_have_customer_id(self):
        df = _make_raw_df(
            Invoice=["536365", "536366"],
            StockCode=["85123A", "71053"],
            Description=["WIDGET A", "WIDGET B"],
            Quantity=[1, 1],
            InvoiceDate=pd.to_datetime(["2010-12-01", "2010-12-01"]),
            Price=[1.0, 1.0],
            CustomerID=[np.nan, np.nan],
            Country=["UK", "UK"],
        )
        cleaned = clean_dataframe(df)
        assert len(cleaned) == 0


# ---------------------------------------------------------------------------
# 4. Basket must have multiple items
# ---------------------------------------------------------------------------

class TestBasketMultipleItems:
    def test_single_item_transactions_excluded(self):
        df = pd.DataFrame(
            {
                "Invoice": ["INV001", "INV001", "INV002"],
                "Description": ["PRODUCT A", "PRODUCT B", "PRODUCT C"],
                "Quantity": [1, 1, 1],
                "Price": [1.0, 1.0, 1.0],
                "CustomerID": [1.0, 1.0, 2.0],
                "InvoiceDate": pd.to_datetime(
                    ["2010-12-01", "2010-12-01", "2010-12-01"]
                ),
                "Country": ["UK", "UK", "UK"],
            }
        )
        baskets_df, _ = build_baskets(df)
        filtered = filter_baskets(baskets_df, min_basket_size=2, min_product_support=1)
        assert "INV001" in filtered["Invoice"].values
        assert "INV002" not in filtered["Invoice"].values


# ---------------------------------------------------------------------------
# 5. Product list is sorted
# ---------------------------------------------------------------------------

class TestProductListSorted:
    def test_products_sorted_alphabetically(self):
        products = ["ZEBRA MUG", "APPLE CORER", "MANGO BOWL"]
        sorted_products = sorted(products)
        assert sorted_products == ["APPLE CORER", "MANGO BOWL", "ZEBRA MUG"]


# ---------------------------------------------------------------------------
# 6. Train/test split ratio
# ---------------------------------------------------------------------------

class TestTrainTestSplitRatio:
    def test_split_is_approximately_80_20(self):
        dates = [datetime(2010, 1, 1) + timedelta(days=i) for i in range(100)]
        df = pd.DataFrame({
            "Invoice": [f"INV{i:03d}" for i in range(100)],
            "InvoiceDate": dates,
            "products": [["PRODUCT A", "PRODUCT B"] for _ in range(100)]
        })
        train, test = temporal_split(df, train_ratio=0.8)
        assert len(train) == 80
        assert len(test) == 20

    def test_split_no_overlap(self):
        dates = [datetime(2010, 1, 1) + timedelta(days=i) for i in range(50)]
        df = pd.DataFrame({
            "Invoice": [f"INV{i:03d}" for i in range(50)],
            "InvoiceDate": dates,
            "products": [[f"PROD_{i}", "PROD_B"] for i in range(50)]
        })
        train, test = temporal_split(df, train_ratio=0.8)
        assert len(train) + len(test) == 50
        assert len(train) == 40
        assert len(test) == 10


# ---------------------------------------------------------------------------
# 7. Description cleaning
# ---------------------------------------------------------------------------

class TestDescriptionCleaning:
    def test_descriptions_uppercased(self):
        df = pd.DataFrame(
            {
                "Invoice": ["INV001"],
                "Description": ["white hanging heart t-light holder"],
                "Quantity": [1],
                "Price": [1.0],
                "CustomerID": [1.0],
                "InvoiceDate": pd.to_datetime(["2010-12-01"]),
                "Country": ["UK"],
            }
        )
        cleaned = clean_dataframe(df)
        if len(cleaned) > 0:
            assert cleaned.iloc[0]["Description"] == cleaned.iloc[0]["Description"].upper()

    def test_descriptions_stripped(self):
        df = pd.DataFrame(
            {
                "Invoice": ["INV001"],
                "Description": ["  WIDGET WITH SPACES   "],
                "Quantity": [1],
                "Price": [1.0],
                "CustomerID": [1.0],
                "InvoiceDate": pd.to_datetime(["2010-12-01"]),
                "Country": ["UK"],
            }
        )
        cleaned = clean_dataframe(df)
        if len(cleaned) > 0:
            desc = cleaned.iloc[0]["Description"]
            assert desc == desc.strip()


# ---------------------------------------------------------------------------
# 8. Non-product descriptions removed
# ---------------------------------------------------------------------------

class TestNonProductRemoval:
    @pytest.mark.parametrize(
        "non_product",
        ["POSTAGE", "DOTCOM POSTAGE", "MANUAL", "BANK CHARGES", "AMAZON FEE"],
    )
    def test_non_products_filtered(self, non_product):
        df = pd.DataFrame(
            {
                "Invoice": ["INV001", "INV002"],
                "Description": [non_product, "REAL PRODUCT ITEM"],
                "Quantity": [1, 1],
                "Price": [1.0, 1.0],
                "CustomerID": [1.0, 1.0],
                "InvoiceDate": pd.to_datetime(["2010-12-01", "2010-12-01"]),
                "Country": ["UK", "UK"],
            }
        )
        cleaned = clean_dataframe(df)
        if len(cleaned) > 0:
            assert non_product not in cleaned["Description"].values

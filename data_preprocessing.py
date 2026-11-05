"""
data_preprocessing.py
=====================
Data acquisition, cleaning, and preprocessing pipeline for the
Smart Product Bundle Recommendation System.

Downloads (or synthetically generates) the UCI Online Retail II dataset,
cleans it, builds transaction baskets, performs a temporal train/test split,
and persists all artefacts to disk.

Usage
-----
    python data_preprocessing.py

    # Or from another module:
    from data_preprocessing import load_or_preprocess
    info = load_or_preprocess(data_dir="data")
"""

from __future__ import annotations

import os
import pickle
import random
import string
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd
import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DATASET_URL = (
    "https://archive.ics.uci.edu/ml/machine-learning-databases/00502/online_retail_II.xlsx"
)

# Descriptions that are not genuine products and should be excluded
NON_PRODUCT_DESCRIPTIONS = {
    "POSTAGE",
    "DOTCOM POSTAGE",
    "MANUAL",
    "BANK CHARGES",
    "AMAZON FEE",
    "DISCOUNT",
    "CRUK COMMISSION",
    "SAMPLES",
    "DAMAGED",
    "LOST",
    "ADJUST",
    "ADJUSTMENT",
    "CARRIAGE",
    "PACKING CHARGE",
    "NEXT DAY CARRIAGE",
    "HIGH RESOLUTION IMAGE",
    "WRONGLY CODED",
    "WRONGLY SOLD",
}

MIN_BASKET_SIZE = 2       # minimum products per transaction
MIN_PRODUCT_SUPPORT = 5   # minimum transactions a product must appear in
TRAIN_RATIO = 0.80        # temporal split ratio

# ---------------------------------------------------------------------------
# DatasetInfo dataclass
# ---------------------------------------------------------------------------


@dataclass
class DatasetInfo:
    """Summary statistics returned after preprocessing.

    Attributes
    ----------
    total_transactions : int
        Number of valid, filtered transactions (baskets with >=2 products).
    unique_products : int
        Number of unique products that passed the support filter.
    train_size : int
        Number of transactions in the training split.
    test_size : int
        Number of transactions in the test split.
    date_range_start : datetime
        Earliest invoice date in the cleaned dataset.
    date_range_end : datetime
        Latest invoice date in the cleaned dataset.
    top_products : list of (str, int)
        Top-20 most-frequent products with their transaction counts.
    """

    total_transactions: int
    unique_products: int
    train_size: int
    test_size: int
    date_range_start: datetime
    date_range_end: datetime
    top_products: List[Tuple[str, int]] = field(default_factory=list)

    def __str__(self) -> str:  # pragma: no cover
        lines = [
            "=" * 60,
            "  DatasetInfo -- Smart Bundle Recommender",
            "=" * 60,
            f"  Total transactions (filtered) : {self.total_transactions:,}",
            f"  Unique products               : {self.unique_products:,}",
            f"  Train / Test split            : {self.train_size:,} / {self.test_size:,}",
            f"  Date range                    : {self.date_range_start.date()} -> {self.date_range_end.date()}",
            "",
            "  Top-20 products by transaction frequency:",
        ]
        for rank, (prod, cnt) in enumerate(self.top_products, 1):
            lines.append(f"    {rank:>2}. {prod[:50]:<50}  ({cnt:,})")
        lines.append("=" * 60)
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Synthetic dataset generation
# ---------------------------------------------------------------------------

# Realistic UK retail product catalogue used when real data cannot be fetched
_PRODUCT_CATALOGUE: List[str] = [
    "WHITE HANGING HEART T-LIGHT HOLDER",
    "WHITE METAL LANTERN",
    "CREAM CUPID HEARTS COAT HANGER",
    "KNITTED UNION FLAG HOT WATER BOTTLE",
    "RED WOOLLY HOTTIE WHITE HEART",
    "SET 7 BABUSHKA NESTING BOXES",
    "GLASS STAR FROSTED T-LIGHT HOLDER",
    "HAND WARMER UNION JACK",
    "HAND WARMER RED POLKA DOT",
    "ASSORTED COLOUR BIRD ORNAMENT",
    "POPPY'S PLAYHOUSE BEDROOM",
    "POPPY'S PLAYHOUSE KITCHEN",
    "FELTCRAFT PRINCESS CHARLOTTE DOLL",
    "IVORY KNITTED MUG COSY",
    "BOX OF 6 ASSORTED COLOUR TEASPOONS",
    "BOX OF VINTAGE JIGSAW BLOCKS",
    "BOX OF VINTAGE ALPHABET BLOCKS",
    "HOME BUILDING BLOCK WORD",
    "LOVE BUILDING BLOCK WORD",
    "RECIPE BOX WITH METAL HEART",
    "DOORMAT NEW HOME",
    "JAM MAKING SET WITH JARS",
    "RED COAT RACK PARIS FASHION",
    "YELLOW COAT RACK PARIS FASHION",
    "BLUE COAT RACK PARIS FASHION",
    "ALARM CLOCK BAKELIKE RED",
    "ALARM CLOCK BAKELIKE GREEN",
    "ALARM CLOCK BAKELIKE IVORY",
    "PANDA AND BUNNIES STICKER SHEET",
    "STARS GIFT TAPE",
    "PINK CHERRY LIGHTS",
    "ENAMEL COLANDER CREAM",
    "ENAMEL COLANDER RED",
    "SMALL CERAMIC TOP STORAGE JAR",
    "CERAMIC STORAGE JAR",
    "CERAMIC CAKE STAND",
    "CERAMIC BOWL WITH FLOWER DESIGN",
    "ROUND SNACK BOXES SET OF 4",
    "SPACEBOY LUNCH BOX",
    "CIRCUS PARADE LUNCH BOX",
    "LUNCH BOX I LOVE LONDON",
    "LUNCH BOX WITH CUTLERY WESTBEACH",
    "MINI PAINT SET VINTAGE",
    "STRAWBERRY CERAMIC TRINKET BOX",
    "ROSE CERAMIC TRINKET BOX",
    "BUTTERFLY CERAMIC TRINKET BOX",
    "WOODEN STAR CHRISTMAS SCANDINAVIAN",
    "WOODEN TREE CHRISTMAS SCANDINAVIAN",
    "WOODEN HEART CHRISTMAS SCANDINAVIAN",
    "PINK FLORAL FELTCRAFT SHOULDER BAG",
    "BLUE FLORAL FELTCRAFT SHOULDER BAG",
    "SUNFLOWER GARDEN TRUG",
    "HERB GARDEN GROW YOUR OWN",
    "SALAD GARDEN GROW YOUR OWN",
    "STRAWBERRY GARDEN GROW YOUR OWN",
    "VINTAGE SNAP CARDS",
    "VINTAGE HEADS AND TAILS GAME",
    "VINTAGE DOMINOS",
    "NEON BUBBLE BATH",
    "BUBBLE BATH WITH RUBBER DUCK",
    "RUBBER DUCK",
    "FAIRY LIQUID PUMP DISPENSER",
    "WOODEN FRAME ANTIQUE WHITE",
    "WOODEN PHOTO FRAME BLACK",
    "TRAVEL CARD WALLET KEEP CALM",
    "GIRLS ALPHABET IRON ON PATCHES",
    "BOYS ALPHABET IRON ON PATCHES",
    "INFLATABLE POLITICAL GLOBE",
    "INFLATABLE GLOBE",
    "SET OF 6 SOLDIER SKITTLES",
    "SET OF 6 FAIRY TALE SKITTLES",
    "RETRO COFFEE MUGS ASSORTED",
    "POLKADOT RAIN BOOT PLANTER",
    "UNION JACK PLATE",
    "UNION JACK MUG",
    "UNION JACK CUSHION COVER",
    "KNITTED UNICORN",
    "PLUSH BUNNY WITH BOW",
    "PLUSH CHICK WITH BOW",
    "PAPER CRAFT LITTLE BIRDIE",
    "PAPER CHAIN KIT RETRO CHRISTMAS",
    "PAPER CHAIN KIT VINTAGE CHRISTMAS",
    "CARD HOLDER BUTTERFLY",
    "CARD HOLDER FLOWER",
    "CARD HOLDER HEART",
    "JUMBO BAG RED RETROSPOT",
    "JUMBO BAG PINK RETROSPOT",
    "JUMBO BAG BAROQUE BLACK WHITE",
    "JUMBO SHOPPER VINTAGE RED PAISLEY",
    "MEDIUM CERAMIC TOP STORAGE JAR",
    "REGENCY CAKESTAND 3 TIER",
    "WOODLAND STATIONERY SET",
    "ANIMALS STATIONERY SET",
    "FAIRY TALE STATIONERY SET",
    "BATH BUILDING BLOCK WORD",
    "PARTY BUNTING",
    "BUNTING UNION JACK",
    "BUNTING WHITE STARS",
    "MINI LADLE LOVE HEART",
    "MINI LADLE FLOWER",
    "MINI LADLE POLKA DOT",
    "POSTBOX MONEY BOX",
    "COTTAGE MONEY BOX",
    "OWL MONEY BOX",
    "GARDENERS KNEELING PAD KEEP CALM",
    "GARDENERS KNEELING PAD CUP OF TEA",
    "GARDENERS TRUG",
    "SPACEBOY PENCIL CASE",
    "CIRCUS PARADE PENCIL CASE",
    "WOODLAND PENCIL CASE",
    "TRAVEL SEWING KIT",
    "TRAVEL MANICURE SET",
    "TRAVEL COMB",
    "NOTEBOOK A7 WOODLAND",
    "NOTEBOOK A7 FAIRY TALE",
    "NOTEBOOK A7 ANIMALS",
    "MUG I AM SO VERY TIRED",
    "MUG KEEP CALM AND CARRY ON",
    "MUG MORNING QUEEN",
    "HANGING METAL HEART LANTERN",
    "HANGING METAL STAR LANTERN",
    "HANGING METAL MOON LANTERN",
    "SET OF 3 CAKE TINS PANTRY DESIGN",
    "SET OF 3 CAKE TINS RETROSPOT",
    "CAKE TIN VINTAGE DESIGN",
    "CAKE TIN BUTTERFLY DESIGN",
    "GINGHAM HEART DOORSTOP",
    "GINGHAM DOG DOORSTOP",
    "GINGHAM RABBIT DOORSTOP",
    "WOODEN ADVENT CALENDAR REINDEER",
    "WOODEN ADVENT CALENDAR SNOWMAN",
    "WOODEN ADVENT CALENDAR TREE",
    "CHRISTMAS GLASS BALL CANDLE HOLDER",
    "CHRISTMAS STAR GLITTER HANGER",
    "CHRISTMAS SNOWFLAKE GLITTER HANGER",
    "REINDEER STOCKING FELT ASSORTED",
    "CHRISTMAS TREE STOCKING FELT",
    "SANTA STOCKING FELT",
    "FESTIVE COOKIE CUTTER SET",
    "COOKIE CUTTER CHRISTMAS TREE",
    "COOKIE CUTTER STAR",
    "COOKIE CUTTER HEART",
    "CERAMIC STAR CHRISTMAS",
    "CERAMIC HEART CHRISTMAS",
    "CERAMIC ANGEL CHRISTMAS",
    "FELT CHRISTMAS TREE ADVENT CALENDAR",
    "FABRIC CHRISTMAS TREE DECORATION",
    "FABRIC SANTA DECORATION",
    "SNOWFLAKE WINDOW STICKER",
    "CHRISTMAS PUDDING CANDLE",
    "CHRISTMAS HOLLY CANDLE",
    "CHRISTMAS STAR CANDLE",
    "HOLLY FAIRY LIGHTS",
    "SNOWFLAKE FAIRY LIGHTS",
    "ICICLE FAIRY LIGHTS",
    "BATTERY OPERATED FAIRY LIGHTS WOOD",
    "BATTERY OPERATED FAIRY LIGHTS STAR",
    "BATTERY OPERATED FAIRY LIGHTS HEART",
    "WICKER STAR LARGE",
    "WICKER STAR SMALL",
    "WICKER HEART LARGE",
    "WICKER HEART SMALL",
    "PLOUGHMAN PICKLE JAR",
    "STRAWBERRY JAM JAR",
    "RASPBERRY JAM JAR",
    "MARMALADE JAR",
    "HONEY JAR",
    "VINTAGE STORAGE TIN",
    "FLORAL STORAGE TIN",
    "POLKADOT STORAGE TIN",
    "AFTERNOON TEA ASSORTED TINS SET OF 3",
    "HERB LABEL METAL SIGNS SET OF 6",
    "VEGETABLE LABEL METAL SIGNS SET OF 6",
    "FRUIT LABEL METAL SIGNS SET OF 6",
    "SIGN KITCHEN RULES LARGE",
    "SIGN KITCHEN RULES SMALL",
    "METAL SIGN HOME",
    "METAL SIGN LOVE",
    "METAL SIGN WELCOME",
    "CHALK BOARD HEART",
    "CHALK BOARD STAR",
    "CHALK BOARD HOUSE",
    "ANTIQUE SILVER PHOTO FRAME",
    "ANTIQUE GOLD PHOTO FRAME",
    "BAMBOO PHOTO FRAME",
    "WOVEN PHOTO FRAME",
    "POLKADOT WATERING CAN PINK",
    "POLKADOT WATERING CAN GREEN",
    "POLKADOT WATERING CAN BLUE",
    "GARDEN BIRD FEEDER",
    "GARDEN BIRD BATH",
    "GARDEN GNOME DIGGING",
    "GARDEN GNOME FISHING",
    "GARDEN HEDGEHOG",
    "GARDEN FROG",
    "GARDEN LADYBIRD",
    "GROW YOUR OWN CRESS EGG",
    "GROW YOUR OWN GRASS HEAD",
    "GROW YOUR OWN SUNFLOWER KIT",
    "LAVENDER SACHET",
    "ROSE SACHET",
    "JASMINE SACHET",
    "SCENTED CANDLE VANILLA",
    "SCENTED CANDLE LAVENDER",
    "SCENTED CANDLE ROSE",
    "SCENTED CANDLE JASMINE",
    "REED DIFFUSER VANILLA",
    "REED DIFFUSER LAVENDER",
    "REED DIFFUSER ROSE",
]


def _generate_synthetic_dataset(n_transactions: int = 5000) -> pd.DataFrame:
    """Generate a synthetic dataset that mirrors the UCI Online Retail II schema.

    The synthetic data features realistic UK retail product names, plausible
    prices, quantities, and a two-year date range matching the real dataset.

    Parameters
    ----------
    n_transactions : int, optional
        Approximate number of unique invoices to generate (default 5000).

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: InvoiceNo, StockCode, Description,
        Quantity, InvoiceDate, Price, CustomerID, Country.
    """
    print("  Generating synthetic dataset ...")
    rng = np.random.default_rng(seed=42)
    random.seed(42)

    products = _PRODUCT_CATALOGUE[: min(200, len(_PRODUCT_CATALOGUE))]
    # Assign a stable StockCode and Price to each product
    stock_codes = {p: f"{rng.integers(10000, 99999)}" for p in products}
    prices = {p: round(float(rng.choice([0.85, 1.25, 1.65, 2.50, 3.95, 4.95, 6.95, 8.95, 12.95, 16.95, 19.95, 24.95])), 2) for p in products}

    countries = [
        "United Kingdom", "United Kingdom", "United Kingdom", "United Kingdom",
        "Germany", "France", "Netherlands", "Spain", "Australia", "EIRE",
    ]
    country_weights = [0.90, 0.90, 0.90, 0.90, 0.02, 0.02, 0.015, 0.01, 0.01, 0.02]
    total_weight = sum(country_weights)
    country_probs = [w / total_weight for w in country_weights]

    start_date = datetime(2009, 12, 1)
    end_date = datetime(2011, 12, 9)
    date_span_days = (end_date - start_date).days

    rows: list[dict] = []
    customer_ids = rng.integers(12346, 18287, size=1500).tolist()

    for invoice_idx in range(n_transactions):
        invoice_no = f"{rng.integers(489000, 582000)}"
        invoice_date = start_date + timedelta(days=int(rng.integers(0, date_span_days)))
        customer_id = random.choice(customer_ids)
        country = rng.choice(countries, p=country_probs)

        # Each basket contains between 1 and 12 distinct products
        basket_size = int(rng.integers(1, 13))
        basket_products = random.sample(products, min(basket_size, len(products)))

        for product in basket_products:
            qty = int(rng.integers(1, 25))
            rows.append(
                {
                    "Invoice": invoice_no,
                    "StockCode": stock_codes[product],
                    "Description": product,
                    "Quantity": qty,
                    "InvoiceDate": invoice_date,
                    "Price": prices[product],
                    "Customer ID": float(customer_id),
                    "Country": country,
                }
            )

    df = pd.DataFrame(rows)
    print(f"  Generated {len(df):,} line items across {n_transactions:,} invoices.")
    return df


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------


def _download_dataset(save_path: Path, timeout: int = 120) -> bool:
    """Attempt to download the UCI Online Retail II Excel file.

    Streams the response and shows a simple progress indicator.

    Parameters
    ----------
    save_path : Path
        Destination file path (including filename).
    timeout : int, optional
        Request timeout in seconds (default 120).

    Returns
    -------
    bool
        ``True`` if the download succeeded, ``False`` otherwise.
    """
    print(f"Attempting to download dataset from:\n  {DATASET_URL}")
    try:
        with requests.get(DATASET_URL, stream=True, timeout=timeout) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("content-length", 0))
            downloaded = 0
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "wb") as fh:
                for chunk in resp.iter_content(chunk_size=65_536):
                    if chunk:
                        fh.write(chunk)
                        downloaded += len(chunk)
                        if total:
                            pct = downloaded / total * 100
                            print(f"\r  Progress: {pct:5.1f}%  ({downloaded:,} / {total:,} bytes)", end="", flush=True)
            print()  # newline after progress
        print(f"  Download complete -> {save_path}")
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"  Download failed: {exc}")
        return False


# ---------------------------------------------------------------------------
# Loading raw data
# ---------------------------------------------------------------------------


def _load_raw_dataframe(data_dir: Path) -> pd.DataFrame:
    """Load raw data either from a downloaded Excel file or synthetically.

    Tries to download the UCI dataset. If the file is already present locally
    it is used directly. Falls back to synthetic generation on any failure.

    Parameters
    ----------
    data_dir : Path
        Directory in which to store / look for the raw Excel file.

    Returns
    -------
    pd.DataFrame
        Raw DataFrame with at least the columns expected by the cleaning step.
    """
    xlsx_path = data_dir / "online_retail_II.xlsx"

    if xlsx_path.exists():
        print(f"  Raw Excel file found at {xlsx_path}, skipping download.")
    else:
        success = _download_dataset(xlsx_path)
        if not success:
            print("  Falling back to synthetic dataset generation.")
            return _generate_synthetic_dataset()

    # The real dataset has two sheets; read both and concatenate
    print("  Parsing Excel file (this may take a moment) ...")
    try:
        sheets = pd.read_excel(xlsx_path, sheet_name=None, engine="openpyxl")
        df = pd.concat(sheets.values(), ignore_index=True)
        print(f"  Loaded {len(df):,} raw rows from Excel.")
        return df
    except Exception as exc:  # noqa: BLE001
        print(f"  Failed to parse Excel: {exc}. Using synthetic data.")
        return _generate_synthetic_dataset()


# ---------------------------------------------------------------------------
# Cleaning
# ---------------------------------------------------------------------------


def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns to a canonical set regardless of source.

    Both the real UCI dataset and the synthetic generator use slightly
    different column names (e.g. ``Customer ID`` vs ``CustomerID``).  This
    function normalises them so the rest of the pipeline is source-agnostic.

    Parameters
    ----------
    df : pd.DataFrame
        Raw DataFrame.

    Returns
    -------
    pd.DataFrame
        DataFrame with standardised column names.
    """
    rename_map = {
        "Customer ID": "CustomerID",
        "customer id": "CustomerID",
        "customer_id": "CustomerID",
        "InvoiceNo": "Invoice",
        "invoice": "Invoice",
        "INVOICE": "Invoice",
        "StockCode": "StockCode",
        "stock_code": "StockCode",
        "Description": "Description",
        "description": "Description",
        "Quantity": "Quantity",
        "quantity": "Quantity",
        "InvoiceDate": "InvoiceDate",
        "invoice_date": "InvoiceDate",
        "UnitPrice": "Price",
        "unit_price": "Price",
        "price": "Price",
        "Country": "Country",
        "country": "Country",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    return df


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all cleaning rules to the raw retail DataFrame.

    Cleaning steps (in order):
    1. Normalise column names.
    2. Remove cancelled transactions (Invoice starts with 'C').
    3. Drop rows with missing CustomerID.
    4. Remove rows where Quantity <= 0.
    5. Remove rows where Price <= 0.
    6. Strip and uppercase Description; drop null/empty descriptions.
    7. Remove known non-product descriptions.

    Parameters
    ----------
    df : pd.DataFrame
        Raw retail DataFrame.

    Returns
    -------
    pd.DataFrame
        Cleaned DataFrame.
    """
    df = _normalise_columns(df)

    initial = len(df)
    print(f"  Cleaning {initial:,} rows ...")

    # 1. Remove cancellations
    mask_cancel = df["Invoice"].astype(str).str.startswith("C")
    df = df[~mask_cancel]
    print(f"    After removing cancellations       : {len(df):,} rows")

    # 2. Drop rows with missing CustomerID
    df = df.dropna(subset=["CustomerID"])
    print(f"    After dropping missing CustomerID  : {len(df):,} rows")

    # 3. Remove non-positive quantities
    df = df[df["Quantity"] > 0]
    print(f"    After Quantity > 0 filter          : {len(df):,} rows")

    # 4. Remove non-positive prices
    df = df[df["Price"] > 0]
    print(f"    After Price > 0 filter             : {len(df):,} rows")

    # 5. Standardise Description
    df["Description"] = (
        df["Description"]
        .astype(str)
        .str.strip()
        .str.upper()
    )
    df = df[df["Description"].notna() & (df["Description"] != "") & (df["Description"] != "NAN")]
    print(f"    After dropping empty descriptions  : {len(df):,} rows")

    # 6. Remove non-product descriptions
    df = df[~df["Description"].isin(NON_PRODUCT_DESCRIPTIONS)]
    print(f"    After removing non-products        : {len(df):,} rows")

    print(f"  Cleaning complete: {initial:,} -> {len(df):,} rows retained.")
    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Basket construction and filtering
# ---------------------------------------------------------------------------


def build_baskets(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[List[str]]]:
    """Group the cleaned DataFrame into per-invoice transaction baskets.

    Parameters
    ----------
    df : pd.DataFrame
        Cleaned retail DataFrame with ``Invoice``, ``InvoiceDate``, and
        ``Description`` columns.

    Returns
    -------
    basket_df : pd.DataFrame
        One row per invoice with columns ``Invoice``, ``InvoiceDate``,
        ``products`` (list of unique descriptions).
    all_baskets : list of list of str
        Flat list of baskets (lists of product descriptions), in invoice order.
    """
    # Ensure InvoiceDate is datetime
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")

    # Group: one row per invoice -> sorted list of unique products
    grp = (
        df.groupby("Invoice")
        .agg(
            InvoiceDate=("InvoiceDate", "min"),
            products=("Description", lambda x: sorted(set(x))),
        )
        .reset_index()
    )
    return grp, grp["products"].tolist()


def filter_baskets(
    basket_df: pd.DataFrame,
    min_basket_size: int = MIN_BASKET_SIZE,
    min_product_support: int = MIN_PRODUCT_SUPPORT,
) -> pd.DataFrame:
    """Filter baskets and products according to minimum support thresholds.

    Steps:
    1. Keep only baskets that contain at least ``min_basket_size`` products.
    2. Count how many transactions each product appears in.
    3. Keep only products that appear in at least ``min_product_support``
       transactions.
    4. Rebuild baskets using only the surviving products; drop baskets that
       fall below ``min_basket_size`` again after product filtering.

    Parameters
    ----------
    basket_df : pd.DataFrame
        DataFrame with ``Invoice``, ``InvoiceDate``, ``products`` columns.
    min_basket_size : int, optional
        Minimum number of products per basket (default 2).
    min_product_support : int, optional
        Minimum number of transactions a product must appear in (default 5).

    Returns
    -------
    pd.DataFrame
        Filtered basket DataFrame (same schema as input).
    """
    # Step 1 -- filter by basket size
    basket_df = basket_df[basket_df["products"].apply(len) >= min_basket_size].copy()
    print(f"    Baskets with >= {min_basket_size} products          : {len(basket_df):,}")

    # Step 2 -- product support counts
    from collections import Counter

    product_counts: Counter = Counter()
    for products in basket_df["products"]:
        product_counts.update(products)

    frequent_products = {p for p, c in product_counts.items() if c >= min_product_support}
    print(f"    Products with >= {min_product_support} transactions      : {len(frequent_products):,}")

    # Step 3 -- rebuild baskets with only frequent products
    basket_df["products"] = basket_df["products"].apply(
        lambda prods: [p for p in prods if p in frequent_products]
    )

    # Step 4 -- re-apply basket size filter
    basket_df = basket_df[basket_df["products"].apply(len) >= min_basket_size].copy()
    print(f"    Baskets remaining after product filter : {len(basket_df):,}")

    return basket_df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Temporal train/test split
# ---------------------------------------------------------------------------


def temporal_split(
    basket_df: pd.DataFrame,
    train_ratio: float = TRAIN_RATIO,
) -> Tuple[List[List[str]], List[List[str]]]:
    """Split baskets into train and test sets by invoice date.

    Transactions are sorted chronologically; the first ``train_ratio``
    fraction (by count) forms the training set and the remainder the test set.

    Parameters
    ----------
    basket_df : pd.DataFrame
        Filtered basket DataFrame with ``InvoiceDate`` and ``products`` columns.
    train_ratio : float, optional
        Fraction of transactions to include in training (default 0.80).

    Returns
    -------
    train_baskets : list of list of str
    test_baskets : list of list of str
    """
    sorted_df = basket_df.sort_values("InvoiceDate").reset_index(drop=True)
    split_idx = int(len(sorted_df) * train_ratio)
    train_baskets = sorted_df["products"].iloc[:split_idx].tolist()
    test_baskets = sorted_df["products"].iloc[split_idx:].tolist()
    print(f"    Train baskets : {len(train_baskets):,}  |  Test baskets : {len(test_baskets):,}")
    return train_baskets, test_baskets


# ---------------------------------------------------------------------------
# Preprocessing entry point
# ---------------------------------------------------------------------------


def preprocess(data_dir: str = "data") -> DatasetInfo:
    """Run the full preprocessing pipeline end-to-end.

    1. Download (or generate) the raw dataset.
    2. Clean the data.
    3. Build and filter transaction baskets.
    4. Perform an 80/20 temporal train/test split.
    5. Persist all artefacts to ``data_dir``.
    6. Return a populated :class:`DatasetInfo` instance.

    Parameters
    ----------
    data_dir : str, optional
        Directory for all data artefacts (default ``"data"``).

    Returns
    -------
    DatasetInfo
        Summary statistics for the processed dataset.
    """
    data_path = Path(data_dir)
    data_path.mkdir(parents=True, exist_ok=True)

    # ── 1. Load raw data ────────────────────────────────────────────────────
    print("\n[1/5] Loading raw data ...")
    raw_df = _load_raw_dataframe(data_path)

    # ── 2. Clean ────────────────────────────────────────────────────────────
    print("\n[2/5] Cleaning data ...")
    clean_df = clean_dataframe(raw_df)

    # ── 3. Build baskets ────────────────────────────────────────────────────
    print("\n[3/5] Building and filtering transaction baskets ...")
    basket_df, _ = build_baskets(clean_df)
    basket_df = filter_baskets(basket_df)

    # ── 4. Temporal split ───────────────────────────────────────────────────
    print("\n[4/5] Performing temporal train/test split ...")
    train_baskets, test_baskets = temporal_split(basket_df)

    # Unique products across all filtered baskets
    all_products_in_baskets: set[str] = set()
    for basket in train_baskets + test_baskets:
        all_products_in_baskets.update(basket)
    product_list = sorted(all_products_in_baskets)

    # ── 5. Persist artefacts ────────────────────────────────────────────────
    print("\n[5/5] Saving artefacts ...")

    clean_csv = data_path / "online_retail_clean.csv"
    train_pkl = data_path / "transactions_train.pkl"
    test_pkl = data_path / "transactions_test.pkl"
    products_pkl = data_path / "product_list.pkl"

    clean_df.to_csv(clean_csv, index=False)
    print(f"  Saved cleaned CSV   -> {clean_csv}")

    with open(train_pkl, "wb") as fh:
        pickle.dump(train_baskets, fh)
    print(f"  Saved train baskets -> {train_pkl}")

    with open(test_pkl, "wb") as fh:
        pickle.dump(test_baskets, fh)
    print(f"  Saved test baskets  -> {test_pkl}")

    with open(products_pkl, "wb") as fh:
        pickle.dump(product_list, fh)
    print(f"  Saved product list  -> {products_pkl}")

    # ── Build DatasetInfo ───────────────────────────────────────────────────
    from collections import Counter

    product_counts: Counter = Counter()
    for basket in train_baskets + test_baskets:
        product_counts.update(basket)
    top_products = product_counts.most_common(20)

    basket_df_sorted = basket_df.sort_values("InvoiceDate")
    date_start = basket_df_sorted["InvoiceDate"].iloc[0]
    date_end = basket_df_sorted["InvoiceDate"].iloc[-1]

    info = DatasetInfo(
        total_transactions=len(train_baskets) + len(test_baskets),
        unique_products=len(product_list),
        train_size=len(train_baskets),
        test_size=len(test_baskets),
        date_range_start=date_start.to_pydatetime() if hasattr(date_start, "to_pydatetime") else date_start,
        date_range_end=date_end.to_pydatetime() if hasattr(date_end, "to_pydatetime") else date_end,
        top_products=top_products,
    )
    return info


# ---------------------------------------------------------------------------
# Cached loader
# ---------------------------------------------------------------------------


def load_or_preprocess(data_dir: str = "data", force: bool = False) -> DatasetInfo:
    """Load cached preprocessing artefacts or run the full pipeline.

    If all expected pickle files are present in ``data_dir`` and ``force``
    is ``False``, the function reconstructs a :class:`DatasetInfo` from the
    cached files without re-running the expensive preprocessing pipeline.

    Parameters
    ----------
    data_dir : str, optional
        Directory containing data artefacts (default ``"data"``).
    force : bool, optional
        When ``True``, re-run preprocessing even if cached files exist
        (default ``False``).

    Returns
    -------
    DatasetInfo
        Summary statistics for the dataset.
    """
    data_path = Path(data_dir)
    train_pkl = data_path / "transactions_train.pkl"
    test_pkl = data_path / "transactions_test.pkl"
    products_pkl = data_path / "product_list.pkl"
    clean_csv = data_path / "online_retail_clean.csv"

    all_cached = all(p.exists() for p in [train_pkl, test_pkl, products_pkl, clean_csv])

    if all_cached and not force:
        print("Cached artefacts found -- loading from disk ...")
        with open(train_pkl, "rb") as fh:
            train_baskets: List[List[str]] = pickle.load(fh)
        with open(test_pkl, "rb") as fh:
            test_baskets: List[List[str]] = pickle.load(fh)
        with open(products_pkl, "rb") as fh:
            product_list: List[str] = pickle.load(fh)

        clean_df = pd.read_csv(clean_csv, low_memory=False)

        from collections import Counter

        product_counts: Counter = Counter()
        for basket in train_baskets + test_baskets:
            product_counts.update(basket)
        top_products = product_counts.most_common(20)

        # Attempt to recover date range from the clean CSV
        try:
            clean_df["InvoiceDate"] = pd.to_datetime(clean_df["InvoiceDate"], errors="coerce")
            date_start = clean_df["InvoiceDate"].dropna().min()
            date_end = clean_df["InvoiceDate"].dropna().max()
        except Exception:  # noqa: BLE001
            date_start = datetime.min
            date_end = datetime.max

        return DatasetInfo(
            total_transactions=len(train_baskets) + len(test_baskets),
            unique_products=len(product_list),
            train_size=len(train_baskets),
            test_size=len(test_baskets),
            date_range_start=date_start.to_pydatetime() if hasattr(date_start, "to_pydatetime") else date_start,
            date_range_end=date_end.to_pydatetime() if hasattr(date_end, "to_pydatetime") else date_end,
            top_products=top_products,
        )

    if force and all_cached:
        print("Force re-preprocessing requested -- ignoring cached files.")

    return preprocess(data_dir=data_dir)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Preprocess the Online Retail II dataset for bundle recommendation."
    )
    parser.add_argument(
        "--data-dir",
        default="data",
        help="Directory for data artefacts (default: data/)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run preprocessing even if cached artefacts exist.",
    )
    args = parser.parse_args()

    info = load_or_preprocess(data_dir=args.data_dir, force=args.force)
    print(info)

"""
train_model.py
==============
Trains the Apriori-based association rule model for the Smart Product Bundle
Recommendation System.

Workflow
--------
1. Encode transaction baskets with mlxtend's TransactionEncoder.
2. Mine frequent itemsets with the Apriori algorithm.
3. Generate association rules (support, confidence, lift).
4. Persist artefacts to disk and return them to the caller.

Usage
-----
    python train_model.py [--data-dir data] [--models-dir models] [--force]
"""

from __future__ import annotations

import argparse
import logging
import os
import pickle
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%H:%M:%S",
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_MIN_SUPPORT = 0.01
_DEFAULT_MIN_LIFT = 1.0
_DEFAULT_MIN_CONFIDENCE = 0.05
_RETRY_MIN_SUPPORT = 0.005  # fallback if no rules found on first attempt

ARTEFACT_ITEMSETS = "frequent_itemsets.pkl"
ARTEFACT_RULES = "association_rules.pkl"
ARTEFACT_METADATA = "model_metadata.pkl"


# ---------------------------------------------------------------------------
# Core training logic
# ---------------------------------------------------------------------------


def _encode_transactions(transactions: list[list[str]]) -> pd.DataFrame:
    """
    Transform a list-of-lists basket into a one-hot encoded DataFrame.

    Parameters
    ----------
    transactions : list[list[str]]
        Each inner list is one transaction (a set of product descriptions).

    Returns
    -------
    pd.DataFrame
        Boolean one-hot encoded matrix (rows = transactions, columns = products).
    """
    logger.info("Encoding %d transactions...", len(transactions))
    te = TransactionEncoder()
    te_array = te.fit_transform(transactions)
    df = pd.DataFrame(te_array, columns=te.columns_)
    logger.info("Encoded basket shape: %s", df.shape)
    return df


def _mine_itemsets(
    basket_df: pd.DataFrame,
    min_support: float,
) -> pd.DataFrame:
    """
    Run the Apriori algorithm to discover frequent itemsets.

    Parameters
    ----------
    basket_df : pd.DataFrame
        One-hot encoded basket DataFrame.
    min_support : float
        Minimum support threshold (0-1).

    Returns
    -------
    pd.DataFrame
        Frequent itemsets with columns ``support`` and ``itemsets``.
    """
    logger.info("Mining frequent itemsets (min_support=%.4f)...", min_support)
    itemsets = apriori(
        basket_df,
        min_support=min_support,
        use_colnames=True,
        verbose=0,
        low_memory=False,
    )
    logger.info("Found %d frequent itemsets.", len(itemsets))
    return itemsets


def _generate_rules(
    itemsets: pd.DataFrame,
    min_lift: float,
    min_confidence: float,
) -> pd.DataFrame:
    """
    Generate association rules from frequent itemsets.

    Parameters
    ----------
    itemsets : pd.DataFrame
        Output of :func:`_mine_itemsets`.
    min_lift : float
        Minimum lift threshold.
    min_confidence : float
        Minimum confidence threshold.

    Returns
    -------
    pd.DataFrame
        Association rules with support, confidence, lift, leverage, conviction.
    """
    logger.info(
        "Generating rules (min_lift=%.2f, min_confidence=%.2f)...",
        min_lift,
        min_confidence,
    )
    # mlxtend requires at least some 2-itemsets to build rules
    if len(itemsets[itemsets["itemsets"].apply(len) >= 2]) == 0:
        logger.warning("No 2+ itemsets found; cannot generate rules.")
        return pd.DataFrame(
            columns=[
                "antecedents",
                "consequents",
                "antecedent support",
                "consequent support",
                "support",
                "confidence",
                "lift",
                "leverage",
                "conviction",
                "antecedents_str",
                "consequents_str",
                "rule_label",
            ]
        )

    rules = association_rules(itemsets, metric="lift", min_threshold=min_lift)

    # Apply additional confidence filter
    rules = rules[rules["confidence"] >= min_confidence].copy()

    # Remove trivial rules (empty antecedents or consequents)
    rules = rules[
        (rules["antecedents"].apply(len) > 0)
        & (rules["consequents"].apply(len) > 0)
    ].copy()

    # Derive human-readable string representations
    rules["antecedents_str"] = rules["antecedents"].apply(
        lambda x: " + ".join(sorted(x))
    )
    rules["consequents_str"] = rules["consequents"].apply(
        lambda x: " + ".join(sorted(x))
    )
    rules["rule_label"] = rules["antecedents_str"] + " -> " + rules["consequents_str"]

    # Sort by lift DESC then confidence DESC
    rules = rules.sort_values(["lift", "confidence"], ascending=False).reset_index(
        drop=True
    )

    logger.info("Generated %d association rules.", len(rules))
    return rules


def train_model(
    transactions: list[list[str]],
    min_support: float = _DEFAULT_MIN_SUPPORT,
    min_lift: float = _DEFAULT_MIN_LIFT,
    min_confidence: float = _DEFAULT_MIN_CONFIDENCE,
    models_dir: str = "models",
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    Full training pipeline: encode -> mine itemsets -> generate rules -> persist.

    Parameters
    ----------
    transactions : list[list[str]]
        Train basket list returned by ``data_preprocessing.build_baskets``.
    min_support : float
        Minimum support for Apriori (default 0.01).
    min_lift : float
        Minimum lift for rule generation (default 1.0).
    min_confidence : float
        Minimum confidence for rule generation (default 0.05).
    models_dir : str
        Directory where model artefacts will be saved.

    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame, dict]
        (frequent_itemsets, association_rules, metadata)
    """
    models_path = Path(models_dir)
    models_path.mkdir(parents=True, exist_ok=True)

    # --- Step 1: Encode ---
    basket_df = _encode_transactions(transactions)

    # --- Step 2: Mine itemsets ---
    itemsets = _mine_itemsets(basket_df, min_support)

    # --- Step 3: Generate rules; retry with lower support if none found ---
    rules = _generate_rules(itemsets, min_lift, min_confidence)
    if len(rules) == 0 and min_support > _RETRY_MIN_SUPPORT:
        logger.warning(
            "No rules found with min_support=%.4f. Retrying with %.4f...",
            min_support,
            _RETRY_MIN_SUPPORT,
        )
        itemsets = _mine_itemsets(basket_df, _RETRY_MIN_SUPPORT)
        rules = _generate_rules(itemsets, min_lift, min_confidence)
        if len(rules) == 0:
            logger.error(
                "Still no rules generated. The dataset may be too sparse or "
                "the thresholds are too strict."
            )

    # --- Step 4: Build metadata ---
    metadata = {
        "min_support": min_support,
        "min_lift": min_lift,
        "min_confidence": min_confidence,
        "num_itemsets": len(itemsets),
        "num_rules": len(rules),
        "num_transactions": len(transactions),
        "training_date": datetime.now().isoformat(timespec="seconds"),
        "avg_support": float(rules["support"].mean()) if len(rules) else 0.0,
        "avg_confidence": float(rules["confidence"].mean()) if len(rules) else 0.0,
        "avg_lift": float(rules["lift"].mean()) if len(rules) else 0.0,
    }

    # --- Step 5: Persist ---
    logger.info("Saving artefacts to '%s'...", models_dir)
    with open(models_path / ARTEFACT_ITEMSETS, "wb") as f:
        pickle.dump(itemsets, f)
    with open(models_path / ARTEFACT_RULES, "wb") as f:
        pickle.dump(rules, f)
    with open(models_path / ARTEFACT_METADATA, "wb") as f:
        pickle.dump(metadata, f)
    logger.info("Artefacts saved successfully.")

    return itemsets, rules, metadata


# ---------------------------------------------------------------------------
# Loading helpers
# ---------------------------------------------------------------------------


def load_model(
    models_dir: str = "models",
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    Load persisted model artefacts from disk.

    Parameters
    ----------
    models_dir : str
        Directory where artefacts were saved by :func:`train_model`.

    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame, dict]
        (frequent_itemsets, association_rules, metadata)

    Raises
    ------
    FileNotFoundError
        If any required artefact is missing.
    """
    models_path = Path(models_dir)
    required = [ARTEFACT_ITEMSETS, ARTEFACT_RULES, ARTEFACT_METADATA]
    missing = [f for f in required if not (models_path / f).exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing model artefacts in '{models_dir}': {missing}. "
            "Run train_model() first."
        )

    logger.info("Loading model artefacts from '%s'...", models_dir)
    with open(models_path / ARTEFACT_ITEMSETS, "rb") as f:
        itemsets = pickle.load(f)
    with open(models_path / ARTEFACT_RULES, "rb") as f:
        rules = pickle.load(f)
    with open(models_path / ARTEFACT_METADATA, "rb") as f:
        metadata = pickle.load(f)

    logger.info(
        "Loaded %d itemsets and %d rules.", len(itemsets), len(rules)
    )
    return itemsets, rules, metadata


def train_or_load(
    transactions: Optional[list[list[str]]] = None,
    models_dir: str = "models",
    data_dir: str = "data",
    force: bool = False,
    min_support: float = _DEFAULT_MIN_SUPPORT,
    min_lift: float = _DEFAULT_MIN_LIFT,
    min_confidence: float = _DEFAULT_MIN_CONFIDENCE,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    Convenience wrapper: load cached model if available, otherwise train.

    Parameters
    ----------
    transactions : list[list[str]] or None
        Training transactions.  If *None* and training is needed, the
        function attempts to load them from ``<data_dir>/transactions_train.pkl``.
    models_dir : str
        Directory for model artefacts.
    data_dir : str
        Directory for data artefacts (used when ``transactions`` is None).
    force : bool
        If *True*, retrain even if artefacts already exist.
    min_support, min_lift, min_confidence : float
        Passed through to :func:`train_model` when training is needed.

    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame, dict]
        (frequent_itemsets, association_rules, metadata)
    """
    models_path = Path(models_dir)
    artefacts_exist = all(
        (models_path / f).exists()
        for f in [ARTEFACT_ITEMSETS, ARTEFACT_RULES, ARTEFACT_METADATA]
    )

    if artefacts_exist and not force:
        logger.info("Cached model artefacts found -- loading from disk.")
        return load_model(models_dir)

    # Need to train
    if transactions is None:
        train_pkl = Path(data_dir) / "transactions_train.pkl"
        if not train_pkl.exists():
            raise FileNotFoundError(
                f"No transactions provided and '{train_pkl}' not found. "
                "Run data_preprocessing.py first."
            )
        logger.info("Loading training transactions from '%s'...", train_pkl)
        with open(train_pkl, "rb") as f:
            transactions = pickle.load(f)

    logger.info(
        "Training model on %d transactions...", len(transactions)
    )
    return train_model(
        transactions,
        min_support=min_support,
        min_lift=min_lift,
        min_confidence=min_confidence,
        models_dir=models_dir,
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Train the Apriori association rule model."
    )
    parser.add_argument(
        "--data-dir", default="data", help="Directory containing data artefacts."
    )
    parser.add_argument(
        "--models-dir", default="models", help="Directory to save model artefacts."
    )
    parser.add_argument(
        "--force", action="store_true", help="Retrain even if artefacts exist."
    )
    parser.add_argument(
        "--min-support",
        type=float,
        default=_DEFAULT_MIN_SUPPORT,
        help=f"Minimum support (default {_DEFAULT_MIN_SUPPORT}).",
    )
    parser.add_argument(
        "--min-lift",
        type=float,
        default=_DEFAULT_MIN_LIFT,
        help=f"Minimum lift (default {_DEFAULT_MIN_LIFT}).",
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=_DEFAULT_MIN_CONFIDENCE,
        help=f"Minimum confidence (default {_DEFAULT_MIN_CONFIDENCE}).",
    )
    args = parser.parse_args()

    itemsets, rules, meta = train_or_load(
        transactions=None,
        models_dir=args.models_dir,
        data_dir=args.data_dir,
        force=args.force,
        min_support=args.min_support,
        min_lift=args.min_lift,
        min_confidence=args.min_confidence,
    )

    print("\n=== Model Training Complete ===")
    print(f"  Frequent itemsets : {meta['num_itemsets']}")
    print(f"  Association rules : {meta['num_rules']}")
    print(f"  Avg support       : {meta['avg_support']:.4f}")
    print(f"  Avg confidence    : {meta['avg_confidence']:.4f}")
    print(f"  Avg lift          : {meta['avg_lift']:.4f}")
    print(f"  Training date     : {meta['training_date']}")
    if len(rules) > 0:
        print("\n  Top 5 rules by lift:")
        for _, row in rules.head(5).iterrows():
            print(
                f"    {row['antecedents_str']} -> {row['consequents_str']}"
                f"  (lift={row['lift']:.2f}, conf={row['confidence']:.2f})"
            )

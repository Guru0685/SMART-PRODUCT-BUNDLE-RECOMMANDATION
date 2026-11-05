"""
tests/conftest.py
-----------------
Shared pytest fixtures for the Smart Product Bundle Recommendation System tests.
"""
from __future__ import annotations

import pandas as pd
import pytest


@pytest.fixture
def sample_rules_df() -> pd.DataFrame:
    """A DataFrame of 10 synthetic association rules for unit testing."""
    rules = [
        {
            "antecedents": frozenset({"WHITE HANGING HEART T-LIGHT HOLDER"}),
            "consequents": frozenset({"RED WOOLLY HOTTIE WHITE HEART"}),
            "antecedent support": 0.30,
            "consequent support": 0.25,
            "support": 0.15,
            "confidence": 0.50,
            "lift": 2.00,
            "leverage": 0.075,
            "conviction": 1.50,
        },
        {
            "antecedents": frozenset({"CREAM CUPID HEARTS COAT HANGER"}),
            "consequents": frozenset({"RED WOOLLY HOTTIE WHITE HEART"}),
            "antecedent support": 0.20,
            "consequent support": 0.25,
            "support": 0.12,
            "confidence": 0.60,
            "lift": 2.40,
            "leverage": 0.070,
            "conviction": 1.90,
        },
        {
            "antecedents": frozenset({"HEART OF WICKER SMALL"}),
            "consequents": frozenset({"HEART OF WICKER LARGE"}),
            "antecedent support": 0.18,
            "consequent support": 0.22,
            "support": 0.10,
            "confidence": 0.55,
            "lift": 2.50,
            "leverage": 0.060,
            "conviction": 1.73,
        },
        {
            "antecedents": frozenset({"CREAM CUPID HEARTS COAT HANGER"}),
            "consequents": frozenset({"WHITE HANGING HEART T-LIGHT HOLDER"}),
            "antecedent support": 0.20,
            "consequent support": 0.30,
            "support": 0.11,
            "confidence": 0.55,
            "lift": 1.83,
            "leverage": 0.050,
            "conviction": 1.55,
        },
        {
            "antecedents": frozenset({"ROUND SNACK BOXES SET OF 4 WOODLAND"}),
            "consequents": frozenset({"ROUND SNACK BOXES SET OF 4 SKULLS"}),
            "antecedent support": 0.15,
            "consequent support": 0.16,
            "support": 0.08,
            "confidence": 0.53,
            "lift": 3.31,
            "leverage": 0.056,
            "conviction": 1.79,
        },
        {
            "antecedents": frozenset({"JUMBO BAG RED RETROSPOT"}),
            "consequents": frozenset({"JUMBO BAG PINK POLKADOT"}),
            "antecedent support": 0.25,
            "consequent support": 0.23,
            "support": 0.09,
            "confidence": 0.36,
            "lift": 1.56,
            "leverage": 0.032,
            "conviction": 1.20,
        },
        {
            "antecedents": frozenset({"SET OF 3 CAKE TINS PANTRY DESIGN"}),
            "consequents": frozenset({"SET OF 3 CAKE TINS VINTAGE DESIGN"}),
            "antecedent support": 0.12,
            "consequent support": 0.13,
            "support": 0.07,
            "confidence": 0.58,
            "lift": 4.46,
            "leverage": 0.054,
            "conviction": 2.07,
        },
        {
            "antecedents": frozenset({"STRAWBERRY CERAMIC TRINKET BOX"}),
            "consequents": frozenset({"REGENCY CAKESTAND 3 TIER"}),
            "antecedent support": 0.14,
            "consequent support": 0.18,
            "support": 0.06,
            "confidence": 0.43,
            "lift": 2.39,
            "leverage": 0.035,
            "conviction": 1.44,
        },
        {
            "antecedents": frozenset({"ALARM CLOCK BAKELIKE GREEN"}),
            "consequents": frozenset({"ALARM CLOCK BAKELIKE RED"}),
            "antecedent support": 0.11,
            "consequent support": 0.12,
            "support": 0.05,
            "confidence": 0.45,
            "lift": 3.75,
            "leverage": 0.037,
            "conviction": 1.60,
        },
        {
            "antecedents": frozenset({"SMALL POPCORN HOLDER"}),
            "consequents": frozenset({"LARGE POPCORN HOLDER"}),
            "antecedent support": 0.10,
            "consequent support": 0.11,
            "support": 0.04,
            "confidence": 0.40,
            "lift": 3.64,
            "leverage": 0.029,
            "conviction": 1.48,
        },
    ]
    df = pd.DataFrame(rules)
    # add helper string columns like train_model.py would
    df["antecedents_str"] = df["antecedents"].apply(lambda x: " + ".join(sorted(x)))
    df["consequents_str"] = df["consequents"].apply(lambda x: " + ".join(sorted(x)))
    df["rule_label"] = df["antecedents_str"] + " → " + df["consequents_str"]
    return df


@pytest.fixture
def sample_transactions() -> list[list[str]]:
    """50 synthetic transaction baskets for unit testing."""
    products = [
        "WHITE HANGING HEART T-LIGHT HOLDER",
        "RED WOOLLY HOTTIE WHITE HEART",
        "CREAM CUPID HEARTS COAT HANGER",
        "HEART OF WICKER SMALL",
        "HEART OF WICKER LARGE",
        "JUMBO BAG RED RETROSPOT",
        "JUMBO BAG PINK POLKADOT",
        "SET OF 3 CAKE TINS PANTRY DESIGN",
        "SET OF 3 CAKE TINS VINTAGE DESIGN",
        "REGENCY CAKESTAND 3 TIER",
        "ALARM CLOCK BAKELIKE GREEN",
        "ALARM CLOCK BAKELIKE RED",
        "SMALL POPCORN HOLDER",
        "LARGE POPCORN HOLDER",
        "STRAWBERRY CERAMIC TRINKET BOX",
    ]

    import random
    random.seed(42)
    transactions = []
    for _ in range(50):
        n = random.randint(2, 6)
        basket = random.sample(products, min(n, len(products)))
        transactions.append(basket)
    return transactions

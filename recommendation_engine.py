"""
recommendation_engine.py
========================
Core recommendation logic for the Smart Product Bundle Recommendation System.

This module provides the BundleRecommender class, which wraps a set of
mlxtend-generated association rules and exposes fast product-bundle
recommendations, product search, and top-bundle queries.
"""

from __future__ import annotations

import pandas as pd
from dataclasses import dataclass, field
from collections import defaultdict
from typing import List, Optional


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class RecommendationResult:
    """A single bundle recommendation derived from one association rule.

    Attributes
    ----------
    antecedents : frozenset
        The set of products that triggered this rule (i.e. what the customer
        already has in their basket).
    consequents : frozenset
        The set of products recommended by this rule.
    support : float
        Fraction of all transactions that contain both antecedents and
        consequents together.
    confidence : float
        P(consequents | antecedents) -- how often the rule is correct.
    lift : float
        Ratio of the observed support to the expected support if antecedents
        and consequents were statistically independent.  Values > 1 indicate
        a positive association.
    explanation : str
        A human-readable sentence describing the recommendation.
    bundle_name : str
        A short display name for the bundle, e.g. ``"Product A + Product B"``.
    """

    antecedents: frozenset
    consequents: frozenset
    support: float
    confidence: float
    lift: float
    explanation: str = field(default="")
    bundle_name: str = field(default="")

    def __post_init__(self) -> None:
        """Auto-generate explanation and bundle_name if not provided."""
        ant_list = sorted(self.antecedents)
        con_list = sorted(self.consequents)

        if not self.bundle_name:
            self.bundle_name = " + ".join(ant_list + con_list)

        if not self.explanation:
            ant_str = ", ".join(f"[{p}]" for p in ant_list)
            con_str = ", ".join(f"[{p}]" for p in con_list)
            self.explanation = (
                f"Customers who bought {ant_str} also frequently bought "
                f"{con_str} in the same transaction "
                f"(Confidence: {self.confidence * 100:.0f}%, "
                f"Lift: {self.lift:.1f}x)."
            )


# ---------------------------------------------------------------------------
# Recommender
# ---------------------------------------------------------------------------

class BundleRecommender:
    """Recommendation engine built on top of mlxtend association rules.

    Parameters
    ----------
    rules_df : pd.DataFrame
        A DataFrame produced by ``mlxtend.frequent_patterns.association_rules``.
        Expected columns: ``antecedents``, ``consequents``, ``support``,
        ``confidence``, ``lift``.  The ``antecedents`` and ``consequents``
        columns must contain ``frozenset`` values.
    top_n : int, optional
        Default number of results to return when ``top_n`` is not passed
        explicitly to a query method.  Defaults to ``10``.

    Notes
    -----
    An internal index ``_antecedent_index`` maps every individual product
    that appears as an antecedent to the list of rule row-indices that
    reference it.  This avoids a full DataFrame scan for each query and
    keeps lookups O(k) where k is the number of rules that involve the
    queried product.
    """

    def __init__(self, rules_df: pd.DataFrame, top_n: int = 10) -> None:
        if rules_df is None or rules_df.empty:
            raise ValueError("rules_df must be a non-empty DataFrame.")

        required_cols = {"antecedents", "consequents", "support", "confidence", "lift"}
        missing = required_cols - set(rules_df.columns)
        if missing:
            raise ValueError(f"rules_df is missing required columns: {missing}")

        self._rules: pd.DataFrame = rules_df.reset_index(drop=True)
        self._top_n: int = top_n

        # Build index: product_name -> [row indices in self._rules]
        self._antecedent_index: dict[str, list[int]] = defaultdict(list)
        for idx, row in self._rules.iterrows():
            for product in row["antecedents"]:
                self._antecedent_index[product].append(idx)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_recommendations(
        self,
        selected_products: List[str],
        min_confidence: float = 0.1,
        min_lift: float = 1.0,
        top_n: Optional[int] = None,
        k: Optional[int] = None,
    ) -> List[RecommendationResult]:
        """Return bundle recommendations given the user's current product selection.

        The method finds every association rule whose antecedent is a subset of
        ``selected_products`` (i.e. strict multi-item rules) **and** every rule
        whose antecedent is a single product that appears in
        ``selected_products``.  Duplicate rules are deduplicated by rule index
        before ranking.

        Parameters
        ----------
        selected_products : list[str]
            Products currently selected / already in the basket.
        min_confidence : float, optional
            Minimum confidence threshold.  Defaults to ``0.1``.
        min_lift : float, optional
            Minimum lift threshold.  Rules with lift below this value are
            excluded.  Defaults to ``1.0``.
        top_n : int, optional
            Maximum number of results to return.  Falls back to the instance
            default when omitted.

        Returns
        -------
        list[RecommendationResult]
            Recommendations sorted by lift (descending), then confidence
            (descending).  Returns an empty list when no matching rules exist.
        """
        if not selected_products:
            return []

        if k is not None and top_n is None:
            top_n = k
        n = top_n if top_n is not None else self._top_n
        selected_set = frozenset(selected_products)

        # Collect candidate rule indices via the antecedent index.
        candidate_indices: set[int] = set()
        for product in selected_products:
            candidate_indices.update(self._antecedent_index.get(product, []))

        if not candidate_indices:
            return []

        results: List[RecommendationResult] = []

        for idx in candidate_indices:
            row = self._rules.loc[idx]
            antecedents: frozenset = row["antecedents"]
            consequents: frozenset = row["consequents"]
            confidence: float = float(row["confidence"])
            lift: float = float(row["lift"])
            support: float = float(row["support"])

            # The rule's antecedent must be a subset of the selected products.
            if not antecedents.issubset(selected_set):
                continue

            # Apply metric thresholds.
            if confidence < min_confidence or lift < min_lift:
                continue

            # Exclude consequents that are already selected.
            new_consequents = consequents - selected_set
            if not new_consequents:
                continue

            results.append(
                RecommendationResult(
                    antecedents=antecedents,
                    consequents=new_consequents,
                    support=support,
                    confidence=confidence,
                    lift=lift,
                )
            )

        # Sort: lift DESC, then confidence DESC.
        results.sort(key=lambda r: (-r.lift, -r.confidence))

        return results[:n]

    def search_products(self, query: str, all_products: List[str]) -> List[str]:
        """Case-insensitive substring search over a product catalogue.

        Results are ranked by relevance:

        1. **Exact match** (case-insensitive)
        2. **Starts with** query (case-insensitive)
        3. **Contains** query (case-insensitive)

        Parameters
        ----------
        query : str
            The search string entered by the user.
        all_products : list[str]
            The full catalogue of product description strings.

        Returns
        -------
        list[str]
            Matching products sorted by relevance tier, then alphabetically
            within each tier.  Returns an empty list when there are no matches.
        """
        q = query.strip().lower()
        if not q:
            return []

        exact: List[str] = []
        starts: List[str] = []
        contains: List[str] = []

        for product in all_products:
            pl = product.lower()
            if pl == q:
                exact.append(product)
            elif pl.startswith(q):
                starts.append(product)
            elif q in pl:
                contains.append(product)

        return sorted(exact) + sorted(starts) + sorted(contains)

    def get_top_bundles(self, n: int = 20) -> List[RecommendationResult]:
        """Return the top N rules by lift (descending).

        Useful for surfacing globally popular product bundles regardless of
        what the user has currently selected.

        Parameters
        ----------
        n : int, optional
            Number of bundles to return.  Defaults to ``20``.

        Returns
        -------
        list[RecommendationResult]
            Top-N rules converted to :class:`RecommendationResult` objects,
            sorted by lift DESC.
        """
        sorted_rules = self._rules.sort_values(
            by=["lift", "confidence"], ascending=[False, False]
        ).head(n)

        return [self._row_to_result(row) for _, row in sorted_rules.iterrows()]

    def get_frequent_pairs(self, n: int = 20) -> List[RecommendationResult]:
        """Return the top N 2-itemset rules by support (descending).

        A 2-itemset rule is one where the antecedent contains exactly one
        product and the consequent contains exactly one product (i.e. the pair
        together has high overall co-occurrence frequency).

        Parameters
        ----------
        n : int, optional
            Number of pairs to return.  Defaults to ``20``.

        Returns
        -------
        list[RecommendationResult]
            Top-N 2-itemset rules sorted by support DESC.
        """
        mask = (
            self._rules["antecedents"].apply(len) == 1
        ) & (
            self._rules["consequents"].apply(len) == 1
        )
        pairs = self._rules[mask].sort_values(by="support", ascending=False).head(n)

        return [self._row_to_result(row) for _, row in pairs.iterrows()]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _row_to_result(self, row: pd.Series) -> RecommendationResult:
        """Convert a single rules DataFrame row into a RecommendationResult.

        Parameters
        ----------
        row : pd.Series
            A row from ``self._rules``.

        Returns
        -------
        RecommendationResult
        """
        return RecommendationResult(
            antecedents=row["antecedents"],
            consequents=row["consequents"],
            support=float(row["support"]),
            confidence=float(row["confidence"]),
            lift=float(row["lift"]),
        )

    @property
    def all_products(self) -> List[str]:
        """Return a sorted list of all unique products present in the rules."""
        if not hasattr(self, "_all_products_cache"):
            s = set()
            for row in self._rules.itertuples():
                s.update(row.antecedents)
                s.update(row.consequents)
            self._all_products_cache = sorted(s)
        return self._all_products_cache


# ---------------------------------------------------------------------------
# Demo / smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    """Quick smoke-test using synthetic association rules.

    Run this script directly to verify the module is working correctly
    without requiring a full dataset:

        python recommendation_engine.py
    """

    # ------------------------------------------------------------------
    # 1.  Build a tiny synthetic rules DataFrame that mimics mlxtend output.
    # ------------------------------------------------------------------
    synthetic_rules = pd.DataFrame(
        {
            "antecedents": [
                frozenset(["WHITE HANGING HEART T-LIGHT HOLDER"]),
                frozenset(["RED WOOLLY HOTTIE WHITE HEART."]),
                frozenset(["SET 7 BABUSHKA NESTING BOXES"]),
                frozenset(["WHITE HANGING HEART T-LIGHT HOLDER", "RED WOOLLY HOTTIE WHITE HEART."]),
                frozenset(["JUMBO BAG RED RETROSPOT"]),
                frozenset(["PARTY BUNTING"]),
                frozenset(["PARTY BUNTING"]),
                frozenset(["LUNCH BAG RED RETROSPOT"]),
            ],
            "consequents": [
                frozenset(["RED WOOLLY HOTTIE WHITE HEART."]),
                frozenset(["WHITE HANGING HEART T-LIGHT HOLDER"]),
                frozenset(["CREAM CUPID HEARTS COAT HANGER"]),
                frozenset(["SET 7 BABUSHKA NESTING BOXES"]),
                frozenset(["LUNCH BAG RED RETROSPOT"]),
                frozenset(["JUMBO BAG RED RETROSPOT"]),
                frozenset(["LUNCH BAG RED RETROSPOT"]),
                frozenset(["JUMBO BAG RED RETROSPOT"]),
            ],
            "support":    [0.05, 0.05, 0.04, 0.03, 0.08, 0.06, 0.05, 0.08],
            "confidence": [0.85, 0.80, 0.72, 0.90, 0.65, 0.70, 0.55, 0.65],
            "lift":       [3.2,  3.2,  2.8,  4.1,  2.1,  2.3,  1.9,  2.1],
        }
    )

    # ------------------------------------------------------------------
    # 2.  Initialise the recommender.
    # ------------------------------------------------------------------
    recommender = BundleRecommender(rules_df=synthetic_rules, top_n=10)

    print("=" * 70)
    print("  Smart Bundle Recommender -- demo")
    print("=" * 70)

    # ------------------------------------------------------------------
    # 3.  get_recommendations demo.
    # ------------------------------------------------------------------
    basket = ["WHITE HANGING HEART T-LIGHT HOLDER", "RED WOOLLY HOTTIE WHITE HEART."]
    print(f"\n[get_recommendations] Basket: {basket}\n")
    recs = recommender.get_recommendations(basket, min_confidence=0.5, min_lift=1.0)
    if recs:
        for r in recs:
            print(f"  Bundle  : {r.bundle_name}")
            print(f"  Lift    : {r.lift:.2f}x  |  Confidence: {r.confidence * 100:.0f}%")
            print(f"  Explain : {r.explanation}")
            print()
    else:
        print("  No recommendations found for this basket.\n")

    # ------------------------------------------------------------------
    # 4.  search_products demo.
    # ------------------------------------------------------------------
    all_products = list(
        set(p for fs in synthetic_rules["antecedents"] for p in fs)
        | set(p for fs in synthetic_rules["consequents"] for p in fs)
    )
    query = "bag"
    print(f"[search_products] Query: '{query}'")
    matches = recommender.search_products(query, all_products)
    print(f"  Matches : {matches}\n")

    # ------------------------------------------------------------------
    # 5.  get_top_bundles demo.
    # ------------------------------------------------------------------
    print("[get_top_bundles] Top 3 bundles by lift:")
    for r in recommender.get_top_bundles(n=3):
        print(f"  {r.bundle_name}  (lift={r.lift:.2f})")

    # ------------------------------------------------------------------
    # 6.  get_frequent_pairs demo.
    # ------------------------------------------------------------------
    print("\n[get_frequent_pairs] Top 3 frequent pairs by support:")
    for r in recommender.get_frequent_pairs(n=3):
        print(f"  {r.bundle_name}  (support={r.support:.3f})")

    print("\n" + "=" * 70)
    print("  All checks passed.")
    print("=" * 70)



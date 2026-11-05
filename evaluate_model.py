"""
evaluate_model.py
-----------------
Evaluation module for the Smart Product Bundle Recommendation System.

Evaluates recommendation quality using held-out test transactions by splitting
each transaction into query items and ground truth items, then measuring how
well the recommender recovers the ground truth from the query.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class EvaluationResult:
    """Container for all evaluation metrics produced by :func:`evaluate_recommender`.

    Attributes
    ----------
    precision_at_k:
        Mean fraction of the top-K recommendations that appear in the ground
        truth, averaged over all evaluated test transactions.
    recall_at_k:
        Mean fraction of ground-truth items that were successfully recommended,
        averaged over all evaluated test transactions.
    hit_rate_at_k:
        Fraction of test transactions where at least one recommended item
        appears in the ground truth.
    coverage:
        Fraction of unique products seen in the test set that appear in at
        least one recommendation (across *all* evaluated transactions).
    avg_support:
        Mean support value of every association rule used to produce
        recommendations across all evaluated transactions.
    avg_confidence:
        Mean confidence of every rule used.
    avg_lift:
        Mean lift of every rule used.
    k:
        The truncation depth used during evaluation.
    num_test_transactions:
        Total number of test transactions considered (those with >= 2 items).
    num_evaluated:
        Number of transactions for which at least one recommendation was made.
    total_recommendations:
        Total number of recommendation records generated across all transactions.
    evaluated:
        ``True`` if the evaluation completed with at least some recommendations.
    notes:
        Human-readable notes about data quality or evaluation caveats.
    """

    precision_at_k: float = 0.0
    recall_at_k: float = 0.0
    hit_rate_at_k: float = 0.0
    coverage: float = 0.0
    avg_support: float = 0.0
    avg_confidence: float = 0.0
    avg_lift: float = 0.0
    k: int = 5
    num_test_transactions: int = 0
    num_evaluated: int = 0
    total_recommendations: int = 0
    evaluated: bool = False
    notes: str = ""


# ---------------------------------------------------------------------------
# Core evaluation function
# ---------------------------------------------------------------------------

def evaluate_recommender(
    recommender: Any,
    test_transactions: List[List[str]],
    k: int = 5,
    min_confidence: float = 0.1,
    min_lift: float = 1.0,
) -> EvaluationResult:
    """Evaluate a bundle recommender against held-out test transactions.

    For each test transaction that contains at least 2 items the transaction is
    split in half:

    * **Query items** - the first ``ceil(n/2)`` items are used as input to the
      recommender.
    * **Ground truth items** - the remaining items are used to judge whether the
      recommendations are correct.

    The recommender is called via ``recommender.get_recommendations(query_items,
    k=k, min_confidence=min_confidence, min_lift=min_lift)``.  The returned
    object is expected to be a :class:`pandas.DataFrame` with at least the
    columns ``consequents``, ``support``, ``confidence``, and ``lift``.  If the
    recommender returns no rules for a transaction that transaction is skipped
    for metric aggregation (but still counted in ``num_test_transactions``).

    Parameters
    ----------
    recommender:
        An instance that exposes a ``get_recommendations`` method compatible
        with the description above.
    test_transactions:
        A list of transactions, where each transaction is a list of product
        name strings.
    k:
        Maximum number of recommendations to request and to use when computing
        Precision@K.
    min_confidence:
        Minimum confidence threshold forwarded to the recommender.
    min_lift:
        Minimum lift threshold forwarded to the recommender.

    Returns
    -------
    EvaluationResult
        Populated dataclass with all computed metrics.
    """

    # Filter to transactions with at least 2 items (needed for a meaningful split)
    eligible = [t for t in test_transactions if len(t) >= 2]
    num_test = len(eligible)

    result = EvaluationResult(k=k, num_test_transactions=num_test)

    if num_test == 0:
        result.notes = (
            "No test transactions with 2 or more items were found. "
            "Evaluation could not be performed."
        )
        logger.warning(result.notes)
        return result

    logger.info(
        "Starting evaluation: %d eligible test transactions, k=%d, "
        "min_confidence=%.3f, min_lift=%.3f",
        num_test, k, min_confidence, min_lift,
    )

    # Accumulators
    precisions: List[float] = []
    recalls: List[float] = []
    hits: List[int] = []
    all_supports: List[float] = []
    all_confidences: List[float] = []
    all_lifts: List[float] = []
    total_recs: int = 0

    # For coverage: collect all unique products in test set and those recommended
    all_test_products: set = set()
    all_recommended_products: set = set()

    num_evaluated: int = 0

    for idx, transaction in enumerate(eligible):
        # Collect test products for coverage metric
        all_test_products.update(transaction)

        # --- Split transaction ---
        split_point = math.ceil(len(transaction) / 2)
        query_items = transaction[:split_point]
        ground_truth = set(transaction[split_point:])

        logger.debug(
            "Transaction %d/%d | query=%s | ground_truth=%s",
            idx + 1, num_test, query_items, ground_truth,
        )

        # --- Get recommendations ---
        try:
            recs_df = recommender.get_recommendations(
                query_items,
                k=k,
                min_confidence=min_confidence,
                min_lift=min_lift,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Recommender raised an exception for transaction %d: %s - skipping.",
                idx + 1, exc,
            )
            continue

        # Validate result
        if recs_df is None:
            continue
        if isinstance(recs_df, list):
            if len(recs_df) == 0:
                continue
            rows = []
            for item in recs_df:
                if hasattr(item, "consequents"):
                    rows.append({
                        "consequents": item.consequents,
                        "support": item.support,
                        "confidence": item.confidence,
                        "lift": item.lift,
                    })
                elif isinstance(item, dict):
                    rows.append(item)
            recs_df = pd.DataFrame(rows)

        if isinstance(recs_df, pd.DataFrame) and recs_df.empty:
            continue

        if not isinstance(recs_df, pd.DataFrame):
            continue

        required_cols = {"consequents", "support", "confidence", "lift"}
        missing = required_cols - set(recs_df.columns)
        if missing:
            logger.warning(
                "Recommendations DataFrame is missing columns %s for transaction %d - skipping.",
                missing, idx + 1,
            )
            continue

        # --- Extract recommended product names ---
        # consequents may be frozensets, sets, lists, or plain strings
        recommended_names: List[str] = []
        for val in recs_df["consequents"]:
            if isinstance(val, (frozenset, set, list, tuple)):
                recommended_names.extend(str(v) for v in val)
            else:
                recommended_names.append(str(val))

        # Deduplicate while preserving order, then truncate to k
        seen: set = set()
        deduped: List[str] = []
        for name in recommended_names:
            if name not in seen:
                seen.add(name)
                deduped.append(name)
        recommended_top_k = deduped[:k]

        if not recommended_top_k:
            logger.debug("Empty recommendation list after processing for transaction %d.", idx + 1)
            continue

        num_evaluated += 1
        total_recs += len(recommended_top_k)
        all_recommended_products.update(recommended_top_k)

        # --- Metrics for this transaction ---
        hits_this = sum(1 for name in recommended_top_k if name in ground_truth)

        precision = hits_this / k
        recall = hits_this / len(ground_truth) if ground_truth else 0.0
        hit = 1 if hits_this > 0 else 0

        precisions.append(precision)
        recalls.append(recall)
        hits.append(hit)

        # --- Rule-quality metrics ---
        supports = recs_df["support"].dropna().tolist()
        confidences = recs_df["confidence"].dropna().tolist()
        lifts = recs_df["lift"].dropna().tolist()

        all_supports.extend(supports)
        all_confidences.extend(confidences)
        all_lifts.extend(lifts)

        logger.debug(
            "Transaction %d: precision=%.3f, recall=%.3f, hit=%d, recs=%s",
            idx + 1, precision, recall, hit, recommended_top_k,
        )

    # --- Aggregate ---
    result.num_evaluated = num_evaluated
    result.total_recommendations = total_recs

    if num_evaluated == 0:
        result.evaluated = False
        result.notes = (
            "The recommender returned no recommendations for any of the "
            f"{num_test} eligible test transactions. "
            "Check that the model has been trained and that min_confidence / "
            "min_lift thresholds are not too restrictive."
        )
        logger.warning(result.notes)
        return result

    result.evaluated = True
    result.precision_at_k = float(np.mean(precisions))
    result.recall_at_k = float(np.mean(recalls))
    result.hit_rate_at_k = float(np.mean(hits))

    # Coverage: fraction of unique test products that were ever recommended
    if all_test_products:
        result.coverage = len(all_test_products & all_recommended_products) / len(all_test_products)
    else:
        result.coverage = 0.0

    result.avg_support = float(np.mean(all_supports)) if all_supports else 0.0
    result.avg_confidence = float(np.mean(all_confidences)) if all_confidences else 0.0
    result.avg_lift = float(np.mean(all_lifts)) if all_lifts else 0.0

    # Build notes
    unevaluated = num_test - num_evaluated
    notes_parts: List[str] = []
    if unevaluated > 0:
        notes_parts.append(
            f"{unevaluated} of {num_test} transactions produced no recommendations "
            "and were excluded from metric averages."
        )
    if result.coverage < 0.2:
        notes_parts.append(
            "Coverage is below 20% - the model may have limited rule variety."
        )
    result.notes = " ".join(notes_parts)

    logger.info(
        "Evaluation complete | evaluated=%d/%d | P@%d=%.4f | R@%d=%.4f | "
        "HitRate=%.4f | Coverage=%.4f",
        num_evaluated, num_test,
        k, result.precision_at_k,
        k, result.recall_at_k,
        result.hit_rate_at_k,
        result.coverage,
    )

    return result


# ---------------------------------------------------------------------------
# Report formatter
# ---------------------------------------------------------------------------

def format_evaluation_report(result: EvaluationResult) -> str:
    """Format an :class:`EvaluationResult` as a Markdown string.

    Parameters
    ----------
    result:
        The evaluation result returned by :func:`evaluate_recommender`.

    Returns
    -------
    str
        A multi-line Markdown string suitable for printing or saving to a file.
    """
    status_icon = "✅" if result.evaluated else "❌"

    lines = [
        "# Smart Bundle Recommender - Evaluation Report",
        "",
        f"**Status:** {status_icon} {'Evaluated' if result.evaluated else 'Not Evaluated'}",
        "",
        "## Configuration",
        "",
        f"| Parameter | Value |",
        f"|-----------|-------|",
        f"| K (top-K) | {result.k} |",
        f"| Test transactions (>=2 items) | {result.num_test_transactions} |",
        f"| Transactions evaluated | {result.num_evaluated} |",
        f"| Total recommendations generated | {result.total_recommendations} |",
        "",
    ]

    if result.evaluated:
        lines += [
            "## Ranking Metrics",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Precision@{result.k} | {result.precision_at_k:.4f} |",
            f"| Recall@{result.k} | {result.recall_at_k:.4f} |",
            f"| Hit Rate@{result.k} | {result.hit_rate_at_k:.4f} |",
            f"| Coverage | {result.coverage:.4f} ({result.coverage * 100:.1f}%) |",
            "",
            "## Rule Quality Metrics",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Average Support | {result.avg_support:.4f} |",
            f"| Average Confidence | {result.avg_confidence:.4f} |",
            f"| Average Lift | {result.avg_lift:.4f} |",
            "",
        ]
    else:
        lines += [
            "## Metrics",
            "",
            "_Metrics could not be computed - see Notes below._",
            "",
        ]

    if result.notes:
        lines += [
            "## Notes",
            "",
            f"> {result.notes}",
            "",
        ]

    lines += [
        "---",
        "_Generated by `evaluate_model.py` - Smart Bundle Recommendation System_",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Demo / smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import random

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )

    # ------------------------------------------------------------------
    # Minimal stub recommender for demonstration purposes.
    # In production, replace this with the real BundleRecommender instance.
    # ------------------------------------------------------------------

    PRODUCT_CATALOG = [
        "Laptop", "Mouse", "Keyboard", "Monitor", "Headphones",
        "Webcam", "USB Hub", "Desk Lamp", "Notebook", "Pen",
        "Coffee Mug", "Chair", "Desk Mat", "Cable Organiser", "Speaker",
    ]

    class _StubRecommender:
        """Minimal stub that returns random plausible recommendations."""

        def get_recommendations(
            self,
            query_items: List[str],
            k: int = 5,
            min_confidence: float = 0.1,
            min_lift: float = 1.0,
        ) -> pd.DataFrame:
            rng = random.Random(hash(tuple(query_items)))
            candidates = [p for p in PRODUCT_CATALOG if p not in query_items]
            if not candidates:
                return pd.DataFrame()
            chosen = rng.sample(candidates, min(k, len(candidates)))
            data = {
                "antecedents": [frozenset(query_items)] * len(chosen),
                "consequents": [frozenset({c}) for c in chosen],
                "support": [rng.uniform(0.05, 0.4) for _ in chosen],
                "confidence": [rng.uniform(0.2, 0.9) for _ in chosen],
                "lift": [rng.uniform(1.0, 4.0) for _ in chosen],
            }
            return pd.DataFrame(data)

    # ------------------------------------------------------------------
    # Build synthetic test transactions
    # ------------------------------------------------------------------
    random.seed(42)
    test_txns: List[List[str]] = []
    for _ in range(200):
        size = random.randint(2, 7)
        txn = random.sample(PRODUCT_CATALOG, size)
        test_txns.append(txn)

    # Add one degenerate single-item transaction (should be skipped)
    test_txns.append(["Laptop"])

    print(f"Generated {len(test_txns)} test transactions ({len(test_txns) - 1} with >=2 items).\n")

    # ------------------------------------------------------------------
    # Run evaluation
    # ------------------------------------------------------------------
    stub = _StubRecommender()
    eval_result = evaluate_recommender(
        recommender=stub,
        test_transactions=test_txns,
        k=5,
        min_confidence=0.1,
        min_lift=1.0,
    )

    # ------------------------------------------------------------------
    # Print formatted report
    # ------------------------------------------------------------------
    report = format_evaluation_report(eval_result)
    print(report)

    # ------------------------------------------------------------------
    # Also show the raw dataclass for debugging
    # ------------------------------------------------------------------
    print("\n### Raw EvaluationResult ###")
    for attr, val in eval_result.__dataclass_fields__.items():
        print(f"  {attr}: {getattr(eval_result, attr)!r}")

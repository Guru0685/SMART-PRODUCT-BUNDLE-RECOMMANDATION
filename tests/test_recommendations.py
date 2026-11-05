"""
tests/test_recommendations.py
-------------------------------
Unit tests for recommendation_engine.BundleRecommender.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from recommendation_engine import BundleRecommender, RecommendationResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_recommender(rules_df: pd.DataFrame) -> BundleRecommender:
    return BundleRecommender(rules_df)


# ---------------------------------------------------------------------------
# 1. Basic smoke test
# ---------------------------------------------------------------------------

class TestGetRecommendationsReturnsList:
    def test_returns_list(self, sample_rules_df):
        rec = _make_recommender(sample_rules_df)
        result = rec.get_recommendations(
            ["WHITE HANGING HEART T-LIGHT HOLDER"],
            min_confidence=0.0,
            min_lift=1.0,
        )
        assert isinstance(result, list)

    def test_returns_recommendation_result_objects(self, sample_rules_df):
        rec = _make_recommender(sample_rules_df)
        result = rec.get_recommendations(
            ["WHITE HANGING HEART T-LIGHT HOLDER"],
            min_confidence=0.0,
            min_lift=1.0,
        )
        for item in result:
            assert isinstance(item, RecommendationResult)


# ---------------------------------------------------------------------------
# 2. Empty input returns empty list
# ---------------------------------------------------------------------------

class TestNoSelectedProducts:
    def test_empty_input_returns_empty(self, sample_rules_df):
        rec = _make_recommender(sample_rules_df)
        result = rec.get_recommendations([], min_confidence=0.0, min_lift=1.0)
        assert result == []

    def test_none_like_empty_list(self, sample_rules_df):
        rec = _make_recommender(sample_rules_df)
        result = rec.get_recommendations([], min_confidence=0.5, min_lift=2.0)
        assert len(result) == 0


# ---------------------------------------------------------------------------
# 3. Selected products not in recommendations
# ---------------------------------------------------------------------------

class TestExcludesSelectedProducts:
    def test_selected_not_in_consequents(self, sample_rules_df):
        selected = ["WHITE HANGING HEART T-LIGHT HOLDER"]
        rec = _make_recommender(sample_rules_df)
        results = rec.get_recommendations(selected, min_confidence=0.0, min_lift=1.0)
        for r in results:
            recommended_products = set(r.consequents)
            for sel in selected:
                assert sel not in recommended_products, (
                    f"'{sel}' should not appear in recommendations"
                )

    def test_multiple_selected_not_in_consequents(self, sample_rules_df):
        selected = [
            "CREAM CUPID HEARTS COAT HANGER",
            "RED WOOLLY HOTTIE WHITE HEART",
        ]
        rec = _make_recommender(sample_rules_df)
        results = rec.get_recommendations(selected, min_confidence=0.0, min_lift=1.0)
        for r in results:
            for sel in selected:
                assert sel not in r.consequents


# ---------------------------------------------------------------------------
# 4. min_confidence filter
# ---------------------------------------------------------------------------

class TestMinConfidenceFilter:
    def test_confidence_above_threshold(self, sample_rules_df):
        min_conf = 0.55
        rec = _make_recommender(sample_rules_df)
        results = rec.get_recommendations(
            ["WHITE HANGING HEART T-LIGHT HOLDER",
             "CREAM CUPID HEARTS COAT HANGER",
             "HEART OF WICKER SMALL"],
            min_confidence=min_conf,
            min_lift=1.0,
        )
        for r in results:
            assert r.confidence >= min_conf - 1e-9, (
                f"confidence {r.confidence} below threshold {min_conf}"
            )

    def test_high_confidence_threshold_reduces_results(self, sample_rules_df):
        rec = _make_recommender(sample_rules_df)
        results_low = rec.get_recommendations(
            ["ALARM CLOCK BAKELIKE GREEN", "ROUND SNACK BOXES SET OF 4 WOODLAND"],
            min_confidence=0.01,
            min_lift=1.0,
        )
        results_high = rec.get_recommendations(
            ["ALARM CLOCK BAKELIKE GREEN", "ROUND SNACK BOXES SET OF 4 WOODLAND"],
            min_confidence=0.99,
            min_lift=1.0,
        )
        assert len(results_high) <= len(results_low)


# ---------------------------------------------------------------------------
# 5. min_lift filter
# ---------------------------------------------------------------------------

class TestMinLiftFilter:
    def test_lift_above_threshold(self, sample_rules_df):
        min_lift = 3.0
        rec = _make_recommender(sample_rules_df)
        # Use all products as antecedents to maximise chances of hitting rules
        all_antecedents = list(
            set(p for fs in sample_rules_df["antecedents"] for p in fs)
        )
        results = rec.get_recommendations(
            all_antecedents, min_confidence=0.0, min_lift=min_lift
        )
        for r in results:
            assert r.lift >= min_lift - 1e-9, (
                f"lift {r.lift} below threshold {min_lift}"
            )

    def test_very_high_lift_returns_fewer_or_equal(self, sample_rules_df):
        rec = _make_recommender(sample_rules_df)
        all_antecedents = list(
            set(p for fs in sample_rules_df["antecedents"] for p in fs)
        )
        low = rec.get_recommendations(all_antecedents, min_confidence=0.0, min_lift=1.0)
        high = rec.get_recommendations(all_antecedents, min_confidence=0.0, min_lift=5.0)
        assert len(high) <= len(low)


# ---------------------------------------------------------------------------
# 6. search_products – exact match first
# ---------------------------------------------------------------------------

class TestSearchProductsExact:
    def test_exact_match_in_results(self, sample_rules_df):
        rec = _make_recommender(sample_rules_df)
        all_products = [
            "ALARM CLOCK BAKELIKE GREEN",
            "ALARM CLOCK BAKELIKE RED",
            "RED WOOLLY HOTTIE WHITE HEART",
            "WHITE HANGING HEART T-LIGHT HOLDER",
        ]
        results = rec.search_products("ALARM CLOCK BAKELIKE GREEN", all_products)
        assert "ALARM CLOCK BAKELIKE GREEN" in results
        # Exact match should appear first
        assert results[0] == "ALARM CLOCK BAKELIKE GREEN"

    def test_case_insensitive(self, sample_rules_df):
        rec = _make_recommender(sample_rules_df)
        all_products = ["ALARM CLOCK BAKELIKE GREEN", "RED WOOLLY HOTTIE WHITE HEART"]
        results = rec.search_products("alarm clock", all_products)
        assert len(results) >= 1


# ---------------------------------------------------------------------------
# 7. search_products – partial match
# ---------------------------------------------------------------------------

class TestSearchProductsPartial:
    def test_partial_match_found(self, sample_rules_df):
        rec = _make_recommender(sample_rules_df)
        all_products = [
            "HEART OF WICKER SMALL",
            "HEART OF WICKER LARGE",
            "JUMBO BAG RED RETROSPOT",
        ]
        results = rec.search_products("HEART", all_products)
        assert "HEART OF WICKER SMALL" in results
        assert "HEART OF WICKER LARGE" in results
        assert "JUMBO BAG RED RETROSPOT" not in results

    def test_no_match_returns_empty(self, sample_rules_df):
        rec = _make_recommender(sample_rules_df)
        all_products = ["ALARM CLOCK BAKELIKE GREEN", "RED WOOLLY HOTTIE WHITE HEART"]
        results = rec.search_products("NONEXISTENT PRODUCT XYZ", all_products)
        assert results == []


# ---------------------------------------------------------------------------
# 8. RecommendationResult has all required fields
# ---------------------------------------------------------------------------

class TestRecommendationResultFields:
    REQUIRED_FIELDS = {
        "antecedents",
        "consequents",
        "support",
        "confidence",
        "lift",
        "explanation",
        "bundle_name",
    }

    def test_all_fields_present(self, sample_rules_df):
        rec = _make_recommender(sample_rules_df)
        all_antecedents = list(
            set(p for fs in sample_rules_df["antecedents"] for p in fs)
        )
        results = rec.get_recommendations(
            all_antecedents, min_confidence=0.0, min_lift=1.0
        )
        if results:
            result = results[0]
            for field in self.REQUIRED_FIELDS:
                assert hasattr(result, field), f"Missing field: {field}"

    def test_explanation_is_string(self, sample_rules_df):
        rec = _make_recommender(sample_rules_df)
        all_antecedents = list(
            set(p for fs in sample_rules_df["antecedents"] for p in fs)
        )
        results = rec.get_recommendations(
            all_antecedents, min_confidence=0.0, min_lift=1.0
        )
        for r in results:
            assert isinstance(r.explanation, str)
            assert len(r.explanation) > 0

    def test_numeric_fields_are_floats(self, sample_rules_df):
        rec = _make_recommender(sample_rules_df)
        all_antecedents = list(
            set(p for fs in sample_rules_df["antecedents"] for p in fs)
        )
        results = rec.get_recommendations(
            all_antecedents, min_confidence=0.0, min_lift=1.0
        )
        for r in results:
            assert isinstance(r.support, float)
            assert isinstance(r.confidence, float)
            assert isinstance(r.lift, float)

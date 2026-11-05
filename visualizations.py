"""
visualizations.py
-----------------
Plotly-based visualization functions for the Smart Product Bundle
Recommendation System.

All functions return a ``plotly.graph_objects.Figure`` and use the
``"plotly_white"`` template with a consistent margin of
``dict(l=40, r=40, t=60, b=40)``.

No ``fig.show()`` calls are made; the caller is responsible for
rendering or exporting the returned figure.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_TEMPLATE = "plotly_white"
_MARGIN = dict(l=40, r=40, t=60, b=40)
_MAX_LABEL_LEN = 40


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _truncate(text: str, max_len: int = _MAX_LABEL_LEN) -> str:
    """Truncate *text* to *max_len* characters, appending '…' if needed."""
    text = str(text)
    return text if len(text) <= max_len else text[: max_len - 1] + "…"


def _empty_figure(title: str) -> go.Figure:
    """Return a blank figure with a centred 'No data available' annotation."""
    fig = go.Figure()
    fig.update_layout(
        title=title,
        template=_TEMPLATE,
        margin=_MARGIN,
        annotations=[
            dict(
                text="No data available",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=16, color="gray"),
            )
        ],
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig


def _frozenset_label(fs: Any) -> str:
    """Convert a frozenset (or any iterable) to a readable string label."""
    try:
        items = sorted(fs)
    except TypeError:
        items = list(fs)
    return ", ".join(_truncate(str(i)) for i in items)


# ---------------------------------------------------------------------------
# 1. Top Products
# ---------------------------------------------------------------------------


def plot_top_products(
    top_products: list[tuple[str, int]],
    n: int = 20,
) -> go.Figure:
    """Plot a horizontal bar chart of the top-N products by transaction count.

    Parameters
    ----------
    top_products:
        List of ``(product_name, transaction_count)`` tuples, ordered
        descending by count.
    n:
        Number of products to display.  Defaults to 20.

    Returns
    -------
    go.Figure
        Horizontal bar chart with a blue colour gradient.
    """
    title = "Top Selling Products"

    if not top_products:
        return _empty_figure(title)

    subset = top_products[:n]
    labels = [_truncate(p[0]) for p in reversed(subset)]
    counts = [p[1] for p in reversed(subset)]

    # Normalise counts to [0, 1] for colour mapping
    max_count = max(counts) if counts else 1
    norm = [c / max_count for c in counts]

    # Sample a sequential blues palette
    blues = px.colors.sequential.Blues
    bar_colors = [
        blues[max(1, int(v * (len(blues) - 1)))] for v in norm
    ]

    fig = go.Figure(
        go.Bar(
            x=counts,
            y=labels,
            orientation="h",
            marker=dict(color=bar_colors),
            hovertemplate="<b>%{y}</b><br>Transactions: %{x:,}<extra></extra>",
        )
    )
    fig.update_layout(
        title=title,
        template=_TEMPLATE,
        margin=_MARGIN,
        xaxis=dict(title="Transaction Count"),
        yaxis=dict(title="Product"),
    )
    return fig


# ---------------------------------------------------------------------------
# 2. Support vs Confidence
# ---------------------------------------------------------------------------


def plot_support_vs_confidence(rules_df: pd.DataFrame) -> go.Figure:
    """Scatter plot of association rules: support vs confidence, coloured by lift.

    Parameters
    ----------
    rules_df:
        DataFrame produced by ``mlxtend.frequent_patterns.association_rules``
        (or equivalent), containing at minimum the columns
        ``antecedents``, ``consequents``, ``support``, ``confidence``,
        and ``lift``.

    Returns
    -------
    go.Figure
        Scatter plot with Viridis colour scale.  Marker size is
        proportional to lift, capped at 20 px.
    """
    title = "Support vs Confidence (colored by Lift)"

    if rules_df is None or rules_df.empty:
        return _empty_figure(title)

    required = {"antecedents", "consequents", "support", "confidence", "lift"}
    if not required.issubset(rules_df.columns):
        return _empty_figure(title)

    df = rules_df.copy()
    df["_ant_label"] = df["antecedents"].apply(_frozenset_label)
    df["_con_label"] = df["consequents"].apply(_frozenset_label)

    # Cap marker size at 20 px
    max_lift = df["lift"].max() if df["lift"].max() > 0 else 1
    sizes = (df["lift"] / max_lift * 20).clip(upper=20).tolist()

    fig = go.Figure(
        go.Scatter(
            x=df["support"],
            y=df["confidence"],
            mode="markers",
            marker=dict(
                size=sizes,
                color=df["lift"],
                colorscale="Viridis",
                showscale=True,
                colorbar=dict(title="Lift"),
                line=dict(width=0.5, color="white"),
            ),
            customdata=list(
                zip(
                    df["_ant_label"],
                    df["_con_label"],
                    df["support"],
                    df["confidence"],
                    df["lift"],
                )
            ),
            hovertemplate=(
                "<b>%{customdata[0]}</b> → <b>%{customdata[1]}</b><br>"
                "Support: %{customdata[2]:.4f}<br>"
                "Confidence: %{customdata[3]:.4f}<br>"
                "Lift: %{customdata[4]:.4f}"
                "<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        title=title,
        template=_TEMPLATE,
        margin=_MARGIN,
        xaxis=dict(title="Support"),
        yaxis=dict(title="Confidence"),
    )
    return fig


# ---------------------------------------------------------------------------
# 3. Top Rules by Lift
# ---------------------------------------------------------------------------


def plot_top_rules_by_lift(
    rules_df: pd.DataFrame,
    n: int = 20,
) -> go.Figure:
    """Horizontal bar chart of the top-N association rules ranked by lift.

    Parameters
    ----------
    rules_df:
        Association rules DataFrame containing ``antecedents``,
        ``consequents``, ``lift``, and ``confidence``.
    n:
        Maximum number of rules to display.  Defaults to 20.

    Returns
    -------
    go.Figure
        Horizontal bar chart coloured by confidence (RdYlGn scale).
    """
    title = "Top Association Rules by Lift"

    if rules_df is None or rules_df.empty:
        return _empty_figure(title)

    required = {"antecedents", "consequents", "lift", "confidence"}
    if not required.issubset(rules_df.columns):
        return _empty_figure(title)

    df = (
        rules_df.nlargest(n, "lift")
        .iloc[::-1]  # ascending for horizontal bar (bottom = highest)
        .copy()
    )
    df["_label"] = (
        df["antecedents"].apply(_frozenset_label)
        + " → "
        + df["consequents"].apply(_frozenset_label)
    )

    fig = go.Figure(
        go.Bar(
            x=df["lift"],
            y=df["_label"],
            orientation="h",
            marker=dict(
                color=df["confidence"],
                colorscale="RdYlGn",
                showscale=True,
                colorbar=dict(title="Confidence"),
                cmin=0,
                cmax=1,
            ),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Lift: %{x:.4f}<br>"
                "Confidence: %{marker.color:.4f}"
                "<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        title=title,
        template=_TEMPLATE,
        margin=_MARGIN,
        xaxis=dict(title="Lift"),
        yaxis=dict(title="Rule (Antecedents → Consequents)"),
    )
    return fig


# ---------------------------------------------------------------------------
# 4. Frequent Pairs
# ---------------------------------------------------------------------------


def plot_frequent_pairs(
    rules_df: pd.DataFrame,
    n: int = 20,
) -> go.Figure:
    """Bar chart of the most frequent 2-item product pairs by support.

    Only rules where both the antecedent and consequent contain exactly
    one item are considered (i.e., genuine 1-to-1 pairs).

    Parameters
    ----------
    rules_df:
        Association rules DataFrame containing ``antecedents``,
        ``consequents``, ``support``, and ``lift``.
    n:
        Maximum number of pairs to display.  Defaults to 20.

    Returns
    -------
    go.Figure
        Horizontal bar chart coloured by lift.
    """
    title = "Most Frequent Product Pairs"

    if rules_df is None or rules_df.empty:
        return _empty_figure(title)

    required = {"antecedents", "consequents", "support", "lift"}
    if not required.issubset(rules_df.columns):
        return _empty_figure(title)

    # Filter to singleton antecedent and consequent
    mask = (
        rules_df["antecedents"].apply(len) == 1
    ) & (
        rules_df["consequents"].apply(len) == 1
    )
    pairs_df = rules_df[mask].copy()

    if pairs_df.empty:
        return _empty_figure(title)

    df = pairs_df.nlargest(n, "support").iloc[::-1].copy()
    df["_label"] = (
        df["antecedents"].apply(_frozenset_label)
        + " → "
        + df["consequents"].apply(_frozenset_label)
    )

    fig = go.Figure(
        go.Bar(
            x=df["support"],
            y=df["_label"],
            orientation="h",
            marker=dict(
                color=df["lift"],
                colorscale="Viridis",
                showscale=True,
                colorbar=dict(title="Lift"),
            ),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Support: %{x:.4f}<br>"
                "Lift: %{marker.color:.4f}"
                "<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        title=title,
        template=_TEMPLATE,
        margin=_MARGIN,
        xaxis=dict(title="Support"),
        yaxis=dict(title="Product Pair"),
    )
    return fig


# ---------------------------------------------------------------------------
# 5. Lift Distribution
# ---------------------------------------------------------------------------


def plot_lift_distribution(rules_df: pd.DataFrame) -> go.Figure:
    """Histogram of lift values across all association rules.

    A vertical reference line is drawn at lift = 1.0 (the no-association
    baseline).

    Parameters
    ----------
    rules_df:
        Association rules DataFrame containing a ``lift`` column.

    Returns
    -------
    go.Figure
        Histogram of lift values coloured teal.
    """
    title = "Distribution of Lift Values"

    if rules_df is None or rules_df.empty or "lift" not in rules_df.columns:
        return _empty_figure(title)

    lifts = rules_df["lift"].dropna()
    if lifts.empty:
        return _empty_figure(title)

    fig = go.Figure(
        go.Histogram(
            x=lifts,
            marker=dict(color="teal", line=dict(color="white", width=0.5)),
            hovertemplate="Lift: %{x:.2f}<br>Count: %{y}<extra></extra>",
        )
    )

    # Baseline reference line at lift = 1.0
    fig.add_vline(
        x=1.0,
        line_dash="dash",
        line_color="crimson",
        annotation_text="Baseline (lift=1)",
        annotation_position="top right",
        annotation=dict(font=dict(color="crimson")),
    )

    fig.update_layout(
        title=title,
        template=_TEMPLATE,
        margin=_MARGIN,
        xaxis=dict(title="Lift"),
        yaxis=dict(title="Count"),
    )
    return fig


# ---------------------------------------------------------------------------
# 6. Confidence Distribution
# ---------------------------------------------------------------------------


def plot_confidence_distribution(rules_df: pd.DataFrame) -> go.Figure:
    """Histogram of confidence values across all association rules.

    Parameters
    ----------
    rules_df:
        Association rules DataFrame containing a ``confidence`` column.

    Returns
    -------
    go.Figure
        Histogram of confidence values coloured orange.
    """
    title = "Distribution of Confidence Values"

    if (
        rules_df is None
        or rules_df.empty
        or "confidence" not in rules_df.columns
    ):
        return _empty_figure(title)

    confidences = rules_df["confidence"].dropna()
    if confidences.empty:
        return _empty_figure(title)

    fig = go.Figure(
        go.Histogram(
            x=confidences,
            marker=dict(color="darkorange", line=dict(color="white", width=0.5)),
            hovertemplate="Confidence: %{x:.2f}<br>Count: %{y}<extra></extra>",
        )
    )
    fig.update_layout(
        title=title,
        template=_TEMPLATE,
        margin=_MARGIN,
        xaxis=dict(title="Confidence", range=[0, 1]),
        yaxis=dict(title="Count"),
    )
    return fig


# ---------------------------------------------------------------------------
# 7. Recommendation Evaluation Stats
# ---------------------------------------------------------------------------


def plot_recommendation_stats(eval_result: Any) -> go.Figure:
    """Bar chart of recommendation system evaluation metrics.

    Parameters
    ----------
    eval_result:
        An object or mapping containing the keys (or attributes)
        ``precision``, ``recall``, ``hit_rate``, and ``coverage``
        (all expected to be in the range [0, 1]).  Both dict-like
        and attribute-style access are supported.

    Returns
    -------
    go.Figure
        Bar chart with distinct colours per metric, y-axis range [0, 1].
    """
    title = "Recommendation System Evaluation Metrics"

    def _get(obj: Any, key: str) -> float | None:
        """Retrieve *key* from dict-like or object attribute."""
        try:
            return float(obj[key])
        except (KeyError, TypeError):
            pass
        try:
            return float(getattr(obj, key))
        except AttributeError:
            pass
        return None

    metric_keys = ["precision", "recall", "hit_rate", "coverage"]
    metric_labels = ["Precision@K", "Recall@K", "Hit Rate@K", "Coverage"]
    colors = ["steelblue", "mediumseagreen", "coral", "mediumpurple"]

    values: list[float] = []
    labels: list[str] = []
    bar_colors: list[str] = []

    for key, label, color in zip(metric_keys, metric_labels, colors):
        val = _get(eval_result, key)
        if val is not None:
            values.append(val)
            labels.append(label)
            bar_colors.append(color)

    if not values:
        return _empty_figure(title)

    fig = go.Figure(
        go.Bar(
            x=labels,
            y=values,
            marker=dict(color=bar_colors),
            text=[f"{v:.3f}" for v in values],
            textposition="outside",
            hovertemplate="<b>%{x}</b>: %{y:.4f}<extra></extra>",
        )
    )
    fig.update_layout(
        title=title,
        template=_TEMPLATE,
        margin=_MARGIN,
        yaxis=dict(title="Score", range=[0, 1.1]),
        xaxis=dict(title="Metric"),
    )
    return fig


# ---------------------------------------------------------------------------
# 8. Itemset Size Distribution
# ---------------------------------------------------------------------------


def plot_itemset_sizes(frequent_itemsets: pd.DataFrame) -> go.Figure:
    """Bar chart of frequent itemset counts broken down by itemset size.

    Parameters
    ----------
    frequent_itemsets:
        DataFrame produced by ``mlxtend.frequent_patterns.apriori``
        (or equivalent) containing an ``itemsets`` column of frozensets.

    Returns
    -------
    go.Figure
        Bar chart where each bar represents an itemset size (1-item,
        2-item, etc.) and the height reflects how many such itemsets exist.
    """
    title = "Frequent Itemset Size Distribution"

    if (
        frequent_itemsets is None
        or frequent_itemsets.empty
        or "itemsets" not in frequent_itemsets.columns
    ):
        return _empty_figure(title)

    sizes = frequent_itemsets["itemsets"].apply(len)
    if sizes.empty:
        return _empty_figure(title)

    size_counts = sizes.value_counts().sort_index()
    x_labels = [f"{s}-item" for s in size_counts.index]

    fig = go.Figure(
        go.Bar(
            x=x_labels,
            y=size_counts.values,
            marker=dict(
                color=size_counts.values,
                colorscale="Blues",
                showscale=False,
                line=dict(color="white", width=0.5),
            ),
            text=size_counts.values,
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Count: %{y:,}<extra></extra>",
        )
    )
    fig.update_layout(
        title=title,
        template=_TEMPLATE,
        margin=_MARGIN,
        xaxis=dict(title="Itemset Size"),
        yaxis=dict(title="Number of Frequent Itemsets"),
    )
    return fig

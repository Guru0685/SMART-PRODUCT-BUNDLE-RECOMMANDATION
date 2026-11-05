"""
Smart Product Bundle Recommendation System
Streamlit Application Entry Point
"""

import streamlit as st
import pandas as pd
import traceback

# ── Page configuration (must be first Streamlit call) ────────────────────────
st.set_page_config(
    page_title="Bundle Recommender",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
        /* Global font stack */
        html, body, [class*="css"] {
            font-family: 'Inter', 'Segoe UI', 'Roboto', sans-serif;
        }

        /* Metric card styling */
        div[data-testid="metric-container"] {
            background: linear-gradient(135deg, #e8f4fd 0%, #ffffff 100%);
            border: 1px solid #cce3f5;
            border-radius: 12px;
            padding: 16px 20px;
            box-shadow: 0 2px 8px rgba(0, 120, 200, 0.08);
            transition: box-shadow 0.2s ease;
        }
        div[data-testid="metric-container"]:hover {
            box-shadow: 0 4px 16px rgba(0, 120, 200, 0.15);
        }

        /* Bundle recommendation card */
        .bundle-card {
            background: #ffffff;
            border: 1px solid #e0e8f0;
            border-radius: 12px;
            padding: 18px 22px;
            margin-bottom: 14px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
            transition: box-shadow 0.2s ease;
        }
        .bundle-card:hover {
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.11);
        }

        /* Lift badge colours */
        .lift-high {
            color: #1a7a4a;
            background-color: #d4f5e4;
            border-radius: 6px;
            padding: 2px 10px;
            font-weight: 700;
        }
        .lift-med {
            color: #7a5f00;
            background-color: #fff4c2;
            border-radius: 6px;
            padding: 2px 10px;
            font-weight: 700;
        }

        /* Section divider */
        .section-divider {
            border: none;
            border-top: 2px solid #e8f0f7;
            margin: 24px 0;
        }

        /* Expander styling */
        details summary {
            font-weight: 600;
            color: #1a5276;
        }

        /* Sidebar branding */
        .sidebar-brand {
            text-align: center;
            padding: 10px 0 20px 0;
        }
        .sidebar-brand h2 {
            color: #1a5276;
            font-size: 1.3rem;
            margin-bottom: 4px;
        }
        .sidebar-brand p {
            color: #555;
            font-size: 0.82rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Project imports ───────────────────────────────────────────────────────────
try:
    from data_preprocessing import load_or_preprocess, DatasetInfo
    from train_model import train_or_load
    from recommendation_engine import BundleRecommender
    from evaluate_model import evaluate_recommender, EvaluationResult, format_evaluation_report
    import visualizations as viz
except ImportError as e:
    st.error(
        f"**Import error:** {e}\n\n"
        "Make sure all project modules (`data_preprocessing.py`, `train_model.py`, "
        "`recommendation_engine.py`, `evaluate_model.py`, `visualizations.py`) "
        "are present in the same directory as `app.py`."
    )
    st.stop()


# ── Cached resource loader ────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_all():
    """Load (or preprocess + train) everything once and cache in-process."""
    info = load_or_preprocess()
    itemsets, rules, metadata = train_or_load(transactions=None, force=False)
    recommender = BundleRecommender(rules)
    return info, itemsets, rules, metadata, recommender


# ── Bootstrap: load model on first run ───────────────────────────────────────
with st.spinner("⏳ Loading data and training model — this may take a moment on first run…"):
    try:
        info, itemsets, rules, metadata, recommender = load_all()
        load_error = None
    except Exception as exc:
        load_error = exc

if load_error is not None:
    st.error(
        f"**Failed to load the model.**\n\n"
        f"```\n{traceback.format_exc()}\n```\n\n"
        "Check that your dataset is in place and that all modules are configured correctly."
    )
    st.stop()

# Derive product list once
try:
    all_products: list = sorted(recommender.all_products)
except Exception:
    all_products = []


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
            <h2>🛒 Bundle Recommender</h2>
            <p>v1.0 · Apriori-based association rules</p>
            <p style="color:#888; font-size:0.75rem;">
                Discover which products are bought together and generate smart bundle suggestions.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    page = st.radio(
        "Navigate",
        [
            "📊 Dashboard",
            "🛒 Product Bundle Recommender",
            "📈 Analytics",
            "🧪 Model Evaluation",
            "📁 Dataset Info",
        ],
        label_visibility="collapsed",
    )

    st.divider()

    # ── Recommendation controls (shown for all pages but used on page 2) ──
    if page == "🛒 Product Bundle Recommender":
        st.subheader("⚙️ Recommendation Settings")
        min_confidence = st.slider(
            "Min Confidence", min_value=0.0, max_value=1.0, value=0.1, step=0.01,
            help="Minimum probability that the consequent is bought when the antecedent is bought."
        )
        min_lift = st.slider(
            "Min Lift", min_value=1.0, max_value=5.0, value=1.0, step=0.1,
            help="Minimum lift; values > 1 indicate a genuine positive association."
        )
        top_n = st.slider(
            "Top N Results", min_value=3, max_value=20, value=10, step=1,
        )
    else:
        min_confidence = 0.1
        min_lift = 1.0
        top_n = 10

    st.divider()
    st.caption("Built with ❤️ using Streamlit + mlxtend")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 1: DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
if page == "📊 Dashboard":
    st.title("📊 Dashboard — Overview")
    st.markdown("A high-level summary of the dataset and the trained association-rule model.")

    # ── Top metrics ──────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Transactions", f"{info.total_transactions:,}")
    with col2:
        st.metric("Unique Products", f"{info.unique_products:,}")
    with col3:
        st.metric("Frequent Itemsets", f"{len(itemsets):,}")
    with col4:
        st.metric("Association Rules", f"{len(rules):,}")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ── Apriori explainer ────────────────────────────────────────────────────
    with st.expander("ℹ️ How does the Apriori algorithm work?", expanded=False):
        st.markdown(
            """
            **Apriori** is a classic algorithm for mining frequent itemsets and generating
            association rules from transactional data.

            | Metric | Meaning |
            |--------|---------|
            | **Support** | Fraction of transactions containing the itemset |
            | **Confidence** | P(consequent \| antecedent) |
            | **Lift** | Confidence ÷ P(consequent) — values > 1 indicate a real association |

            **How it works:**
            1. Enumerate all itemsets that meet the minimum *support* threshold.
            2. Generate candidate rules from those frequent itemsets.
            3. Prune rules that fall below the minimum *confidence* and *lift* thresholds.

            The result is a compact set of rules like  
            `{Bread, Butter} → {Jam}  (support=0.12, confidence=0.74, lift=2.3)`
            """
        )

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ── Charts ───────────────────────────────────────────────────────────────
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("🏆 Top Selling Products")
        try:
            fig = viz.plot_top_products(info)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Could not render Top Products chart: {e}")

    with chart_col2:
        st.subheader("📦 Frequent Itemset Size Distribution")
        try:
            fig = viz.plot_itemset_sizes(itemsets)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Could not render Itemset Sizes chart: {e}")

    st.subheader("⚡ Lift Distribution")
    try:
        fig = viz.plot_lift_distribution(rules)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"Could not render Lift Distribution chart: {e}")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ── Model metadata ────────────────────────────────────────────────────────
    st.subheader("🗂️ Model Metadata")
    try:
        meta_df = pd.DataFrame(
            [
                {"Parameter": "Min Support", "Value": metadata.get("min_support", "N/A")},
                {"Parameter": "Min Lift", "Value": metadata.get("min_lift", "N/A")},
                {"Parameter": "Training Date", "Value": metadata.get("training_date", "N/A")},
                {"Parameter": "Number of Rules", "Value": len(rules)},
            ]
        )
        st.dataframe(meta_df, use_container_width=True, hide_index=True)
    except Exception as e:
        st.warning(f"Could not render metadata table: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 2: PRODUCT BUNDLE RECOMMENDER
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🛒 Product Bundle Recommender":
    st.title("🛒 Product Bundle Recommender")
    st.markdown(
        "Select one or more products to discover complementary bundles based on purchase patterns."
    )

    selected_products = st.multiselect(
        "🔍 Search & select products",
        options=all_products,
        placeholder="Type to search products…",
        help="Choose the products a customer has already selected or is browsing.",
    )

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    if not selected_products:
        st.info(
            "👆 **Select at least one product above** to see bundle recommendations.\n\n"
            "You can search by typing the product name in the multiselect box. "
            "Use the sidebar controls to adjust confidence, lift, and the number of results."
        )
    else:
        # ── Fetch recommendations ─────────────────────────────────────────────
        try:
            recommendations = recommender.get_recommendations(
                selected_products,
                min_confidence=min_confidence,
                min_lift=min_lift,
                top_n=top_n,
            )
        except Exception as exc:
            st.error(f"Recommendation engine error: {exc}")
            recommendations = []

        st.subheader(
            f"Showing {len(recommendations)} recommendation(s) for: "
            f"**{', '.join(selected_products)}**"
        )

        if not recommendations:
            st.warning(
                "⚠️ **No bundles found** for the current selection and filter settings.\n\n"
                "**Suggestions:**\n"
                "- Lower the *Min Confidence* slider in the sidebar.\n"
                "- Lower the *Min Lift* slider.\n"
                "- Try selecting fewer or different products.\n"
                "- If the model was trained with a high min_support, niche products may have no rules."
            )
        else:
            for idx, rec in enumerate(recommendations, start=1):
                # Each recommendation is expected to be a dict or object with:
                # bundle_name, support, confidence, lift, explanation
                try:
                    if isinstance(rec, dict):
                        bundle_name   = rec.get("bundle_name", rec.get("name", f"Bundle {idx}"))
                        support       = rec.get("support", 0.0)
                        confidence    = rec.get("confidence", 0.0)
                        lift          = rec.get("lift", 0.0)
                        explanation   = rec.get("explanation", "")
                    else:
                        bundle_name   = getattr(rec, "bundle_name", getattr(rec, "name", f"Bundle {idx}"))
                        support       = getattr(rec, "support", 0.0)
                        confidence    = getattr(rec, "confidence", 0.0)
                        lift          = getattr(rec, "lift", 0.0)
                        explanation   = getattr(rec, "explanation", "")

                    lift_class   = "lift-high" if lift >= 2.0 else "lift-med"
                    support_pct  = f"{support * 100:.2f}%"
                    confidence_pct = f"{confidence * 100:.2f}%"

                    with st.container():
                        st.markdown(
                            f'<div class="bundle-card">'
                            f'<p style="font-size:1.05rem; font-weight:700; margin-bottom:6px;">'
                            f'#{idx} &nbsp; {bundle_name}</p>',
                            unsafe_allow_html=True,
                        )

                        m1, m2, m3 = st.columns(3)
                        with m1:
                            st.metric("Support", support_pct, help="Fraction of all transactions containing this bundle.")
                        with m2:
                            st.metric("Confidence", confidence_pct, help="P(bundle | selected products).")
                        with m3:
                            st.metric(
                                "Lift",
                                f"{lift:.3f}",
                                help="Lift > 1 means a genuine positive association.",
                            )

                        if explanation:
                            st.markdown(f"*{explanation}*")

                        st.markdown(
                            f'<span class="{lift_class}">Lift: {lift:.3f}</span>',
                            unsafe_allow_html=True,
                        )
                        st.markdown("</div>", unsafe_allow_html=True)

                except Exception as card_exc:
                    st.warning(f"Could not render recommendation #{idx}: {card_exc}")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 3: ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📈 Analytics":
    st.title("📈 Analytics — Association Rules Deep Dive")
    st.markdown("Visual exploration of the mined association rules and frequent itemsets.")

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("🔵 Support vs Confidence")
        try:
            fig = viz.plot_support_vs_confidence(rules)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Could not render Support vs Confidence chart: {e}")

    with col_b:
        st.subheader("🏅 Top Rules by Lift")
        try:
            fig = viz.plot_top_rules_by_lift(rules)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Could not render Top Rules by Lift chart: {e}")

    col_c, col_d = st.columns(2)

    with col_c:
        st.subheader("🔗 Most Frequent Product Pairs")
        try:
            fig = viz.plot_frequent_pairs(rules)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Could not render Frequent Pairs chart: {e}")

    with col_d:
        st.subheader("📊 Confidence Distribution")
        try:
            fig = viz.plot_confidence_distribution(rules)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Could not render Confidence Distribution chart: {e}")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ── Full rules table with optional column filter ──────────────────────────
    st.subheader("📋 Full Association Rules Table")
    try:
        rules_display = rules.copy()
        # Convert frozensets to readable strings if needed
        for col in ["antecedents", "consequents"]:
            if col in rules_display.columns:
                rules_display[col] = rules_display[col].apply(
                    lambda x: ", ".join(sorted(x)) if hasattr(x, "__iter__") and not isinstance(x, str) else x
                )

        with st.expander("🔎 Filter & view all rules", expanded=False):
            float_cols = rules_display.select_dtypes(include="float").columns.tolist()
            filter_col = st.selectbox("Filter by column", options=float_cols, index=0 if float_cols else 0)
            if filter_col:
                col_min = float(rules_display[filter_col].min())
                col_max = float(rules_display[filter_col].max())
                filter_val = st.slider(
                    f"Min {filter_col}",
                    min_value=col_min,
                    max_value=col_max,
                    value=col_min,
                    step=(col_max - col_min) / 100 if col_max != col_min else 0.01,
                )
                rules_display = rules_display[rules_display[filter_col] >= filter_val]

            st.dataframe(
                rules_display.sort_values("lift", ascending=False).reset_index(drop=True),
                use_container_width=True,
                height=400,
            )
            st.caption(f"Showing {len(rules_display):,} rules.")
    except Exception as e:
        st.warning(f"Could not render rules table: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 4: MODEL EVALUATION
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🧪 Model Evaluation":
    st.title("🧪 Model Evaluation")

    st.markdown(
        """
        ### Methodology

        The evaluation uses an **80 / 20 temporal split**: the model is trained on the earlier
        80% of transactions and tested on the most-recent 20%.  
        For each test transaction the first *k* items are used as the "query" and the remaining
        items become the ground-truth targets.  Three metrics are computed at a chosen **k**:

        | Metric | Definition |
        |--------|-----------|
        | **Precision\@K** | Among the top-K recommended items, what fraction are actually relevant? |
        | **Recall\@K** | Of all relevant items, what fraction appear in the top-K recommendations? |
        | **Hit Rate\@K** | Fraction of test transactions where at least one recommendation is correct. |

        These are averaged across all test transactions to give overall model quality scores.
        """
    )

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    if "eval_result" not in st.session_state:
        st.session_state["eval_result"] = None

    run_btn = st.button("▶️ Run Evaluation", type="primary", use_container_width=False)

    if run_btn:
        with st.spinner("Running evaluation on the test split…"):
            try:
                eval_result: EvaluationResult = evaluate_recommender(recommender, info)
                st.session_state["eval_result"] = eval_result
                st.success("Evaluation complete!")
            except Exception as exc:
                st.error(f"Evaluation failed: {exc}\n\n```\n{traceback.format_exc()}\n```")

    eval_result = st.session_state.get("eval_result")

    if eval_result is not None:
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        st.subheader("📐 Evaluation Metrics")

        try:
            # Support both dict-like and attribute-style EvaluationResult
            def _get(obj, key, default=0.0):
                if isinstance(obj, dict):
                    return obj.get(key, default)
                return getattr(obj, key, default)

            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("Precision@K", f"{_get(eval_result, 'precision_at_k'):.4f}")
            with m2:
                st.metric("Recall@K", f"{_get(eval_result, 'recall_at_k'):.4f}")
            with m3:
                st.metric("Hit Rate@K", f"{_get(eval_result, 'hit_rate_at_k'):.4f}")
            with m4:
                st.metric("K", str(_get(eval_result, "k", "N/A")))
        except Exception as e:
            st.warning(f"Could not render evaluation metrics: {e}")

        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

        st.subheader("📊 Recommendation Statistics")
        try:
            fig = viz.plot_recommendation_stats(eval_result)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Could not render Recommendation Stats chart: {e}")

        with st.expander("📄 Full Evaluation Report", expanded=False):
            try:
                report_text = format_evaluation_report(eval_result)
                st.text(report_text)
            except Exception as e:
                st.warning(f"Could not render evaluation report: {e}")
    else:
        st.info("Click **▶️ Run Evaluation** above to compute metrics on the hold-out test set.")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 5: DATASET INFO
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📁 Dataset Info":
    st.title("📁 Dataset Info")
    st.markdown("Summary statistics about the pre-processed dataset used to train the model.")

    # ── Dataset metrics ───────────────────────────────────────────────────────
    st.subheader("📏 Dataset Dimensions")
    try:
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Total Transactions", f"{info.total_transactions:,}")
        with m2:
            st.metric("Unique Products", f"{info.unique_products:,}")
        with m3:
            train_size = getattr(info, "train_size", "N/A")
            st.metric("Train Size", f"{train_size:,}" if isinstance(train_size, int) else str(train_size))
        with m4:
            test_size = getattr(info, "test_size", "N/A")
            st.metric("Test Size", f"{test_size:,}" if isinstance(test_size, int) else str(test_size))

        d1, d2 = st.columns(2)
        with d1:
            date_start = getattr(info, "date_range_start", None)
            st.metric("Date Range Start", str(date_start) if date_start else "N/A")
        with d2:
            date_end = getattr(info, "date_range_end", None)
            st.metric("Date Range End", str(date_end) if date_end else "N/A")
    except Exception as e:
        st.warning(f"Could not render dataset metrics: {e}")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ── Top products table ────────────────────────────────────────────────────
    st.subheader("🏆 Top Products by Frequency")
    try:
        top_products = getattr(info, "top_products", None)
        if top_products is not None:
            if isinstance(top_products, dict):
                top_df = pd.DataFrame(
                    list(top_products.items()), columns=["Product", "Frequency"]
                ).sort_values("Frequency", ascending=False).reset_index(drop=True)
            elif isinstance(top_products, pd.DataFrame):
                top_df = top_products
            else:
                top_df = pd.DataFrame(top_products)

            col_t, col_c = st.columns([2, 3])
            with col_t:
                st.dataframe(top_df, use_container_width=True, hide_index=True)
            with col_c:
                try:
                    fig = viz.plot_top_products(info)
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.warning(f"Could not render Top Products chart: {e}")
        else:
            st.info("No top_products data available in DatasetInfo.")
    except Exception as e:
        st.warning(f"Could not render top products: {e}")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ── Cleaned CSV sample ────────────────────────────────────────────────────
    st.subheader("🗒️ Cleaned Dataset Sample (first 100 rows)")
    try:
        cleaned_csv_path = getattr(info, "cleaned_csv_path", None)
        if cleaned_csv_path:
            sample_df = pd.read_csv(cleaned_csv_path, nrows=100)
            st.dataframe(sample_df, use_container_width=True, height=350)
            st.caption(f"Source: `{cleaned_csv_path}`")
        else:
            st.info(
                "No `cleaned_csv_path` attribute found on `DatasetInfo`. "
                "Set `info.cleaned_csv_path` to a valid CSV path to enable this preview."
            )
    except Exception as e:
        st.warning(f"Could not load CSV sample: {e}")

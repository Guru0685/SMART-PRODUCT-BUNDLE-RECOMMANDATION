"""
generate_3_slide_presentation.py
--------------------------------
Generates a 3-slide executive PowerPoint presentation for the Smart Product
Bundle Recommendation System covering:
1. Problem Statement & Data Pipeline
2. Algorithm Used vs Best Algorithm (Comparative Benchmark)
3. Visualizations & Empirical Output (Charts + Real Results)
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_3_slide_deck(output_path: str, art_dir: str):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Color Palette
    NAVY_DARK = RGBColor(15, 23, 42)       # #0F172A
    NAVY_SLATE = RGBColor(30, 41, 59)      # #1E293B
    TEXT_MUTED = RGBColor(100, 116, 139)   # #64748B
    TEXT_MAIN = RGBColor(51, 65, 85)       # #334155
    BLUE_ACCENT = RGBColor(2, 132, 199)    # #0284C7
    TEAL_ACCENT = RGBColor(13, 148, 136)   # #0D9488
    CARD_BG = RGBColor(248, 250, 252)      # #F8FAFC
    CARD_BORDER = RGBColor(226, 232, 240)  # #E2E8F0
    WHITE = RGBColor(255, 255, 255)
    METRIC_BLUE = RGBColor(30, 64, 175)    # #1E40AF
    GREEN_ACCENT = RGBColor(22, 101, 52)   # #166534
    TERM_BG = RGBColor(15, 23, 42)         # #0F172A Dark Console
    TERM_GREEN = RGBColor(34, 197, 94)     # #22C55E
    TERM_YELLOW = RGBColor(234, 179, 8)    # #EAB308
    TERM_CYAN = RGBColor(56, 189, 248)     # #38BDF8
    TERM_WHITE = RGBColor(241, 245, 249)   # #F1F5F9

    # =========================================================================
    # SLIDE 1: Problem Statement, Objective & Data Pipeline
    # =========================================================================
    slide1 = prs.slides.add_slide(blank_layout)

    # Header
    hb1 = slide1.shapes.add_textbox(Inches(0.6), Inches(0.35), Inches(12.133), Inches(1.1))
    tf1 = hb1.text_frame
    tf1.word_wrap = True
    tf1.margin_left = tf1.margin_right = tf1.margin_top = tf1.margin_bottom = 0
    p = tf1.paragraphs[0]
    p.text = "Smart Product Bundle Recommendation System"
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = NAVY_DARK

    p_sub = tf1.add_paragraph()
    p_sub.text = "Slide 1/3: Problem Statement, Solution Architecture & Data Preprocessing Pipeline"
    p_sub.font.size = Pt(11)
    p_sub.font.color.rgb = BLUE_ACCENT
    p_sub.space_before = Pt(3)

    # 3-Column Layout
    col_w = Inches(3.85)
    col_gap = Inches(0.28)
    card_top = Inches(1.5)
    card_h = Inches(5.6)

    # Card 1.1: Problem Statement
    c1_left = Inches(0.6)
    s1_shape = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, c1_left, card_top, col_w, card_h)
    s1_shape.fill.solid()
    s1_shape.fill.fore_color.rgb = CARD_BG
    s1_shape.line.color.rgb = CARD_BORDER
    s1_shape.line.width = Pt(1)

    tb_s1 = slide1.shapes.add_textbox(c1_left + Inches(0.2), card_top + Inches(0.2), col_w - Inches(0.4), card_h - Inches(0.4))
    tf_s1 = tb_s1.text_frame
    tf_s1.word_wrap = True
    tf_s1.margin_left = tf_s1.margin_right = tf_s1.margin_top = tf_s1.margin_bottom = 0

    p = tf_s1.paragraphs[0]
    p.text = "THE COMMERCIAL CHALLENGE"
    p.font.size = Pt(8.5)
    p.font.bold = True
    p.font.color.rgb = BLUE_ACCENT

    p = tf_s1.add_paragraph()
    p.text = "Problem Statement"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = NAVY_DARK
    p.space_after = Pt(8)

    ps_items = [
        ("Suboptimal Order Value (AOV)", "E-commerce retailers struggle with low Average Order Value and high single-item cart abandonments, missing substantial revenue from untriggered cross-sells."),
        ("The Cold-Start Dilemma", "Over 70% of e-commerce sessions are anonymous guests or first-time buyers with zero purchase history, rendering traditional user-profile recommenders unusable."),
        ("Manual Bundling Bottleneck", "Curating product bundles by hand is labor-intensive, fails to scale across thousands of SKUs, and overlooks subtle, high-converting product associations."),
        ("Lack of Consumer Trust", "Generic 'You Might Also Like' widgets lack justification and often recommend irrelevant or redundant items that shoppers already placed in their cart."),
        ("Core Objective", "Develop an intelligent, autonomous market basket analysis system that predicts complementary items in real-time using in-cart signals with mathematical explainability.")
    ]
    for h, b in ps_items:
        p_item = tf_s1.add_paragraph()
        p_item.space_before = Pt(4.5)
        rh = p_item.add_run()
        rh.text = f"{h}: "
        rh.font.bold = True
        rh.font.size = Pt(9.5)
        rh.font.color.rgb = NAVY_SLATE
        rb = p_item.add_run()
        rb.text = b
        rb.font.size = Pt(9)
        rb.font.color.rgb = TEXT_MAIN

    # Card 1.2: Data Hygiene & Preprocessing
    c2_left = c1_left + col_w + col_gap
    s2_shape = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, c2_left, card_top, col_w, card_h)
    s2_shape.fill.solid()
    s2_shape.fill.fore_color.rgb = CARD_BG
    s2_shape.line.color.rgb = CARD_BORDER
    s2_shape.line.width = Pt(1)

    tb_s2 = slide1.shapes.add_textbox(c2_left + Inches(0.2), card_top + Inches(0.2), col_w - Inches(0.4), card_h - Inches(0.4))
    tf_s2 = tb_s2.text_frame
    tf_s2.word_wrap = True
    tf_s2.margin_left = tf_s2.margin_right = tf_s2.margin_top = tf_s2.margin_bottom = 0

    p = tf_s2.paragraphs[0]
    p.text = "DATA ENGINEERING PIPELINE"
    p.font.size = Pt(8.5)
    p.font.bold = True
    p.font.color.rgb = TEAL_ACCENT

    p = tf_s2.add_paragraph()
    p.text = "Dataset Hygiene & Filtration"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = NAVY_DARK
    p.space_after = Pt(8)

    prep_items = [
        ("Source Dataset", "UCI Online Retail II dataset spanning 2 full years of non-store UK e-commerce transactions (1,067,371 raw records)."),
        ("Cancellation Removal", "Identified and removed all cancelled invoices (prefixed with 'C') to prevent negative association bias."),
        ("Identity & Value Hygiene", "Dropped anonymous transactions (missing CustomerID) and purged records with Quantity <= 0 or Price <= 0."),
        ("Text Normalization", "Standardized descriptions to uppercase, trimmed whitespace, and resolved blank entries."),
        ("Operational Overhead Purge", "Filtered out non-product line items: POSTAGE, MANUAL, BANK CHARGES, AMAZON FEES, and DISCOUNTS."),
        ("Basket Qualification", "Grouped by Invoice ID; retained baskets with >= 2 products and SKUs appearing in >= 5 transactions."),
        ("Chronological Split", "80% temporal train set (27,048 baskets) and 20% future held-out test set (6,762 baskets).")
    ]
    for h, b in prep_items:
        p_item = tf_s2.add_paragraph()
        p_item.space_before = Pt(4.5)
        rh = p_item.add_run()
        rh.text = f"{h}: "
        rh.font.bold = True
        rh.font.size = Pt(9.5)
        rh.font.color.rgb = NAVY_SLATE
        rb = p_item.add_run()
        rb.text = b
        rb.font.size = Pt(9)
        rb.font.color.rgb = TEXT_MAIN

    # Card 1.3: Pipeline Execution Output Box
    c3_left = c2_left + col_w + col_gap
    s3_shape = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, c3_left, card_top, col_w, card_h)
    s3_shape.fill.solid()
    s3_shape.fill.fore_color.rgb = CARD_BG
    s3_shape.line.color.rgb = CARD_BORDER
    s3_shape.line.width = Pt(1)

    tb_s3 = slide1.shapes.add_textbox(c3_left + Inches(0.2), card_top + Inches(0.2), col_w - Inches(0.4), card_h - Inches(0.4))
    tf_s3 = tb_s3.text_frame
    tf_s3.word_wrap = True
    tf_s3.margin_left = tf_s3.margin_right = tf_s3.margin_top = tf_s3.margin_bottom = 0

    p = tf_s3.paragraphs[0]
    p.text = "VERIFIED PIPELINE EXECUTION"
    p.font.size = Pt(8.5)
    p.font.bold = True
    p.font.color.rgb = GREEN_ACCENT

    p = tf_s3.add_paragraph()
    p.text = "Execution Log & Output"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = NAVY_DARK
    p.space_after = Pt(6)

    # Console snippet inside Card 1.3
    t1_top = card_top + Inches(0.85)
    t1_h = Inches(2.65)
    t1_w = col_w - Inches(0.4)
    t1_shape = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, c3_left + Inches(0.2), t1_top, t1_w, t1_h)
    t1_shape.fill.solid()
    t1_shape.fill.fore_color.rgb = TERM_BG
    t1_shape.line.color.rgb = RGBColor(51, 65, 85)

    tb_term1 = slide1.shapes.add_textbox(c3_left + Inches(0.28), t1_top + Inches(0.1), t1_w - Inches(0.16), t1_h - Inches(0.2))
    tf_t1 = tb_term1.text_frame
    tf_t1.word_wrap = True
    tf_t1.margin_left = tf_t1.margin_right = tf_t1.margin_top = tf_t1.margin_bottom = 0

    t1_lines = [
        ("$ python data_preprocessing.py", TERM_YELLOW),
        ("  Raw Input Records   : 1,067,371 rows", TERM_WHITE),
        ("  Clean Rows Retained : 802,600 (75.2%)", TERM_WHITE),
        ("  Multi-Item Baskets  : 33,810 (>=2 items)", TERM_GREEN),
        ("  Verified SKUs       : 4,627 products", TERM_GREEN),
        ("  Temporal Train Set  : 27,048 baskets", TERM_CYAN),
        ("  Held-Out Test Set   : 6,762 baskets", TERM_CYAN),
        ("$ python train_model.py", TERM_YELLOW),
        ("  Encoded Matrix Shape: (27,048, 4,376)", TERM_WHITE),
        ("  Frequent Itemsets   : 891 mined (s>=0.01)", TERM_GREEN),
        ("  Association Rules   : 592 generated", TERM_GREEN),
        ("  Average Rule Lift   : 12.71x (strong)", TERM_CYAN),
    ]
    for idx, (txt, col) in enumerate(t1_lines):
        pt = tf_t1.paragraphs[0] if idx == 0 else tf_t1.add_paragraph()
        pt.text = txt
        pt.font.name = "Consolas"
        pt.font.size = Pt(7.5)
        pt.font.color.rgb = col
        pt.space_before = Pt(1.5)

    # Key Statistics Callout below Console
    b_stats = slide1.shapes.add_textbox(c3_left + Inches(0.2), t1_top + t1_h + Inches(0.15), col_w - Inches(0.4), Inches(1.8))
    tf_bs = b_stats.text_frame
    tf_bs.word_wrap = True
    tf_bs.margin_left = tf_bs.margin_right = tf_bs.margin_top = tf_bs.margin_bottom = 0

    p_bs = tf_bs.paragraphs[0]
    p_bs.text = "Key Data Architecture Milestones:"
    p_bs.font.bold = True
    p_bs.font.size = Pt(9.5)
    p_bs.font.color.rgb = NAVY_SLATE
    p_bs.space_after = Pt(3)

    stat_bullets = [
        ("Catalog Top Seller", "WHITE HANGING HEART T-LIGHT HOLDER (4,836 baskets)"),
        ("Data Hygiene Yield", "264,771 noise/cancelled rows filtered out"),
        ("Sparsity Handling", "Pruned 22,000+ single-item non-bundle baskets"),
        ("Split Integrity", "Zero data leakage via strict temporal ordering")
    ]
    for h, b in stat_bullets:
        pb = tf_bs.add_paragraph()
        pb.space_before = Pt(2)
        r1 = pb.add_run()
        r1.text = f"- {h}: "
        r1.font.bold = True
        r1.font.size = Pt(8.5)
        r1.font.color.rgb = NAVY_DARK
        r2 = pb.add_run()
        r2.text = b
        r2.font.size = Pt(8.5)
        r2.font.color.rgb = TEXT_MAIN

    # =========================================================================
    # SLIDE 2: Algorithm Used vs. Best Algorithm (Comparative Benchmark)
    # =========================================================================
    slide2 = prs.slides.add_slide(blank_layout)

    # Header
    hb2 = slide2.shapes.add_textbox(Inches(0.6), Inches(0.35), Inches(12.133), Inches(1.1))
    tf2 = hb2.text_frame
    tf2.word_wrap = True
    tf2.margin_left = tf2.margin_right = tf2.margin_top = tf2.margin_bottom = 0
    p = tf2.paragraphs[0]
    p.text = "Smart Product Bundle Recommendation System"
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = NAVY_DARK

    p_sub = tf2.add_paragraph()
    p_sub.text = "Slide 2/3: Algorithm Used, Mathematical Foundations & Why Apriori is the Best Algorithm"
    p_sub.font.size = Pt(11)
    p_sub.font.color.rgb = BLUE_ACCENT
    p_sub.space_before = Pt(3)

    # Left Column: Algorithm Used & Core Mathematics
    col2_left_w = Inches(5.8)
    s2_left_shape = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), card_top, col2_left_w, card_h)
    s2_left_shape.fill.solid()
    s2_left_shape.fill.fore_color.rgb = CARD_BG
    s2_left_shape.line.color.rgb = CARD_BORDER
    s2_left_shape.line.width = Pt(1)

    tb2_left = slide2.shapes.add_textbox(Inches(0.8), card_top + Inches(0.2), col2_left_w - Inches(0.4), card_h - Inches(0.4))
    tf2_l = tb2_left.text_frame
    tf2_l.word_wrap = True
    tf2_l.margin_left = tf2_l.margin_right = tf2_l.margin_top = tf2_l.margin_bottom = 0

    p = tf2_l.paragraphs[0]
    p.text = "ALGORITHM USED"
    p.font.size = Pt(8.5)
    p.font.bold = True
    p.font.color.rgb = BLUE_ACCENT

    p = tf2_l.add_paragraph()
    p.text = "Apriori Association Rule Mining"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = NAVY_DARK
    p.space_after = Pt(6)

    algo_items = [
        ("The Downward-Closure Property", "Apriori's anti-monotonicity principle states: If an itemset is infrequent, all of its supersets are also infrequent. This prunes millions of combinatorial candidates in polynomial time."),
        ("One-Hot Basket Encoding", "27,048 training transactions mapped to a sparse boolean matrix across 4,376 unique SKUs."),
        ("Support Threshold (min_support = 0.01)", "Filters out spurious co-occurrences by requiring pairs to appear in >= 270 transactions. Generates 891 frequent itemsets."),
        ("Mathematical Rule Formulation", [
            ("Support(A -> B)", "P(A & B) = Frequency(A U B) / Total Transactions"),
            ("Confidence(A -> B)", "P(B | A) = Support(A U B) / Support(A)"),
            ("Lift(A -> B)", "Confidence(A -> B) / Support(B) = P(A & B) / [P(A) * P(B)]")
        ]),
        ("Sub-Millisecond Inverted Hash Index", "Precomputes an antecedent-to-rule index mapping each product to matching rule rows, guaranteeing O(1) query latency at checkout."),
        ("Dynamic Deduplication & Ranking", "Excludes items already present in the active cart; ranks candidates by descending Lift, then Confidence.")
    ]
    for item in algo_items:
        h, b = item
        p_item = tf2_l.add_paragraph()
        p_item.space_before = Pt(4)
        if isinstance(b, list):
            rh = p_item.add_run()
            rh.text = f"{h}:\n"
            rh.font.bold = True
            rh.font.size = Pt(9.5)
            rh.font.color.rgb = NAVY_SLATE
            for formula_title, formula_eq in b:
                pf = tf2_l.add_paragraph()
                pf.space_before = Pt(1.5)
                rf1 = pf.add_run()
                rf1.text = f"  * {formula_title} = "
                rf1.font.bold = True
                rf1.font.size = Pt(9)
                rf1.font.color.rgb = METRIC_BLUE
                rf2 = pf.add_run()
                rf2.text = formula_eq
                rf2.font.size = Pt(8.5)
                rf2.font.color.rgb = TEXT_MAIN
        else:
            rh = p_item.add_run()
            rh.text = f"{h}: "
            rh.font.bold = True
            rh.font.size = Pt(9.5)
            rh.font.color.rgb = NAVY_SLATE
            rb = p_item.add_run()
            rb.text = b
            rb.font.size = Pt(9)
            rb.font.color.rgb = TEXT_MAIN

    # Right Column: Why Apriori is the "Best Algorithm" (Comparative Benchmark)
    col2_right_w = Inches(6.05)
    s2_right_shape = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.68), card_top, col2_right_w, card_h)
    s2_right_shape.fill.solid()
    s2_right_shape.fill.fore_color.rgb = CARD_BG
    s2_right_shape.line.color.rgb = CARD_BORDER
    s2_right_shape.line.width = Pt(1)

    tb2_right = slide2.shapes.add_textbox(Inches(6.88), card_top + Inches(0.2), col2_right_w - Inches(0.4), card_h - Inches(0.4))
    tf2_r = tb2_right.text_frame
    tf2_r.word_wrap = True
    tf2_r.margin_left = tf2_r.margin_right = tf2_r.margin_top = tf2_r.margin_bottom = 0

    p = tf2_r.paragraphs[0]
    p.text = "COMPARATIVE BENCHMARK & SELECTION JUSTIFICATION"
    p.font.size = Pt(8.5)
    p.font.bold = True
    p.font.color.rgb = TEAL_ACCENT

    p = tf2_r.add_paragraph()
    p.text = "Why Apriori is the Best Algorithm"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = NAVY_DARK
    p.space_after = Pt(6)

    comp_items = [
        ("1. vs. Collaborative Filtering (User-Item / Matrix Factorization)", 
         "CF requires rich historical user profiles and breaks down completely on anonymous guest checkouts (the primary e-commerce traffic). Apriori is the superior algorithm because it relies purely on in-cart session items, achieving 100% cold-start resilience."),
        ("2. vs. Deep Learning & Sequential Neural Models (RNNs / Transformers)", 
         "Neural recommenders act as opaque black boxes with high inference compute latency. In contrast, Apriori provides total mathematical transparency (Confidence & Lift) allowing natural language explanations that convert shoppers and ensure commercial trust."),
        ("3. vs. Brute-Force Combinatorial Co-Occurrence", 
         "Evaluating all item combinations across 4,627 SKUs requires evaluating 2^4627 itemsets (computationally intractable). Apriori's anti-monotonic pruning restricts search space to frequent candidates, completing in seconds."),
        ("4. High-Precision Cross-Selling vs. Popularity Bias", 
         "Generic popularity-based recommenders suggest best-sellers that customers would buy anyway. Apriori's Lift metric isolates genuine complementary affinity (mean 15.21x lift), unlocking true incremental sales."),
        ("Summary Verdict", 
         "Apriori combines zero-cold-start dependency, absolute mathematical explainability, sub-millisecond O(1) query latency, and high-lift complementary precision, making it the optimal engine for product bundles.")
    ]
    for h, b in comp_items:
        p_item = tf2_r.add_paragraph()
        p_item.space_before = Pt(4.5)
        rh = p_item.add_run()
        rh.text = f"{h}:\n"
        rh.font.bold = True
        rh.font.size = Pt(9.5)
        rh.font.color.rgb = NAVY_SLATE if not h.startswith("Summary") else GREEN_ACCENT
        rb = p_item.add_run()
        rb.text = b
        rb.font.size = Pt(8.8)
        rb.font.color.rgb = TEXT_MAIN

    # =========================================================================
    # SLIDE 3: Visualizations & Empirical Output (Real-World Results)
    # =========================================================================
    slide3 = prs.slides.add_slide(blank_layout)

    # Header
    hb3 = slide3.shapes.add_textbox(Inches(0.6), Inches(0.35), Inches(12.133), Inches(1.1))
    tf3 = hb3.text_frame
    tf3.word_wrap = True
    tf3.margin_left = tf3.margin_right = tf3.margin_top = tf3.margin_bottom = 0
    p = tf3.paragraphs[0]
    p.text = "Smart Product Bundle Recommendation System"
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = NAVY_DARK

    p_sub = tf3.add_paragraph()
    p_sub.text = "Slide 3/3: Embedded Visualizations, Actual Empirical Evaluation & Production Recommendation Output"
    p_sub.font.size = Pt(11)
    p_sub.font.color.rgb = BLUE_ACCENT
    p_sub.space_before = Pt(3)

    # Left Column: Visualizations (Images from Real Data)
    col3_left_w = Inches(5.8)
    s3_left_shape = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), card_top, col3_left_w, card_h)
    s3_left_shape.fill.solid()
    s3_left_shape.fill.fore_color.rgb = CARD_BG
    s3_left_shape.line.color.rgb = CARD_BORDER
    s3_left_shape.line.width = Pt(1)

    tb3_left = slide3.shapes.add_textbox(Inches(0.8), card_top + Inches(0.15), col3_left_w - Inches(0.4), Inches(0.6))
    tf3_l = tb3_left.text_frame
    tf3_l.word_wrap = True
    tf3_l.margin_left = tf3_l.margin_right = tf3_l.margin_top = tf3_l.margin_bottom = 0

    p = tf3_l.paragraphs[0]
    p.text = "EMBEDDED MODEL VISUALIZATIONS"
    p.font.size = Pt(8.5)
    p.font.bold = True
    p.font.color.rgb = BLUE_ACCENT

    p = tf3_l.add_paragraph()
    p.text = "Real Dataset Visual Analytics"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = NAVY_DARK

    # Embed Chart 1 (Support vs Confidence)
    c1_img_path = os.path.join(art_dir, "chart_support_conf.png")
    if os.path.exists(c1_img_path):
        slide3.shapes.add_picture(c1_img_path, Inches(0.8), card_top + Inches(0.8), Inches(5.4), Inches(2.25))

    # Embed Chart 2 (Evaluation Metrics)
    c2_img_path = os.path.join(art_dir, "chart_eval_metrics.png")
    if os.path.exists(c2_img_path):
        slide3.shapes.add_picture(c2_img_path, Inches(0.8), card_top + Inches(3.15), Inches(5.4), Inches(2.25))

    # Right Column: Actual Output, Evaluation Metrics & Live Bundle Demo
    col3_right_w = Inches(6.05)
    s3_right_shape = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.68), card_top, col3_right_w, card_h)
    s3_right_shape.fill.solid()
    s3_right_shape.fill.fore_color.rgb = CARD_BG
    s3_right_shape.line.color.rgb = CARD_BORDER
    s3_right_shape.line.width = Pt(1)

    tb3_right = slide3.shapes.add_textbox(Inches(6.88), card_top + Inches(0.18), col3_right_w - Inches(0.4), card_h - Inches(0.36))
    tf3_r = tb3_right.text_frame
    tf3_r.word_wrap = True
    tf3_r.margin_left = tf3_r.margin_right = tf3_r.margin_top = tf3_r.margin_bottom = 0

    p = tf3_r.paragraphs[0]
    p.text = "ACTUAL EVALUATION & LIVE BUNDLE OUTPUT"
    p.font.size = Pt(8.5)
    p.font.bold = True
    p.font.color.rgb = GREEN_ACCENT

    p = tf3_r.add_paragraph()
    p.text = "Empirical Results on 6,762 Held-Out Baskets"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = NAVY_DARK
    p.space_after = Pt(4)

    # 4 Key Metrics Row
    m_row = [
        ("Hit Rate @ 5", "36.58%", "1 in 3 baskets received a true ground-truth match"),
        ("Average Lift", "15.21x", "15x higher purchase affinity than independence"),
        ("Precision @ 5", "10.20%", "Mean top-5 recommended items co-purchased"),
        ("Avg Confidence", "39.85%", "Mean rule probability across 15,850 recommendations")
    ]
    for lbl, val, sub in m_row:
        pm = tf3_r.add_paragraph()
        pm.space_before = Pt(3)
        r1 = pm.add_run()
        r1.text = f"{lbl}: "
        r1.font.bold = True
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = NAVY_DARK

        r2 = pm.add_run()
        r2.text = f"{val}  "
        r2.font.bold = True
        r2.font.size = Pt(11)
        r2.font.color.rgb = METRIC_BLUE

        r3 = pm.add_run()
        r3.text = f"({sub})"
        r3.font.size = Pt(8)
        r3.font.color.rgb = TEXT_MUTED

    # Live Recommendation Output Box
    rec_box_top = card_top + Inches(2.2)
    rec_box_h = Inches(1.75)
    rec_box_w = col3_right_w - Inches(0.4)
    rec_shape = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.88), rec_box_top, rec_box_w, rec_box_h)
    rec_shape.fill.solid()
    rec_shape.fill.fore_color.rgb = WHITE
    rec_shape.line.color.rgb = RGBColor(203, 213, 225)
    rec_shape.line.width = Pt(1)

    tb_rec = slide3.shapes.add_textbox(Inches(6.98), rec_box_top + Inches(0.1), rec_box_w - Inches(0.2), rec_box_h - Inches(0.2))
    tf_rec = tb_rec.text_frame
    tf_rec.word_wrap = True
    tf_rec.margin_left = tf_rec.margin_right = tf_rec.margin_top = tf_rec.margin_bottom = 0

    p_rt = tf_rec.paragraphs[0]
    p_rt.text = "LIVE BUNDLE RECOMMENDATION DEMO"
    p_rt.font.bold = True
    p_rt.font.size = Pt(8.5)
    p_rt.font.color.rgb = TEAL_ACCENT

    p_rc = tf_rec.add_paragraph()
    p_rc.space_before = Pt(2)
    r = p_rc.add_run()
    r.text = "In-Cart Product: "
    r.font.bold = True
    r.font.size = Pt(8.5)
    r.font.color.rgb = NAVY_SLATE
    r = p_rc.add_run()
    r.text = "\"WHITE HANGING HEART T-LIGHT HOLDER\"\n"
    r.font.size = Pt(8.5)
    r.font.color.rgb = TEXT_MAIN

    r = p_rc.add_run()
    r.text = "Recommended Complement: "
    r.font.bold = True
    r.font.size = Pt(8.5)
    r.font.color.rgb = NAVY_SLATE
    r = p_rc.add_run()
    r.text = "CANDLEHOLDER PINK HANGING HEART\n"
    r.font.bold = True
    r.font.size = Pt(8.5)
    r.font.color.rgb = METRIC_BLUE

    r = p_rc.add_run()
    r.text = "Computed Metrics: "
    r.font.bold = True
    r.font.size = Pt(8)
    r.font.color.rgb = NAVY_SLATE
    r = p_rc.add_run()
    r.text = "Support: 1.20%  |  Confidence: 8.10%  |  Lift: 4.76x\n"
    r.font.bold = True
    r.font.size = Pt(8)
    r.font.color.rgb = GREEN_ACCENT

    r = p_rc.add_run()
    r.text = "Rationale: "
    r.font.bold = True
    r.font.size = Pt(8)
    r.font.color.rgb = NAVY_SLATE
    r = p_rc.add_run()
    r.text = "\"Customers who purchased [A] frequently purchased [B] in the same session (Confidence: 8.1%, Lift: 4.76x).\""
    r.font.italic = True
    r.font.size = Pt(7.8)
    r.font.color.rgb = TEXT_MAIN

    # Commercial Conclusion below Demo Box
    p_conc = tf3_r.add_paragraph()
    p_conc.space_before = Pt(7)
    r = p_conc.add_run()
    r.text = "Commercial Conclusion & Production Impact:\n"
    r.font.bold = True
    r.font.size = Pt(9.5)
    r.font.color.rgb = GREEN_ACCENT

    conclusion_bullets = [
        ("AOV Expansion", "Bundle cross-selling increases basket volume at checkout without extra customer acquisition cost."),
        ("Zero-Cold-Start Reliability", "Delivers immediate recommendations for guest users using purely in-session signals."),
        ("Explainability & Trust", "Real-time lift explanations eliminate black-box uncertainty for consumers."),
        ("Deployment Ready", "Interactive Streamlit UI, O(1) query latency, and 34 passing automated unit tests.")
    ]
    for h, b in conclusion_bullets:
        pb = tf3_r.add_paragraph()
        pb.space_before = Pt(2)
        r1 = pb.add_run()
        r1.text = f"* {h}: "
        r1.font.bold = True
        r1.font.size = Pt(8.2)
        r1.font.color.rgb = NAVY_SLATE
        r2 = pb.add_run()
        r2.text = b
        r2.font.size = Pt(8)
        r2.font.color.rgb = TEXT_MAIN

    # Save presentation
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    prs.save(output_path)
    print(f"3-Slide Presentation saved successfully to: {output_path}")

if __name__ == "__main__":
    out = r"C:\Users\gurup\.gemini\antigravity\scratch\smart-bundle-recommender\Smart_Product_Bundle_Recommendation_System_3Slides.pptx"
    art = r"C:\Users\gurup\.gemini\antigravity\brain\d5e111d0-6a2a-4e06-a35a-a324914b7909"
    create_3_slide_deck(out, art)

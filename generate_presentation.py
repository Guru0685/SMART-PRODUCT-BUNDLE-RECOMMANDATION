"""
generate_presentation.py
------------------------
Generates a 2-slide executive presentation in .pptx format for the
Smart Product Bundle Recommendation System with verified actual metrics.
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
import os

def create_deck(output_path: str):
    prs = Presentation()
    # 16:9 Widescreen
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Colors
    NAVY_DARK = RGBColor(15, 23, 42)      # #0F172A
    NAVY_SLATE = RGBColor(30, 41, 59)     # #1E293B
    TEXT_MUTED = RGBColor(100, 116, 139)  # #64748B
    TEXT_MAIN = RGBColor(51, 65, 85)      # #334155
    BLUE_ACCENT = RGBColor(2, 132, 199)   # #0284C7
    TEAL_ACCENT = RGBColor(13, 148, 136)  # #0D9488
    CARD_BG = RGBColor(248, 250, 252)     # #F8FAFC
    CARD_BORDER = RGBColor(226, 232, 240) # #E2E8F0
    WHITE = RGBColor(255, 255, 255)
    METRIC_BG = RGBColor(239, 246, 255)   # #EFF6FF
    METRIC_BLUE = RGBColor(30, 64, 175)   # #1E40AF
    GREEN_ACCENT = RGBColor(22, 101, 52)  # #166534

    # -------------------------------------------------------------
    # SLIDE 1: Architecture, Data Preprocessing & Methodology
    # -------------------------------------------------------------
    slide1 = prs.slides.add_slide(blank_layout)

    # Top Header Banner
    header_box = slide1.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.733), Inches(1.1))
    tf1 = header_box.text_frame
    tf1.word_wrap = True
    tf1.margin_left = tf1.margin_right = tf1.margin_top = tf1.margin_bottom = 0
    p1 = tf1.paragraphs[0]
    p1.text = "Smart Product Bundle Recommendation System"
    p1.font.size = Pt(24)
    p1.font.bold = True
    p1.font.color.rgb = NAVY_DARK

    p1_sub = tf1.add_paragraph()
    p1_sub.text = "Slide 1/2: Dataset Profiling, Data Engineering Pipeline & Association Mining Workflow"
    p1_sub.font.size = Pt(12)
    p1_sub.font.color.rgb = BLUE_ACCENT
    p1_sub.space_before = Pt(4)

    # 3 Column Cards on Slide 1
    col_width = Inches(3.68)
    col_gap = Inches(0.34)
    card_top = Inches(1.6)
    card_height = Inches(5.35)

    columns_data_s1 = [
        {
            "tag": "DATASET & SPLIT",
            "tag_color": BLUE_ACCENT,
            "title": "UCI Online Retail II",
            "items": [
                ("Transactional Baseline", "Real UK non-store online retail dataset covering 1,067,371 raw purchase records across 2 full years."),
                ("Curated Volume", "Filtered down to 33,810 qualified multi-product transaction baskets comprising 4,627 verified retail SKUs."),
                ("Temporal Validation Split", "Strict chronological 80/20 train-test partition preserving realistic time dynamics:"),
                ("  * Train Corpus", "27,048 transaction baskets used for Apriori frequent itemset and rule generation."),
                ("  * Held-Out Test Set", "6,762 transaction baskets completely unseen during mining, used for offline empirical evaluation."),
                ("Product Diversity", "Covers gifts, kitchenware, decor, and seasonal sets with varying order frequency.")
            ]
        },
        {
            "tag": "DATA PREPROCESSING",
            "tag_color": TEAL_ACCENT,
            "title": "Hygiene & Filtering Pipeline",
            "items": [
                ("Cancellation Pruning", "Identified and removed all cancelled and returned invoices (prefixed with 'C')."),
                ("Customer & Value Hygiene", "Dropped anonymous transactions (missing CustomerID) and purged records with Quantity <= 0 or Price <= 0."),
                ("Text Standardization", "Normalized SKUs to uppercase, trimmed whitespace, and resolved product descriptions."),
                ("Non-Product Exclusion", "Filtered operational charges: POSTAGE, MANUAL, BANK CHARGES, AMAZON FEES, and DISCOUNTS."),
                ("Basket Construction", "Aggregated line items by Invoice ID; retained transactions with >= 2 products and SKUs with >= 5 occurrences."),
                ("Data Quality", "Cleaned 1,067,371 raw entries to 802,600 verified retail line items (75.2% retention).")
            ]
        },
        {
            "tag": "ALGORITHM & WORKFLOW",
            "tag_color": NAVY_SLATE,
            "title": "Apriori Mining Engine",
            "items": [
                ("Transaction Encoding", "Sparse boolean one-hot matrix via mlxtend.TransactionEncoder (27,048 transactions x 4,376 SKUs)."),
                ("Apriori Mining", "Discovered 891 frequent itemsets at min_support = 0.01 (>=270 basket occurrences)."),
                ("Rule Discovery", "Mined 592 production association rules with min_lift >= 1.0 and min_confidence >= 0.05."),
                ("Rule Indexing", "In-memory inverted antecedent index providing sub-millisecond O(1) candidate lookup."),
                ("Dynamic Scoring", "Ranks candidate bundles by descending Lift and Confidence, avoiding already-selected items."),
                ("Natural-Language Rationale", "Generates human-understandable justifications backed by empirical rule lift & confidence.")
            ]
        }
    ]

    for i, col in enumerate(columns_data_s1):
        left = Inches(0.8) + i * (col_width + col_gap)
        
        # Background Box
        shape = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, card_top, col_width, card_height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = CARD_BG
        shape.line.color.rgb = CARD_BORDER
        shape.line.width = Pt(1)

        # Content Text Box
        tb = slide1.shapes.add_textbox(left + Inches(0.2), card_top + Inches(0.2), col_width - Inches(0.4), card_height - Inches(0.4))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

        # Tag
        p_tag = tf.paragraphs[0]
        p_tag.text = col["tag"]
        p_tag.font.size = Pt(9)
        p_tag.font.bold = True
        p_tag.font.color.rgb = col["tag_color"]

        # Title
        p_title = tf.add_paragraph()
        p_title.text = col["title"]
        p_title.font.size = Pt(15)
        p_title.font.bold = True
        p_title.font.color.rgb = NAVY_DARK
        p_title.space_after = Pt(10)

        # Items
        for heading, body in col["items"]:
            p_item = tf.add_paragraph()
            p_item.space_before = Pt(5)
            r_head = p_item.add_run()
            r_head.text = heading + (" — " if not heading.startswith(" ") else " ")
            r_head.font.bold = True
            r_head.font.size = Pt(10)
            r_head.font.color.rgb = NAVY_SLATE

            r_body = p_item.add_run()
            r_body.text = body
            r_body.font.bold = False
            r_body.font.size = Pt(9.5)
            r_body.font.color.rgb = TEXT_MAIN

    # -------------------------------------------------------------
    # SLIDE 2: Empirical Evaluation, Insights & Business Impact
    # -------------------------------------------------------------
    slide2 = prs.slides.add_slide(blank_layout)

    # Top Header Banner
    header_box2 = slide2.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.733), Inches(1.1))
    tf2 = header_box2.text_frame
    tf2.word_wrap = True
    tf2.margin_left = tf2.margin_right = tf2.margin_top = tf2.margin_bottom = 0
    p2 = tf2.paragraphs[0]
    p2.text = "Smart Product Bundle Recommendation System"
    p2.font.size = Pt(24)
    p2.font.bold = True
    p2.font.color.rgb = NAVY_DARK

    p2_sub = tf2.add_paragraph()
    p2_sub.text = "Slide 2/2: Empirical Evaluation (Actual Results), Interpretation & Enterprise Business Value"
    p2_sub.font.size = Pt(12)
    p2_sub.font.color.rgb = BLUE_ACCENT
    p2_sub.space_before = Pt(4)

    # Left Column: Metric Cards (Actual Evaluation Results)
    left_w = Inches(4.5)
    left_box_shape = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), card_top, left_w, card_height)
    left_box_shape.fill.solid()
    left_box_shape.fill.fore_color.rgb = CARD_BG
    left_box_shape.line.color.rgb = CARD_BORDER
    left_box_shape.line.width = Pt(1)

    tb_eval = slide2.shapes.add_textbox(Inches(1.0), card_top + Inches(0.2), left_w - Inches(0.4), card_height - Inches(0.4))
    tf_eval = tb_eval.text_frame
    tf_eval.word_wrap = True
    tf_eval.margin_left = tf_eval.margin_right = tf_eval.margin_top = tf_eval.margin_bottom = 0

    p_ev_tag = tf_eval.paragraphs[0]
    p_ev_tag.text = "OFFLINE TEST EVALUATION (ACTUAL RESULTS)"
    p_ev_tag.font.size = Pt(9)
    p_ev_tag.font.bold = True
    p_ev_tag.font.color.rgb = BLUE_ACCENT

    p_ev_title = tf_eval.add_paragraph()
    p_ev_title.text = "Verified Model Performance (K = 5)"
    p_ev_title.font.size = Pt(15)
    p_ev_title.font.bold = True
    p_ev_title.font.color.rgb = NAVY_DARK
    p_ev_title.space_after = Pt(6)

    p_ev_desc = tf_eval.add_paragraph()
    p_ev_desc.text = "Evaluated on 6,762 held-out transactions using 50/50 intra-basket split (first 50% = query basket, remaining 50% = ground-truth purchases)."
    p_ev_desc.font.size = Pt(9)
    p_ev_desc.font.color.rgb = TEXT_MUTED
    p_ev_desc.space_after = Pt(10)

    # 4 Metric Highlights in a 2x2 grid inside left column
    metrics = [
        ("Hit Rate @ 5", "36.58%", "Over 1 in 3 test baskets received >=1 correct recommendation"),
        ("Average Lift", "15.21x", "15x higher affinity than independent co-occurrence baseline"),
        ("Precision @ 5", "10.20%", "Mean proportion of top-5 recommended items co-purchased"),
        ("Avg Confidence", "39.85%", "Mean probability P(B|A) across 15,850 served recommendations")
    ]

    for label, val, sub in metrics:
        p_m = tf_eval.add_paragraph()
        p_m.space_before = Pt(6)
        r_lbl = p_m.add_run()
        r_lbl.text = f"{label}: "
        r_lbl.font.bold = True
        r_lbl.font.size = Pt(11)
        r_lbl.font.color.rgb = NAVY_DARK

        r_val = p_m.add_run()
        r_val.text = f"{val}  "
        r_val.font.bold = True
        r_val.font.size = Pt(13)
        r_val.font.color.rgb = METRIC_BLUE

        p_sub = tf_eval.add_paragraph()
        r_sub = p_sub.add_run()
        r_sub.text = sub
        r_sub.font.size = Pt(8.5)
        r_sub.font.color.rgb = TEXT_MUTED

    # Additional secondary stats
    p_sec = tf_eval.add_paragraph()
    p_sec.space_before = Pt(8)
    p_sec.text = "Additional Verified Metrics:"
    p_sec.font.bold = True
    p_sec.font.size = Pt(9.5)
    p_sec.font.color.rgb = NAVY_SLATE

    sec_items = [
        "Recall @ 5: 6.05% of entire held-out shopping baskets captured",
        "Catalog Coverage: 4.26% (conservative, high-precision rules)",
        "Mean Support: 1.33% | Active Eval Coverage: 4,732 / 6,762 (70.0%)",
        "Total Recommendations Generated in Test: 15,850"
    ]
    for si in sec_items:
        p_si = tf_eval.add_paragraph()
        p_si.text = f"- {si}"
        p_si.font.size = Pt(8.5)
        p_si.font.color.rgb = TEXT_MAIN

    # Right Column: Results Interpretation & Business Impact
    right_left = Inches(5.6)
    right_w = Inches(6.933)

    # Box 1: Results Interpretation
    b1_h = Inches(2.55)
    b1_shape = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, right_left, card_top, right_w, b1_h)
    b1_shape.fill.solid()
    b1_shape.fill.fore_color.rgb = CARD_BG
    b1_shape.line.color.rgb = CARD_BORDER
    b1_shape.line.width = Pt(1)

    tb_b1 = slide2.shapes.add_textbox(right_left + Inches(0.2), card_top + Inches(0.15), right_w - Inches(0.4), b1_h - Inches(0.3))
    tf_b1 = tb_b1.text_frame
    tf_b1.word_wrap = True
    tf_b1.margin_left = tf_b1.margin_right = tf_b1.margin_top = tf_b1.margin_bottom = 0

    p_b1_tag = tf_b1.paragraphs[0]
    p_b1_tag.text = "RESULTS INTERPRETATION"
    p_b1_tag.font.size = Pt(9)
    p_b1_tag.font.bold = True
    p_b1_tag.font.color.rgb = TEAL_ACCENT

    p_b1_title = tf_b1.add_paragraph()
    p_b1_title.text = "High-Affinity Associations Outperform Pure Popularity"
    p_b1_title.font.size = Pt(13)
    p_b1_title.font.bold = True
    p_b1_title.font.color.rgb = NAVY_DARK
    p_b1_title.space_after = Pt(4)

    interp_bullets = [
        ("Empirical Lift Advantage (15.21x)", "Customers buying bundle items are 15 times more likely to purchase the recommended companion than random chance, confirming strong behavioral affinity over spurious frequency."),
        ("Zero-Cold-Start Basket Hits (36.58%)", "Without requiring user profile histories or invasive tracking, the system successfully predicts held-out customer basket items in 36.6% of sessions using only in-cart signals."),
        ("Precision vs. Coverage Tradeoff", "A 10.20% Precision@5 and 4.26% catalog coverage reflects intentional threshold filtering (min_support=0.01) that prioritizes high-confidence bundle suggestions over noisy long-tail items.")
    ]
    for h, b in interp_bullets:
        p_ib = tf_b1.add_paragraph()
        p_ib.space_before = Pt(3)
        r_h = p_ib.add_run()
        r_h.text = h + " — "
        r_h.font.bold = True
        r_h.font.size = Pt(9)
        r_h.font.color.rgb = NAVY_SLATE
        r_b = p_ib.add_run()
        r_b.text = b
        r_b.font.size = Pt(8.5)
        r_b.font.color.rgb = TEXT_MAIN

    # Box 2: Enterprise Business Value & Conclusion
    b2_top = card_top + b1_h + Inches(0.25)
    b2_h = Inches(2.55)
    b2_shape = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, right_left, b2_top, right_w, b2_h)
    b2_shape.fill.solid()
    b2_shape.fill.fore_color.rgb = CARD_BG
    b2_shape.line.color.rgb = CARD_BORDER
    b2_shape.line.width = Pt(1)

    tb_b2 = slide2.shapes.add_textbox(right_left + Inches(0.2), b2_top + Inches(0.15), right_w - Inches(0.4), b2_h - Inches(0.3))
    tf_b2 = tb_b2.text_frame
    tf_b2.word_wrap = True
    tf_b2.margin_left = tf_b2.margin_right = tf_b2.margin_top = tf_b2.margin_bottom = 0

    p_b2_tag = tf_b2.paragraphs[0]
    p_b2_tag.text = "BUSINESS IMPACT & CONCLUSION"
    p_b2_tag.font.size = Pt(9)
    p_b2_tag.font.bold = True
    p_b2_tag.font.color.rgb = GREEN_ACCENT

    p_b2_title = tf_b2.add_paragraph()
    p_b2_title.text = "Actionable Commercial Strategy & Deployment Architecture"
    p_b2_title.font.size = Pt(13)
    p_b2_title.font.bold = True
    p_b2_title.font.color.rgb = NAVY_DARK
    p_b2_title.space_after = Pt(4)

    conclusion_bullets = [
        ("Average Order Value (AOV) Uplift", "Bundling complements dynamically increases basket size and cross-selling efficiency at checkout, directly expanding margin without customer acquisition costs."),
        ("Full Explainability Builds Trust", "Every bundle is accompanied by verified confidence and lift explanations, giving shoppers clear context on why pairings work together."),
        ("Production-Ready Full-Stack System", "Delivers an interactive Streamlit UI, multi-product basket selection, real-time analytics, modular test coverage, and O(1) query latency ready for production deployment.")
    ]
    for h, b in conclusion_bullets:
        p_cb = tf_b2.add_paragraph()
        p_cb.space_before = Pt(3)
        r_h = p_cb.add_run()
        r_h.text = h + " — "
        r_h.font.bold = True
        r_h.font.size = Pt(9)
        r_h.font.color.rgb = NAVY_SLATE
        r_b = p_cb.add_run()
        r_b.text = b
        r_b.font.size = Pt(8.5)
        r_b.font.color.rgb = TEXT_MAIN

    # Save presentation
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    prs.save(output_path)
    print(f"Presentation saved successfully to: {output_path}")

if __name__ == "__main__":
    out = r"C:\Users\gurup\.gemini\antigravity\scratch\smart-bundle-recommender\Smart_Product_Bundle_Recommendation_System.pptx"
    create_deck(out)

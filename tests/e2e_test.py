"""End-to-end pipeline test script."""
import warnings
import pickle
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

warnings.filterwarnings("ignore")

print("=== End-to-End Pipeline Test ===")
print(f"Working dir: {os.getcwd()}")

# Step 1: Preprocessing (synthetic data, no download)
print("\n[1] Running preprocessing...")
from data_preprocessing import load_or_preprocess
info = load_or_preprocess(data_dir="data", force=False)
print(f"  Transactions: {info.total_transactions}")
print(f"  Unique products: {info.unique_products}")
print(f"  Train size: {info.train_size}")
print(f"  Test size: {info.test_size}")
print(f"  Top product: {info.top_products[0][0]} ({info.top_products[0][1]} txns)")

# Step 2: Model training
print("\n[2] Training model...")
from train_model import train_or_load
with open("data/transactions_train.pkl", "rb") as f:
    train_txns = pickle.load(f)
itemsets, rules, meta = train_or_load(transactions=train_txns, force=False)
print(f"  Frequent itemsets: {meta['num_itemsets']}")
print(f"  Association rules: {meta['num_rules']}")
print(f"  Avg lift: {meta['avg_lift']:.3f}")

# Step 3: Recommendations
print("\n[3] Testing recommendations...")
from recommendation_engine import BundleRecommender
rec = BundleRecommender(rules)
sample_product = info.top_products[0][0]
recs = rec.get_recommendations([sample_product], min_confidence=0.0, min_lift=1.0, top_n=3)
print(f"  Selected product: {sample_product}")
print(f"  Got {len(recs)} recommendations")
if recs:
    r = recs[0]
    print(f"  Top rec bundle: {r.bundle_name[:80]}")
    print(f"  Lift: {r.lift:.2f}, Confidence: {r.confidence:.2f}")

# Step 4: Evaluation
print("\n[4] Running evaluation...")
from evaluate_model import evaluate_recommender
with open("data/transactions_test.pkl", "rb") as f:
    test_txns = pickle.load(f)
result = evaluate_recommender(rec, test_txns, k=5)
print(f"  Evaluated: {result.evaluated}")
print(f"  Test transactions: {result.num_test_transactions}")
print(f"  Hit Rate@5: {result.hit_rate_at_k:.3f}")
print(f"  Precision@5: {result.precision_at_k:.3f}")
print(f"  Recall@5: {result.recall_at_k:.3f}")

# Step 5: Search
print("\n[5] Testing product search...")
all_products = rec.all_products
query = all_products[0][:8]
found = rec.search_products(query, all_products)
print(f"  Search query: '{query}'")
print(f"  Found {len(found)} matching products")

print("\n=== All tests passed! ===")

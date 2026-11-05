# 🛒 Smart Product Bundle Recommendation System

> **Boost cross-sell revenue with AI-powered product bundle recommendations using Market Basket Analysis.**

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?logo=streamlit&logoColor=white)
![mlxtend](https://img.shields.io/badge/mlxtend-0.23%2B-orange)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📋 Table of Contents

1. [Project Overview](#-project-overview)
2. [Features](#-features)
3. [Technology Stack](#-technology-stack)
4. [Machine Learning Methodology](#-machine-learning-methodology)
5. [Project Structure](#-project-structure)
6. [Installation & Setup](#-installation--setup)
7. [Usage Guide](#-usage-guide)
8. [Dataset](#-dataset)
9. [Running Tests](#-running-tests)
10. [Known Limitations](#-known-limitations)
11. [Future Improvements](#-future-improvements)
12. [License](#-license)

---

## 🔍 Project Overview

The **Smart Product Bundle Recommendation System** is an end-to-end machine learning application that analyzes historical transaction data to surface intelligent product bundle recommendations. By mining patterns in customer purchase history, the system identifies which products are frequently bought together and presents actionable bundle suggestions through an interactive Streamlit dashboard.

### 💼 Business Value

| Benefit | Description |
|---|---|
| 📈 **Cross-Selling** | Automatically surface complementary products at the right moment |
| 💰 **AOV Improvement** | Increase Average Order Value by encouraging multi-item purchases |
| 😊 **Customer Satisfaction** | Reduce discovery friction — show customers what they didn't know they needed |
| 🧠 **Data-Driven Decisions** | Replace gut-feel merchandising with statistically validated association rules |

### 🧮 Core ML Concept: Market Basket Analysis

The system uses **Market Basket Analysis (MBA)** with the **Apriori algorithm** to mine association rules from transactional data. It discovers relationships like *"Customers who buy Product A also tend to buy Product B"*, quantified through interpretable metrics (support, confidence, and lift) that determine bundle quality and ranking.

---

## ✨ Features

### 📊 Dashboard Pages

| Page | Description |
|---|---|
| 🏠 **Dashboard** | High-level KPIs: total transactions, unique products, rules mined, avg. lift |
| 🔮 **Recommender** | Interactive bundle recommender — select a product and get ranked bundle suggestions |
| 📉 **Analytics** | Deep-dive charts: support/confidence/lift distributions, top product pairs, heatmaps |
| 🧪 **Evaluation** | Model performance metrics on a held-out test set (Precision@K, Recall@K, Hit Rate@K) |
| 📂 **Dataset** | Explore, filter, and preview the underlying transaction dataset |

### 📐 Computed Metrics

- **Support** — How often a product pair appears together in all transactions
- **Confidence** — How often the rule is correct given the antecedent is present
- **Lift** — How much more likely the consequent is given the antecedent, vs. at random
- **Precision@K, Recall@K, Hit Rate@K** — Offline evaluation of recommendation quality

### 🖱️ Interactive Features

- 🔎 Product search with autocomplete
- 🎚️ Adjustable support / confidence / lift sliders
- 📤 Export recommendations as CSV
- 📅 Date range filtering for analytics
- 🌍 Country-level segmentation

---

## 🛠️ Technology Stack

| Technology | Purpose | Version |
|---|---|---|
| **Python** | Core language | 3.9+ |
| **Streamlit** | Interactive web dashboard | 1.x |
| **mlxtend** | Apriori algorithm & association rule mining | 0.23+ |
| **pandas** | Data wrangling & preprocessing | 2.x |
| **NumPy** | Numerical operations | 1.24+ |
| **matplotlib** | Static charts & visualizations | 3.7+ |
| **seaborn** | Statistical plots & heatmaps | 0.12+ |
| **plotly** | Interactive charts | 5.x |
| **scikit-learn** | Train/test splitting & evaluation utilities | 1.3+ |
| **pytest** | Unit & integration testing | 7.x |
| **ucimlrepo** | Programmatic dataset download | latest |

---

## 🧠 Machine Learning Methodology

### Apriori Algorithm Overview

The Apriori algorithm is a classic **frequent itemset mining** technique. It works by:

1. Scanning the transaction database to count individual item frequencies
2. Pruning items that fall below a **minimum support** threshold
3. Generating candidate itemsets of increasing size (2-itemsets, 3-itemsets, …) from the surviving frequent items
4. Applying the **downward closure property**: any subset of a frequent itemset must also be frequent
5. Extracting **association rules** from the frequent itemsets and filtering by confidence and lift

### 📏 Key Formulas

**Support** — measures how often the pair appears across all transactions:

```
support(A → B) = freq(A ∪ B) / N
```

Where `freq(A ∪ B)` is the number of transactions containing both A and B, and `N` is the total number of transactions.

**Confidence** — measures the conditional probability of B given A:

```
confidence(A → B) = freq(A ∪ B) / freq(A)
```

Where `freq(A)` is the number of transactions containing A.

**Lift** — measures how much more likely B is purchased with A compared to random chance:

```
lift(A → B) = confidence(A → B) / support(B)
```

### 📖 Interpreting the Metrics for Bundle Recommendations

| Metric | Value | Meaning |
|---|---|---|
| **Lift > 1** | Positive association | Products are more likely to be bought together than by chance — **strong bundle candidate** |
| **Lift = 1** | Independence | No meaningful relationship between products |
| **Lift < 1** | Negative association | Products are bought together **less** than chance would suggest — avoid bundling |
| **High Confidence** | Reliable rule | A large proportion of A-buyers also buy B |
| **Low Support** | Niche pair | The combo is real but rare — may not justify a mass promotion |

> **Rule of thumb for bundle curation:** Prioritize rules with **lift > 1.5** and **confidence > 0.3** for actionable recommendations. Adjust thresholds depending on catalog size and transaction volume.

### 🧪 Evaluation Approach

The model is evaluated using an **80/20 temporal split** — the earliest 80% of transactions are used for training (rule mining) and the most recent 20% are used as a held-out test set. This simulates a realistic deployment scenario where the model must generalize to future purchases.

**Evaluation Metrics (at cutoff K):**

```
Precision@K  = (Recommended items in top-K that were actually purchased) / K

Recall@K     = (Recommended items in top-K that were actually purchased) / (Total items purchased)

Hit Rate@K   = 1 if at least one recommended item in top-K was purchased, else 0
             (averaged over all test baskets)
```

These metrics jointly capture **accuracy** (Precision), **coverage** (Recall), and **usefulness** (Hit Rate) of the recommendation engine.

---

## 📁 Project Structure

```
smart-bundle-recommender/
│
├── app.py                      # Streamlit entry point — multi-page router
│
├── pages/
│   ├── 01_Dashboard.py         # KPI overview page
│   ├── 02_Recommender.py       # Interactive product recommender
│   ├── 03_Analytics.py         # Association rule analytics & charts
│   ├── 04_Evaluation.py        # Offline model evaluation metrics
│   └── 05_Dataset.py           # Dataset explorer & preview
│
├── data_preprocessing.py       # Raw data ingestion, cleaning & basket encoding
├── model.py                    # Apriori rule mining, caching & recommendation logic
├── evaluation.py               # Precision@K, Recall@K, Hit Rate@K computation
├── utils.py                    # Shared helper functions (formatting, filtering, exports)
│
├── data/
│   ├── raw/                    # Original downloaded dataset (auto-populated)
│   └── processed/              # Cleaned transaction matrix & mined rules cache
│
├── tests/
│   ├── test_preprocessing.py   # Unit tests for data cleaning functions
│   ├── test_model.py           # Unit tests for rule mining & recommendation logic
│   └── test_evaluation.py      # Unit tests for evaluation metric calculations
│
├── requirements.txt            # Python dependency list
├── .streamlit/
│   └── config.toml             # Streamlit theme & server configuration
└── README.md                   # This file
```

---

## 🚀 Installation & Setup

### Prerequisites

- Python 3.9 or higher
- `pip` package manager
- (~50 MB disk space for the dataset)

### Step-by-Step

```bash
# 1. Clone / navigate to project
cd smart-bundle-recommender

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate      # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Pre-download & preprocess the dataset
#    This caches the cleaned data so the app starts faster
python data_preprocessing.py

# 5. Run the app
streamlit run app.py
```

The app will open automatically at `http://localhost:8501`. 🎉

---

## 📖 Usage Guide

### 🗺️ Navigating the App

Use the **sidebar** to switch between the five pages. The sidebar also exposes global controls:

- **Min Support / Min Confidence sliders** — tune the Apriori thresholds
- **Country filter** — restrict analysis to a specific market
- **Date range picker** — limit transactions to a time window

### 🔮 Getting Bundle Recommendations

1. Navigate to the **Recommender** page
2. Type a product name in the search box (autocomplete will help)
3. Click **Get Recommendations**
4. The table shows suggested bundle partners ranked by **lift** (highest first)
5. Click **Export CSV** to download the results

### 🧪 Running the Evaluation

1. Navigate to the **Evaluation** page
2. Set the **train/test split date** or use the default 80/20 temporal split
3. Choose a value of **K** (default: 5)
4. Click **Run Evaluation** — results appear as metric cards and a bar chart
5. Compare Precision@K, Recall@K, and Hit Rate@K across different threshold settings

### 📊 Interpreting Lift

| Lift Value | Interpretation | Action |
|---|---|---|
| `lift > 2.0` | Very strong association | Feature as a prominent bundle offer |
| `1.5 ≤ lift ≤ 2.0` | Strong association | Include in standard recommendations |
| `1.0 < lift < 1.5` | Moderate association | Use as a secondary suggestion |
| `lift ≤ 1.0` | Weak / no association | Do **not** recommend as a bundle |

---

## 📦 Dataset

### UCI Online Retail II

The project uses the **[Online Retail II dataset](https://archive.ics.uci.edu/ml/datasets/Online+Retail+II)** from the UCI Machine Learning Repository.

> A real-world transactional dataset from a UK-based non-store online retailer, covering all transactions between **01/12/2009** and **09/12/2011**. The company mainly sells unique all-occasion gift-ware.

### 📑 Data Dictionary

| Column | Type | Description |
|---|---|---|
| `InvoiceNo` | string | Unique invoice number; prefix `C` denotes a cancellation |
| `StockCode` | string | Unique product (item) code |
| `Description` | string | Product name / description |
| `Quantity` | integer | Number of units purchased per transaction |
| `InvoiceDate` | datetime | Date and time of the invoice |
| `Price` | float | Unit price in GBP (£) |
| `CustomerID` | string | Unique customer identifier (nullable) |
| `Country` | string | Country where the customer resides |

### 🔧 Preprocessing Steps Applied

1. **Remove cancellations** — drop rows where `InvoiceNo` starts with `C`
2. **Drop nulls** — remove rows with missing `CustomerID` or `Description`
3. **Filter invalid quantities/prices** — remove rows where `Quantity ≤ 0` or `Price ≤ 0`
4. **Deduplicate** — drop exact duplicate rows
5. **Basket encoding** — pivot data into a binary transaction matrix (rows = invoices, columns = products)
6. **Binarize** — convert quantities to 1/0 (purchased or not)

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

To run a specific test file:

```bash
pytest tests/test_model.py -v
```

To run with coverage report:

```bash
pytest tests/ -v --cov=. --cov-report=term-missing
```

---

## ⚠️ Known Limitations

- **Cold Start Problem** — New products with no transaction history cannot appear in association rules. New items need sufficient purchase data before they can be recommended in bundles.

- **Sparse Data for Niche Products** — Low-volume or seasonal products may not reach minimum support thresholds, causing them to be excluded from rule mining even if genuine associations exist.

- **UK Retail Specificity** — The UCI Online Retail II dataset is sourced from a single UK gift retailer. Models trained on this data may not generalize well to other industries, geographies, or product categories without retraining.

- **Apriori Scalability** — The Apriori algorithm can become computationally expensive as catalog size grows. For very large catalogs (millions of SKUs), more scalable algorithms such as **FP-Growth** or **ECLAT** should be considered.

- **No Personalization** — Recommendations are derived from population-level patterns and do not account for individual customer preferences or browsing history.

---

## 🔭 Future Improvements

- [ ] **Collaborative Filtering / Hybrid Approach** — Combine MBA with user-based or item-based collaborative filtering to deliver personalized bundle suggestions
- [ ] **Real-Time Recommendations via API** — Expose a FastAPI endpoint so the recommendation engine can integrate with e-commerce platforms and serve live predictions
- [ ] **User Personalization** — Incorporate individual customer purchase history to shift from population-level rules to user-specific bundle suggestions
- [ ] **A/B Testing Framework** — Instrument recommendations with experiment tracking to measure actual uplift in AOV and conversion rate in production
- [ ] **FP-Growth Upgrade** — Swap Apriori for FP-Growth to handle larger catalogs without the exponential candidate generation step
- [ ] **Seasonal / Temporal Rules** — Mine rules that are time-aware (e.g., holiday bundles) to improve relevance throughout the calendar year

---

## 📄 License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

<p align="center">
  Made with ❤️ and 🛒 by the Smart Bundle Recommender team
</p>

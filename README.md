# Budget Tracker

A local Streamlit-based personal finance dashboard that aggregates transactions from multiple bank accounts, auto-categorizes spending, and tracks budgets, loans, and savings goals.

All data stays on your machine — no cloud uploads, no third-party APIs.

## Supported Banks

| Bank | Format | Auto-Filtered |
|------|--------|---------------|
| PNC (Checking/Debit) | CSV | Credit card payments, internal transfers |
| Capital One | CSV | Payment credits |
| Citi | CSV | Payment credits |
| Discover | CSV | Payments & credits |

Bank format is auto-detected from CSV headers — just upload the export and it figures out the rest.

## Features

- **CSV import** with per-bank parsing rules and duplicate detection
- **Hierarchical categories** — top-level baskets (Food & Drink, Housing, etc.) with sub-categories (Groceries, Dining, Coffee)
- **Teachable categorization** — teach a keyword once and all matching transactions get categorized
- **Merchant normalization** — clean up messy bank descriptions (e.g. `AMZN MKTP US*2X4` → Amazon)
- **Recurring transaction detection** — finds subscriptions and bills that appear 3+ consecutive months
- **Budget alerts** — set monthly limits and get warnings when projected to overshoot
- **Savings goals** — track multiple goals with compound interest / HYSA projections
- **Loan tracker** — avalanche vs. snowball payoff strategies, "what if I pay extra?" scenarios
- **Trends** — year-over-year comparison, savings rate over time, 6-month cash flow projection
- **Tax tagging** — mark transactions as deductible with notes
- **Split transactions** — allocate one purchase across multiple categories
- **Duplicate detection** — 4 methods (exact, normalized merchant, suspicious amounts, same-day multiples)

## Setup

```bash
# Clone the repo
git clone <your-repo-url>
cd Budget

# Create a virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# Install dependencies
pip install streamlit pandas plotly pdfplumber numpy

# Launch
streamlit run dashboard.py
```

Opens at `http://localhost:8501`.

## Project Structure

```
dashboard.py              # Main entry point — sidebar router
advanced_tracker.py       # Core engine: parsing, categorization, dedup, insights
income_loan_tracker.py    # Income streams & loan management
savings_goals.py          # Savings goals with compound interest

page_live_view.py         # Current month metrics, alerts, charts
page_upload.py            # CSV upload + sorting interface
page_transactions.py      # Transaction table, uncategorized review, quick actions
page_recurring.py         # Recurring transaction list + missing alerts
page_trends.py            # YoY comparison, savings rate, projections
page_loan_tracker.py      # Loans, strategies, payment history
page_savings_goals.py     # Goals, contributions, interest projections
page_settings.py          # Baskets, interest, income, duplicates, budgets

check_duplicates.py       # CLI utility for duplicate scan/removal
```

## Data Files

All generated at runtime, stored locally, and gitignored:

| File | Contents |
|------|----------|
| `transaction_database.csv` | All imported transactions |
| `category_rules.json` | Keyword → category mappings |
| `category_baskets.json` | Basket → sub-category hierarchy |
| `merchant_normalization.json` | Raw → clean merchant name map |
| `recurring_transactions.json` | Detected recurring transactions |
| `budgets.json` | Monthly budget limits |
| `savings_goals.json` | Goal definitions & contributions |
| `loans.json` | Loan definitions |
| `loan_payments.json` | Payment history per loan |
| `income_streams.json` | Income categorization keywords |
| `split_transactions.json` | Split transaction definitions |
| `tax_deductible.json` | Tax deductible flags & notes |

## Usage

1. **Export CSV** from your bank's website (PNC, Capital One, Citi, or Discover)
2. Go to **Upload Transactions**, drop the CSV, give it a source label, and hit Import
3. Uncategorized transactions appear in the **Sort** section — pick a basket and sub-category for each merchant
4. The keyword is learned automatically — future imports with the same merchant will be categorized
5. Check **Live View** for spending summaries, **Trends** for historical analysis

## Privacy

- Zero network calls — everything runs locally on `localhost`
- Bank CSVs, PDFs, and all data files are gitignored
- No account credentials are stored or needed — you export CSVs manually from your bank

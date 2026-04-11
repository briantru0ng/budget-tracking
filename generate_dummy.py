"""Generate a 3300-row dummy transaction CSV spanning Jan 2023 – Dec 2026."""
import csv, random
from datetime import date, timedelta

random.seed(42)

# Columns: Date,Description,Amount,Category,Source,Normalized_Merchant,Tax_Deductible,Split_ID,Budget_Date
SOURCES = ['PNC Bank', 'Capital One', 'Citi', 'Barclays US', 'Discover']

# (Description template, Category, Amount range (low, high), is_income, tax_deductible)
# Categories match category_baskets.json exactly
TEMPLATES = [
    # Food & Drink — Groceries, Dining
    ('WHOLE FOODS #{n}', 'Groceries', (25, 180), False, False),
    ('TRADER JOES #{n}', 'Groceries', (20, 120), False, False),
    ('H MART #{n}', 'Groceries', (15, 90), False, False),
    ('ALDI #{n}', 'Groceries', (18, 75), False, False),
    ('WEGMANS #{n}', 'Groceries', (30, 150), False, False),
    ('CHIPOTLE #{n}', 'Dining', (10, 25), False, False),
    ('TST*CORNER BISTRO', 'Dining', (15, 65), False, False),
    ('SQ *TACO SHACK', 'Dining', (8, 30), False, False),
    ('DOORDASH*ORDER', 'Dining', (12, 55), False, False),

    # Housing & Utilities — Housing, Internet, Water, Electric
    ('RENT PAYMENT - LANDLORD', 'Housing', (1200, 1800), False, False),
    ('SUBLESSEE RENT SHARE', 'Housing', (600, 900), False, False),
    ('XFINITY INTERNET', 'Internet', (60, 90), False, False),
    ('VERIZON FIOS', 'Internet', (50, 80), False, False),
    ('MUNICIPAL WATER BILL', 'Water', (25, 60), False, False),
    ('WATER UTILITY DISTRICT', 'Water', (20, 55), False, False),
    ('ELECTRIC COMPANY', 'Electric', (50, 200), False, False),
    ('POWER GRID BILLING', 'Electric', (60, 180), False, False),

    # Transportation — Transportation, Gas
    ('UBER TRIP', 'Transportation', (8, 45), False, False),
    ('LYFT RIDE', 'Transportation', (7, 40), False, False),
    ('PARKING GARAGE #{n}', 'Transportation', (5, 25), False, False),
    ('METRO TRANSIT PASS', 'Transportation', (50, 100), False, False),
    ('SHELL OIL #{n}', 'Gas', (30, 70), False, False),
    ('BP GAS #{n}', 'Gas', (25, 65), False, False),
    ('SUNOCO #{n}', 'Gas', (28, 60), False, False),

    # Shopping — Shopping, Electronics
    ('AMAZON MKTP #{n}', 'Shopping', (10, 250), False, False),
    ('TARGET #{n}', 'Shopping', (15, 120), False, False),
    ('HOME DEPOT #{n}', 'Shopping', (20, 300), False, False),
    ('BEST BUY #{n}', 'Electronics', (30, 500), False, False),
    ('APPLE STORE #{n}', 'Electronics', (50, 400), False, False),

    # Entertainment — Entertainment, Gaming
    ('NETFLIX', 'Entertainment', (15, 23), False, False),
    ('SPOTIFY', 'Entertainment', (10, 16), False, False),
    ('HULU', 'Entertainment', (8, 18), False, False),
    ('AMC THEATERS #{n}', 'Entertainment', (12, 35), False, False),
    ('STEAM PURCHASE', 'Gaming', (5, 60), False, False),
    ('PLAYSTATION STORE', 'Gaming', (10, 70), False, False),
    ('XBOX GAME PASS', 'Gaming', (10, 15), False, False),

    # Health & Insurance — Healthcare, Insurance
    ('CVS PHARMACY #{n}', 'Healthcare', (8, 80), False, False),
    ('URGENT CARE COPAY', 'Healthcare', (25, 75), False, True),
    ('DENTAL OFFICE VISIT', 'Healthcare', (50, 200), False, True),
    ('GEICO AUTO INSURANCE', 'Insurance', (100, 200), False, False),
    ('HEALTH INSURANCE PREM', 'Insurance', (150, 350), False, True),

    # Services — Services, Monthly Subscriptions, Yearly Subscriptions
    ('HAIRCUT - BARBER', 'Services', (20, 45), False, False),
    ('DRY CLEANING PICKUP', 'Services', (15, 40), False, False),
    ('PET VET VISIT', 'Services', (50, 250), False, False),
    ('YOUTUBE PREMIUM', 'Monthly Subscriptions', (12, 14), False, False),
    ('ICLOUD STORAGE', 'Monthly Subscriptions', (3, 10), False, False),
    ('GYM MEMBERSHIP', 'Monthly Subscriptions', (25, 60), False, False),
    ('AMAZON PRIME YEARLY', 'Yearly Subscriptions', (139, 139), False, False),
    ('COSTCO MEMBERSHIP', 'Yearly Subscriptions', (60, 120), False, False),

    # Cash — Cash Withdrawals
    ('ATM WITHDRAWAL', 'Cash Withdrawals', (20, 200), False, False),

    # Income — Income, Other Income
    ('EMPLOYER DIRECT DEP', 'Income', (2000, 4500), True, False),
    ('PARENT GIFT TRANSFER', 'Other Income', (50, 500), True, False),
    ('FRIEND REPAYMENT VENMO', 'Other Income', (10, 150), True, False),
    ('SUBLESSEE RENT DEPOSIT', 'Other Income', (400, 900), True, False),
    ('FREELANCE PAYMENT', 'Other Income', (200, 1500), True, True),

    # Transfers (empty in baskets but keep a couple)
    ('TRANSFER TO SAVINGS', 'Transfers', (100, 800), False, False),
    ('TRANSFER FROM CHECKING', 'Transfers', (50, 500), True, False),

    # Savings — Roth IRA, HYSA, E-Fund, General Investing, Student Loans (as savings)
    ('VANGUARD ROTH IRA', 'Roth IRA', (200, 500), False, False),
    ('FIDELITY ROTH CONTRIB', 'Roth IRA', (100, 500), False, False),
    ('HYSA DEPOSIT MARCUS', 'HYSA', (100, 600), False, False),
    ('ALLY HYSA TRANSFER', 'HYSA', (50, 400), False, False),
    ('EMERGENCY FUND DEPOSIT', 'E-Fund', (50, 300), False, False),
    ('WEALTHFRONT INVEST', 'General Investing', (100, 500), False, False),
    ('ROBINHOOD DEPOSIT', 'General Investing', (50, 300), False, False),
    ('STUDENT LOAN PMT NAVIENT', 'Student Loans', (150, 400), False, False),

    # Loans — Auto Loan, Student Loans (as loan)
    ('AUTO LOAN PMT CHASE', 'Auto Loan', (250, 450), False, False),
    ('AUTO LOAN PMT ALLY', 'Auto Loan', (200, 400), False, False),
    ('STUDENT LOAN PMT FEDLOAN', 'Student Loans', (150, 350), False, False),
]

# Weight distribution — more grocery/dining, fewer big purchases
WEIGHTS = [
    12, 10, 6, 6, 5,        # Groceries
    8, 6, 5, 7,              # Dining
    2, 1,                    # Housing
    2, 1,                    # Internet
    1, 1,                    # Water
    2, 1,                    # Electric
    5, 4, 3, 2,              # Transportation
    3, 2, 2,                 # Gas
    8, 5, 3,                 # Shopping
    2, 1,                    # Electronics
    2, 2, 1, 3,              # Entertainment
    3, 2, 1,                 # Gaming
    3, 1, 1,                 # Healthcare
    1, 1,                    # Insurance
    2, 1, 1,                 # Services
    2, 1, 2,                 # Monthly Subscriptions
    1, 1,                    # Yearly Subscriptions
    2,                       # Cash Withdrawals
    3, 2, 3, 1, 1,          # Income
    2, 1,                    # Transfers
    1, 1,                    # Roth IRA
    2, 1,                    # HYSA
    1,                       # E-Fund
    1, 1,                    # General Investing
    2,                       # Student Loans (savings bucket)
    1, 1,                    # Auto Loan
    1,                       # Student Loans (loan bucket)
]

START = date(2023, 1, 1)
END = date(2026, 12, 31)
DAYS = (END - START).days

# Build a lookup: category -> list of matching templates
CAT_TO_TEMPLATES = {}
for tmpl_entry in TEMPLATES:
    cat = tmpl_entry[1]
    CAT_TO_TEMPLATES.setdefault(cat, []).append(tmpl_entry)

# All unique categories
ALL_CATEGORIES = list(CAT_TO_TEMPLATES.keys())

def make_row(tmpl_entry, d):
    tmpl, cat, (lo, hi), is_income, tax = tmpl_entry
    desc = tmpl.replace('{n}', str(random.randint(100, 9999)))
    amount = round(random.uniform(lo, hi), 2)
    if not is_income:
        amount = -amount
    return {
        'Date': d.isoformat(),
        'Description': desc,
        'Amount': amount,
        'Category': cat,
        'Source': random.choice(SOURCES),
        'Normalized_Merchant': desc.split('#')[0].strip().rstrip('*'),
        'Tax_Deductible': tax,
        'Split_ID': '',
        'Budget_Date': d.isoformat(),
    }

rows = []

# Step 1: guarantee at least one transaction per category per month
cur = START.replace(day=1)
while cur <= END:
    # Last day of this month
    next_month = (cur.replace(day=28) + timedelta(days=4)).replace(day=1)
    month_end = next_month - timedelta(days=1)

    for cat in ALL_CATEGORIES:
        tmpl_entry = random.choice(CAT_TO_TEMPLATES[cat])
        d = cur + timedelta(days=random.randint(0, (month_end - cur).days))
        rows.append(make_row(tmpl_entry, d))

    cur = next_month

# Step 2: fill remaining rows randomly to reach 3300
while len(rows) < 3300:
    tmpl_entry = random.choices(TEMPLATES, weights=WEIGHTS, k=1)[0]
    d = START + timedelta(days=random.randint(0, DAYS))
    rows.append(make_row(tmpl_entry, d))

rows.sort(key=lambda r: r['Date'])

with open('dummy_transactions.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=[
        'Date', 'Description', 'Amount', 'Category', 'Source',
        'Normalized_Merchant', 'Tax_Deductible', 'Split_ID', 'Budget_Date',
    ])
    w.writeheader()
    w.writerows(rows)

print(f"Wrote {len(rows)} rows to dummy_transactions.csv")

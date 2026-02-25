#!/usr/bin/env python3
"""
Advanced Budget Tracker with Smart Features
- Recurring transaction detection
- Budget alerts & forecasting
- Merchant normalization
- Split transactions
- YoY comparison
- Savings rate tracking
- Cash flow projection
- Tax tagging
"""
import pdfplumber
import pandas as pd
import re
import json
from datetime import datetime, timedelta
from pathlib import Path

# File paths
TRANSACTION_DB = 'transaction_database.csv'
CATEGORY_RULES = 'category_rules.json'
MERCHANT_MAP = 'merchant_normalization.json'
RECURRING_DB = 'recurring_transactions.json'
SPLIT_TRANSACTIONS = 'split_transactions.json'
TAX_CATEGORIES = 'tax_deductible.json'

# Default categories
DEFAULT_CATEGORIES = {
    'Groceries': ['grocery', 'supermarket', 'whole foods', 'trader joe', 'safeway', 'kroger', 
                  'walmart', 'target', 'costco', 'publix', 'albertsons', 'h mart', 'hmart',
                  'aldi', 'wegmans', 'food lion', 'giant', 'shoprite', 'stop shop'],
    'Dining': ['restaurant', 'cafe', 'coffee', 'starbucks', 'chipotle', 'mcdonald', 'pizza', 
               'burger', 'taco', 'doordash', 'ubereats', 'grubhub', 'seamless'],
    'Transportation': ['uber', 'lyft', 'gas', 'fuel', 'parking', 'transit', 'metro', 'train', 
                       'bus', 'shell', 'chevron', 'exxon', 'bp', 'sunoco'],
    'Utilities': ['electric', 'gas company', 'water', 'internet', 'phone', 'verizon', 'at&t', 
                  'comcast', 'tmobile', 'sprint', 'xfinity'],
    'Entertainment': ['netflix', 'spotify', 'hulu', 'disney', 'hbo', 'amazon prime', 'movie', 
                      'theater', 'cinema', 'gym', 'fitness', 'youtube', 'apple music'],
    'Shopping': ['amazon', 'ebay', 'etsy', 'nordstrom', 'macy', 'best buy', 'apple store', 
                 'home depot', 'lowes'],
    'Healthcare': ['pharmacy', 'cvs', 'walgreens', 'doctor', 'medical', 'hospital', 'health', 
                   'dental', 'vision', 'urgent care'],
    'Insurance': ['insurance', 'geico', 'state farm', 'allstate', 'progressive'],
    'Housing': ['rent', 'mortgage', 'landlord', 'property management', 'apartment'],
    'Income': ['deposit', 'payroll', 'salary', 'direct dep', 'payment received', 'refund']
}

# Common merchant patterns for normalization
MERCHANT_PATTERNS = {
    r'AMZN MKTP.*': 'Amazon',
    r'AMAZON\.COM.*': 'Amazon',
    r'AMZ\*.*': 'Amazon',
    r'SQ \*(.+?)(?:\s+#|\s+\d{3})': r'\1',  # Square payments
    r'TST\* ?(.+?)(?:\s+#|\s+\d{3})': r'\1',  # Toast POS
    r'UBER.*TRIP': 'Uber',
    r'UBER.*EATS': 'Uber Eats',
    r'LYFT.*': 'Lyft',
    r'DOORDASH.*': 'DoorDash',
    r'GRUBHUB.*': 'GrubHub',
    r'SPOTIFY.*': 'Spotify',
    r'NETFLIX.*': 'Netflix',
    r'HULU.*': 'Hulu',
    r'TRADER JOE.*': "Trader Joe's",
    r'WHOLE FOODS.*': 'Whole Foods',
    r'STARBUCKS.*': 'Starbucks',
    r'COSTCO.*': 'Costco',
}

class AdvancedBudgetTracker:
    def __init__(self):
        self.category_rules = self.load_category_rules()
        self.merchant_map = self.load_merchant_map()
        self.transaction_db = self.load_transaction_db()
        self.recurring_db = self.load_recurring_db()
        self.split_transactions = self.load_split_transactions()
        self.tax_categories = self.load_tax_categories()
        
    def load_category_rules(self):
        if Path(CATEGORY_RULES).exists():
            with open(CATEGORY_RULES, 'r') as f:
                return json.load(f)
        return DEFAULT_CATEGORIES.copy()
    
    def save_category_rules(self):
        with open(CATEGORY_RULES, 'w') as f:
            json.dump(self.category_rules, f, indent=2)
    
    def load_merchant_map(self):
        if Path(MERCHANT_MAP).exists():
            with open(MERCHANT_MAP, 'r') as f:
                return json.load(f)
        return {}
    
    def save_merchant_map(self):
        with open(MERCHANT_MAP, 'w') as f:
            json.dump(self.merchant_map, f, indent=2)
    
    def load_recurring_db(self):
        if Path(RECURRING_DB).exists():
            with open(RECURRING_DB, 'r') as f:
                return json.load(f)
        return {}
    
    def save_recurring_db(self):
        with open(RECURRING_DB, 'w') as f:
            json.dump(self.recurring_db, f, indent=2)
    
    def load_split_transactions(self):
        if Path(SPLIT_TRANSACTIONS).exists():
            with open(SPLIT_TRANSACTIONS, 'r') as f:
                return json.load(f)
        return {}
    
    def save_split_transactions(self):
        with open(SPLIT_TRANSACTIONS, 'w') as f:
            json.dump(self.split_transactions, f, indent=2)
    
    def load_tax_categories(self):
        if Path(TAX_CATEGORIES).exists():
            with open(TAX_CATEGORIES, 'r') as f:
                return json.load(f)
        return {}
    
    def save_tax_categories(self):
        with open(TAX_CATEGORIES, 'w') as f:
            json.dump(self.tax_categories, f, indent=2)
    
    def load_transaction_db(self):
        if Path(TRANSACTION_DB).exists():
            df = pd.read_csv(TRANSACTION_DB, parse_dates=['Date'])
            return df
        return pd.DataFrame(columns=['Date', 'Description', 'Amount', 'Category', 'Source', 
                                     'Normalized_Merchant', 'Tax_Deductible', 'Split_ID'])
    
    def save_transaction_db(self):
        self.transaction_db.to_csv(TRANSACTION_DB, index=False)
    
    def normalize_merchant(self, description):
        """Clean up merchant names using patterns"""
        # Check custom mappings first
        desc_lower = description.lower()
        for key, value in self.merchant_map.items():
            if key.lower() in desc_lower:
                return value
        
        # Apply regex patterns
        for pattern, replacement in MERCHANT_PATTERNS.items():
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                if isinstance(replacement, str) and '\\1' in replacement:
                    return re.sub(pattern, replacement, description, flags=re.IGNORECASE).strip()
                return replacement
        
        # Clean up common junk
        cleaned = description
        cleaned = re.sub(r'\s+#\d+.*$', '', cleaned)  # Remove store numbers
        cleaned = re.sub(r'\s+\d{3,}.*$', '', cleaned)  # Remove trailing numbers
        cleaned = re.sub(r'\s{2,}', ' ', cleaned)  # Remove extra spaces
        return cleaned.strip()
    
    def categorize_transaction(self, description, amount):
        """Categorize with normalization"""
        normalized = self.normalize_merchant(description)
        description_lower = normalized.lower()
        
        if amount > 0:
            for keyword in self.category_rules.get('Income', []):
                if keyword.lower() in description_lower:
                    return 'Income', normalized
            return 'Other Income', normalized
        
        for category, keywords in self.category_rules.items():
            if category in ['Income', 'Other Income']:
                continue
            for keyword in keywords:
                if keyword.lower() in description_lower:
                    return category, normalized
        
        return 'UNCATEGORIZED', normalized
    
    def detect_recurring_transactions(self):
        """Detect recurring transactions (subscriptions, rent, etc.)"""
        if self.transaction_db.empty:
            return {}
        
        df = self.transaction_db.copy()
        df['Month'] = df['Date'].dt.to_period('M')
        df['Amount_Rounded'] = df['Amount'].round(2)
        
        # Group by normalized merchant and rounded amount
        recurring = {}
        
        for merchant in df['Normalized_Merchant'].unique():
            merchant_txns = df[df['Normalized_Merchant'] == merchant]
            
            for amount in merchant_txns['Amount_Rounded'].unique():
                amount_txns = merchant_txns[merchant_txns['Amount_Rounded'] == amount]
                
                # Check if appears in 3+ consecutive months
                months = amount_txns['Month'].unique()
                if len(months) >= 3:
                    months_sorted = sorted(months)
                    consecutive = 1
                    max_consecutive = 1
                    
                    for i in range(1, len(months_sorted)):
                        if (months_sorted[i].to_timestamp() - 
                            months_sorted[i-1].to_timestamp()).days <= 35:
                            consecutive += 1
                            max_consecutive = max(max_consecutive, consecutive)
                        else:
                            consecutive = 1
                    
                    if max_consecutive >= 3:
                        key = f"{merchant}|{amount}"
                        recurring[key] = {
                            'merchant': merchant,
                            'amount': float(amount),
                            'category': amount_txns.iloc[0]['Category'],
                            'frequency': 'monthly',
                            'occurrences': len(months),
                            'last_seen': amount_txns['Date'].max().strftime('%Y-%m-%d'),
                            'avg_day_of_month': int(amount_txns['Date'].dt.day.mean())
                        }
        
        self.recurring_db = recurring
        self.save_recurring_db()
        return recurring
    
    def check_missing_recurring(self, current_date=None):
        """Check if any recurring transactions are missing"""
        if not self.recurring_db:
            return []
        
        if current_date is None:
            current_date = datetime.now()
        
        current_month = pd.Period(current_date, freq='M')
        missing = []
        
        for key, recurring in self.recurring_db.items():
            last_seen = pd.to_datetime(recurring['last_seen'])
            last_month = pd.Period(last_seen, freq='M')
            
            # If last seen was before current month and it's past expected day
            if last_month < current_month:
                expected_day = recurring['avg_day_of_month']
                if current_date.day >= expected_day:
                    missing.append({
                        'merchant': recurring['merchant'],
                        'amount': recurring['amount'],
                        'expected_date': f"{current_date.year}-{current_date.month:02d}-{expected_day:02d}",
                        'category': recurring['category']
                    })
        
        return missing
    
    def calculate_savings_rate(self, month=None):
        """Calculate savings rate: (Income - Expenses) / Income"""
        if self.transaction_db.empty:
            return None
        
        df = self.transaction_db.copy()
        
        if month:
            df = df[df['Date'].dt.to_period('M') == pd.Period(month)]
        
        income = df[df['Amount'] > 0]['Amount'].sum()
        expenses = abs(df[df['Amount'] < 0]['Amount'].sum())
        
        if income == 0:
            return 0
        
        savings = income - expenses
        return (savings / income) * 100
    
    def project_cash_flow(self, months=3):
        """Project cash flow for next N months based on recurring transactions"""
        if not self.recurring_db:
            self.detect_recurring_transactions()
        
        projections = []
        current_date = datetime.now()
        
        for i in range(months):
            month_date = current_date + timedelta(days=30*i)
            month_str = month_date.strftime('%Y-%m')
            
            projected_income = 0
            projected_expenses = 0
            
            for recurring in self.recurring_db.values():
                amount = recurring['amount']
                if amount > 0:
                    projected_income += amount
                else:
                    projected_expenses += abs(amount)
            
            projections.append({
                'month': month_str,
                'projected_income': projected_income,
                'projected_expenses': projected_expenses,
                'projected_net': projected_income - projected_expenses
            })
        
        return projections
    
    def calculate_yoy_comparison(self):
        """Compare spending year-over-year"""
        if self.transaction_db.empty:
            return {}
        
        df = self.transaction_db.copy()
        df['Year'] = df['Date'].dt.year
        df['Month'] = df['Date'].dt.month
        
        years = df['Year'].unique()
        if len(years) < 2:
            return {}
        
        comparisons = {}
        
        for category in df['Category'].unique():
            if category in ['Income', 'Other Income']:
                continue
            
            cat_data = df[df['Category'] == category]
            yearly_totals = cat_data.groupby('Year')['Amount'].sum().abs()
            
            if len(yearly_totals) >= 2:
                years_sorted = sorted(yearly_totals.index)
                prev_year = years_sorted[-2]
                curr_year = years_sorted[-1]
                
                prev_total = yearly_totals[prev_year]
                curr_total = yearly_totals[curr_year]
                
                if prev_total > 0:
                    pct_change = ((curr_total - prev_total) / prev_total) * 100
                    comparisons[category] = {
                        'prev_year': int(prev_year),
                        'curr_year': int(curr_year),
                        'prev_total': float(prev_total),
                        'curr_total': float(curr_total),
                        'pct_change': float(pct_change)
                    }
        
        return comparisons
    
    def budget_forecast_alert(self, budgets, current_date=None):
        """Alert if on track to exceed budget based on current spending rate"""
        if self.transaction_db.empty or not budgets:
            return []
        
        if current_date is None:
            current_date = datetime.now()
        
        current_month = pd.Period(current_date, freq='M')
        df = self.transaction_db[self.transaction_db['Date'].dt.to_period('M') == current_month]
        
        days_in_month = current_month.days_in_month
        day_of_month = current_date.day
        days_remaining = days_in_month - day_of_month
        
        alerts = []
        
        for category, budget_amount in budgets.items():
            cat_spending = abs(df[df['Category'] == category]['Amount'].sum())
            
            if day_of_month > 0:
                daily_rate = cat_spending / day_of_month
                projected_total = cat_spending + (daily_rate * days_remaining)
                
                if projected_total > budget_amount:
                    overage = projected_total - budget_amount
                    alerts.append({
                        'category': category,
                        'budget': budget_amount,
                        'spent_so_far': cat_spending,
                        'projected_total': projected_total,
                        'projected_overage': overage,
                        'days_remaining': days_remaining
                    })
        
        return alerts
    
    def split_transaction(self, transaction_id, splits):
        """Split a transaction into multiple categories
        
        splits = [
            {'category': 'Groceries', 'amount': 100, 'tax_deductible': False},
            {'category': 'Shopping', 'amount': 50, 'tax_deductible': False}
        ]
        """
        split_id = f"split_{transaction_id}"
        self.split_transactions[split_id] = splits
        self.save_split_transactions()
        
        # Update transaction with split marker
        self.transaction_db.loc[self.transaction_db.index == transaction_id, 'Split_ID'] = split_id
        self.save_transaction_db()
        
        return split_id
    
    def tag_tax_deductible(self, transaction_id, is_deductible=True, notes=""):
        """Mark transaction as tax deductible"""
        self.tax_categories[str(transaction_id)] = {
            'deductible': is_deductible,
            'notes': notes,
            'date': datetime.now().strftime('%Y-%m-%d')
        }
        self.save_tax_categories()
        
        self.transaction_db.loc[self.transaction_db.index == transaction_id, 'Tax_Deductible'] = is_deductible
        self.save_transaction_db()
    
    def extract_transactions_from_pdf(self, pdf_path, source_name):
        """Extract transactions with normalization"""
        transactions = []
        current_year = datetime.now().year

        with pdfplumber.open(pdf_path) as pdf:
            # Try to detect the statement year from any 4-digit year in the PDF
            statement_year = None
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                year_match = re.search(r'\b(20\d{2})\b', text)
                if year_match:
                    statement_year = int(year_match.group(1))
                    break
            if statement_year is None:
                statement_year = current_year

            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue

                patterns = [
                    # MM/DD/YYYY or MM/DD/YY with description and amount
                    r'(\d{1,2}/\d{1,2}/\d{2,4})\s+(.+?)\s+([-]?\$?[\d,]+\.\d{2})',
                    # MM/DD (no year) with description and amount
                    r'(\d{1,2}/\d{1,2})\s+(.+?)\s+([-]?\$?[\d,]+\.\d{2})',
                    # YYYY-MM-DD with description and amount
                    r'(\d{4}-\d{2}-\d{2})\s+(.+?)\s+([-]?\$?[\d,]+\.\d{2})',
                    # Trans date + post date + description + amount (credit cards)
                    r'(\d{2}/\d{2})\s+(\d{2}/\d{2})\s+(.+?)\s+([-]?\$?[\d,]+\.\d{2})',
                ]

                for pattern in patterns:
                    matches = re.finditer(pattern, text, re.MULTILINE)
                    for match in matches:
                        groups = match.groups()
                        if len(groups) == 3:
                            date_str, description, amount_str = groups
                        elif len(groups) == 4:
                            _, date_str, description, amount_str = groups
                        else:
                            continue

                        description = description.strip()
                        amount_str = amount_str.replace('$', '').replace(',', '')

                        try:
                            amount = float(amount_str)
                        except ValueError:
                            continue

                        if len(description) < 3:
                            continue

                        try:
                            if '/' in date_str:
                                parts = date_str.split('/')
                                if len(parts) == 2:
                                    # MM/DD — use statement year
                                    date = datetime.strptime(
                                        f"{date_str}/{statement_year}", '%m/%d/%Y'
                                    )
                                elif len(parts[2]) == 2:
                                    date = datetime.strptime(date_str, '%m/%d/%y')
                                else:
                                    date = datetime.strptime(date_str, '%m/%d/%Y')
                            else:
                                date = datetime.strptime(date_str, '%Y-%m-%d')
                        except ValueError:
                            continue

                        category, normalized_merchant = self.categorize_transaction(
                            description, amount
                        )

                        transactions.append({
                            'Date': date,
                            'Description': description,
                            'Amount': amount,
                            'Category': category,
                            'Source': source_name,
                            'Normalized_Merchant': normalized_merchant,
                            'Tax_Deductible': False,
                            'Split_ID': None
                        })

        return transactions

    # ------------------------------------------------------------------ #
    #  CSV import — one parser per bank, auto-detected from headers        #
    # ------------------------------------------------------------------ #

    def _detect_csv_bank(self, headers):
        """Return bank identifier from CSV header names."""
        h = set(h.strip().lower() for h in headers)
        if 'transaction description' in h and 'balance' in h:
            return 'pnc'
        if 'card no.' in h and 'debit' in h and 'credit' in h:
            return 'capital_one'
        if 'member name' in h and 'status' in h:
            return 'citi'
        if 'trans. date' in h or ('post date' in h and 'amount' in h):
            return 'discover'
        return 'unknown'

    def _parse_pnc_amount(self, amount_str):
        """Convert '+ $10' / '- $8.84' to signed float."""
        s = amount_str.replace('$', '').replace(',', '').strip()
        if s.startswith('+'):
            return float(s[1:].strip())
        if s.startswith('-'):
            return -float(s[1:].strip())
        return float(s)

    def _should_skip_pnc(self, row):
        """Return True if this PNC row should be filtered out."""
        date_str = str(row.get('Transaction Date', '')).strip()
        desc = str(row.get('Transaction Description', '')).upper()
        cat = str(row.get('Category', '')).strip()

        # Skip pending rows
        if date_str.upper().startswith('PENDING'):
            return True
        # Skip credit card payments
        if cat == 'Credit Card Payments':
            return True
        # Skip internal account transfers (ONLINE TRANSFER TO/FROM XXXXX...)
        if re.match(r'ONLINE TRANSFER (TO|FROM) XXXXX', desc):
            return True
        return False

    def _should_skip_capital_one(self, row):
        """Return True if this Capital One row should be filtered out."""
        desc = str(row.get('Description', '')).upper()
        # Skip own payment credits (these are reflected in PNC already)
        if re.search(r'CAPITAL ONE (ONLINE|MOBILE) PYMT', desc):
            return True
        return False

    def _should_skip_discover(self, row):
        """Return True if this Discover row should be filtered out."""
        cat = str(row.get('Category', '')).strip()
        desc = str(row.get('Description', '')).upper()
        # Skip payment credits
        if cat == 'Payments and Credits':
            return True
        if 'INTERNET PAYMENT' in desc:
            return True
        return False

    def _should_skip_citi(self, row):
        """Return True if this Citi row should be filtered out."""
        desc = str(row.get('Description', '')).upper()
        credit = str(row.get('Credit', '')).strip()
        # Skip payment credits (positive credit entries = payment to card)
        if credit:
            return True
        if 'ONLINE PAYMENT' in desc:
            return True
        return False

    def extract_transactions_from_csv(self, csv_path, source_name):
        """Parse a bank CSV export and return transaction dicts."""
        transactions = []
        df = pd.read_csv(csv_path, dtype=str).fillna('')
        bank = self._detect_csv_bank(df.columns.tolist())

        for _, row in df.iterrows():
            try:
                if bank == 'pnc':
                    if self._should_skip_pnc(row):
                        continue
                    date_str = str(row['Transaction Date']).strip()
                    # Try YYYY-MM-DD first, then other formats
                    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y'):
                        try:
                            date = datetime.strptime(date_str, fmt)
                            break
                        except ValueError:
                            continue
                    else:
                        continue
                    description = str(row['Transaction Description']).strip()
                    amount = self._parse_pnc_amount(str(row['Amount']))

                elif bank == 'capital_one':
                    if self._should_skip_capital_one(row):
                        continue
                    date_str = str(row['Transaction Date']).strip()
                    date = datetime.strptime(date_str, '%Y-%m-%d')
                    description = str(row['Description']).strip()
                    debit = str(row.get('Debit', '')).strip()
                    credit = str(row.get('Credit', '')).strip()
                    if debit:
                        amount = -float(debit.replace(',', ''))
                    elif credit:
                        amount = float(credit.replace(',', ''))
                    else:
                        continue

                elif bank == 'discover':
                    if self._should_skip_discover(row):
                        continue
                    date_str = str(row['Trans. Date']).strip()
                    for fmt in ('%m/%d/%Y', '%Y-%m-%d'):
                        try:
                            date = datetime.strptime(date_str, fmt)
                            break
                        except ValueError:
                            continue
                    else:
                        continue
                    description = str(row['Description']).strip()
                    amount_str = str(row['Amount']).replace(',', '').strip()
                    amount = float(amount_str)
                    # Discover: negative = spending (already correct sign)

                elif bank == 'citi':
                    if self._should_skip_citi(row):
                        continue
                    date_str = str(row['Date']).strip()
                    for fmt in ('%m/%d/%Y', '%Y-%m-%d'):
                        try:
                            date = datetime.strptime(date_str, fmt)
                            break
                        except ValueError:
                            continue
                    else:
                        continue
                    description = str(row['Description']).strip()
                    debit = str(row.get('Debit', '')).strip()
                    if debit:
                        amount = -float(debit.replace(',', ''))
                    else:
                        continue  # no debit and payment already filtered

                else:
                    continue  # Unknown format

                if len(description) < 2:
                    continue

                category, normalized_merchant = self.categorize_transaction(
                    description, amount
                )
                transactions.append({
                    'Date': date,
                    'Description': description,
                    'Amount': amount,
                    'Category': category,
                    'Source': source_name,
                    'Normalized_Merchant': normalized_merchant,
                    'Tax_Deductible': False,
                    'Split_ID': None,
                })

            except (ValueError, KeyError):
                continue

        return transactions, bank

    def add_transactions(self, new_transactions, source_name):
        """Add transactions with enhanced deduplication"""
        new_df = pd.DataFrame(new_transactions)
        
        if new_df.empty:
            return {'added': 0, 'duplicates': 0, 'details': []}
        
        duplicates_found = []
        
        if not self.transaction_db.empty:
            # Method 1: Exact match (Date + Description + Amount)
            merged = pd.concat([self.transaction_db, new_df])
            before_count = len(merged)
            
            # Mark duplicates before removing
            duplicate_mask = merged.duplicated(subset=['Date', 'Description', 'Amount'], keep='first')
            duplicates = merged[duplicate_mask]
            
            for _, dup in duplicates.iterrows():
                duplicates_found.append({
                    'date': dup['Date'].strftime('%Y-%m-%d'),
                    'description': dup['Description'],
                    'amount': float(dup['Amount']),
                    'source': dup['Source'],
                    'reason': 'exact_match'
                })
            
            merged = merged.drop_duplicates(subset=['Date', 'Description', 'Amount'], keep='first')
            
            # Method 2: Fuzzy duplicates (same date, amount, similar description)
            # This catches cases like:
            # "AMAZON MKTP US" vs "AMAZON.COM" on same day, same amount
            new_transactions_after_exact = merged[merged['Source'] == source_name]
            
            for idx, new_txn in new_transactions_after_exact.iterrows():
                existing = merged[(merged['Date'] == new_txn['Date']) & 
                                 (merged['Amount'] == new_txn['Amount']) &
                                 (merged['Source'] != source_name)]
                
                if not existing.empty:
                    # Check if normalized merchants match
                    for _, exist_txn in existing.iterrows():
                        if new_txn['Normalized_Merchant'].lower() == exist_txn['Normalized_Merchant'].lower():
                            duplicates_found.append({
                                'date': new_txn['Date'].strftime('%Y-%m-%d'),
                                'description': new_txn['Description'],
                                'amount': float(new_txn['Amount']),
                                'source': new_txn['Source'],
                                'reason': 'same_merchant_date_amount',
                                'matched_with': exist_txn['Description']
                            })
                            merged = merged.drop(idx)
                            break
            
            self.transaction_db = merged.reset_index(drop=True)
            new_count = len(new_df) - len(duplicates_found)
        else:
            self.transaction_db = new_df
            new_count = len(new_df)
        
        self.save_transaction_db()
        
        return {
            'added': new_count,
            'duplicates': len(duplicates_found),
            'details': duplicates_found
        }
    
    def learn_category(self, keyword, category):
        """Add keyword to category"""
        if category not in self.category_rules:
            self.category_rules[category] = []
        
        keyword_lower = keyword.lower()
        if keyword_lower not in [k.lower() for k in self.category_rules[category]]:
            self.category_rules[category].append(keyword_lower)
            self.save_category_rules()
            return True
        return False
    
    def learn_merchant_normalization(self, raw_name, normalized_name):
        """Teach merchant normalization"""
        self.merchant_map[raw_name.lower()] = normalized_name
        self.save_merchant_map()
    
    def recategorize_all(self):
        """Re-run categorization on all transactions"""
        if self.transaction_db.empty:
            return
        
        for idx, row in self.transaction_db.iterrows():
            category, normalized = self.categorize_transaction(row['Description'], row['Amount'])
            self.transaction_db.at[idx, 'Category'] = category
            self.transaction_db.at[idx, 'Normalized_Merchant'] = normalized
        
        self.save_transaction_db()
    
    def get_insights(self):
        """Generate comprehensive insights"""
        insights = {
            'recurring_transactions': self.detect_recurring_transactions(),
            'missing_recurring': self.check_missing_recurring(),
            'savings_rate_current': self.calculate_savings_rate(),
            'yoy_comparison': self.calculate_yoy_comparison(),
            'cash_flow_projection': self.project_cash_flow(3)
        }
        return insights

def main():
    import sys
    
    tracker = AdvancedBudgetTracker()
    
    if len(sys.argv) < 2:
        print("\n=== Advanced Budget Tracker ===\n")
        print("Commands:")
        print("  add <pdf> <source>          - Add transactions")
        print("  learn <keyword> <category>  - Learn categorization")
        print("  normalize <raw> <clean>     - Learn merchant name")
        print("  recategorize                - Re-run all categorization")
        print("  insights                    - Show AI insights")
        print("  split <id> <cat:amt,cat:amt> - Split transaction")
        print("  tax <id> [notes]            - Mark tax deductible")
        print("  dashboard                   - Launch web dashboard\n")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'add':
        if len(sys.argv) < 4:
            print("Usage: python advanced_tracker.py add <pdf> <source>")
            return
        
        pdf_file = sys.argv[2]
        source_name = sys.argv[3]
        
        print(f"\nProcessing: {pdf_file} ({source_name})")
        transactions = tracker.extract_transactions_from_pdf(pdf_file, source_name)
        result = tracker.add_transactions(transactions, source_name)
        
        print(f"\n✓ Added {result['added']} new transactions")
        
        if result['duplicates'] > 0:
            print(f"⚠️  Skipped {result['duplicates']} duplicates:")
            for dup in result['details'][:5]:  # Show first 5
                reason = "Exact match" if dup['reason'] == 'exact_match' else "Same merchant/date/amount"
                print(f"   - {dup['date']}: {dup['description'][:50]} ${dup['amount']:.2f} ({reason})")
            if len(result['details']) > 5:
                print(f"   ... and {len(result['details']) - 5} more")
        
        
    elif command == 'learn':
        keyword = sys.argv[2]
        category = sys.argv[3]
        tracker.learn_category(keyword, category)
        print(f"✓ Learned: '{keyword}' → {category}")
        
    elif command == 'normalize':
        raw = sys.argv[2]
        clean = sys.argv[3]
        tracker.learn_merchant_normalization(raw, clean)
        print(f"✓ Normalized: '{raw}' → '{clean}'")
        
    elif command == 'recategorize':
        tracker.recategorize_all()
        print("✓ Recategorized all transactions")
        
    elif command == 'insights':
        insights = tracker.get_insights()
        print("\n=== INSIGHTS ===\n")
        print(f"💰 Current Savings Rate: {insights['savings_rate_current']:.1f}%\n")
        
        if insights['recurring_transactions']:
            print(f"🔄 Detected {len(insights['recurring_transactions'])} recurring transactions")
        
        if insights['missing_recurring']:
            print(f"\n⚠️  {len(insights['missing_recurring'])} recurring transactions missing:")
            for missing in insights['missing_recurring']:
                print(f"   - {missing['merchant']}: ${missing['amount']:.2f} ({missing['category']})")
        
        if insights['yoy_comparison']:
            print("\n📊 Year-over-Year Changes:")
            for cat, data in insights['yoy_comparison'].items():
                sign = "📈" if data['pct_change'] > 0 else "📉"
                print(f"   {sign} {cat}: {data['pct_change']:+.1f}% vs last year")
        
        print("\n💵 Cash Flow Projection (next 3 months):")
        for proj in insights['cash_flow_projection']:
            print(f"   {proj['month']}: ${proj['projected_net']:,.2f}")
        
    elif command == 'dashboard':
        print("\n🚀 Launching Streamlit dashboard...")
        print("Run: streamlit run dashboard.py")
        print("(Dashboard file will be created separately)")

if __name__ == "__main__":
    main()

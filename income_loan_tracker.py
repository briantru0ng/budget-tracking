#!/usr/bin/env python3
"""
Income & Loan Tracking Module
- Multiple income stream categorization
- Loan payment tracking
- Payoff timeline projection
- Interest calculations
"""
import pandas as pd
import json
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np

INCOME_STREAMS = 'income_streams.json'
LOANS_DB = 'loans.json'
LOAN_PAYMENTS = 'loan_payments.json'

# Income categories with keywords
INCOME_CATEGORIES = {
    'Salary': ['payroll', 'direct dep salary', 'paychex', 'adp', 'employer'],
    'Side_Income': ['freelance', 'upwork', 'fiverr', 'consulting', 'contract'],
    'Investments': ['dividend', 'interest', 'capital gain', 'schwab', 'fidelity', 'vanguard'],
    'Gifts': ['venmo', 'zelle', 'cash app', 'paypal', 'gift', 'mom', 'dad', 'parent'],
    'Refunds': ['refund', 'reimbursement', 'return'],
    'Government': ['tax refund', 'stimulus', 'social security', 'unemployment'],
    'Rental': ['rent payment', 'rental income'],
    'Business': ['stripe', 'square', 'business revenue', 'sales']
}

class IncomeAndLoanTracker:
    def __init__(self, tracker):
        """Initialize with main budget tracker"""
        self.tracker = tracker
        self.income_streams = self.load_income_streams()
        self.loans = self.load_loans()
        self.loan_payments = self.load_loan_payments()
    
    def load_income_streams(self):
        if Path(INCOME_STREAMS).exists():
            with open(INCOME_STREAMS, 'r') as f:
                return json.load(f)
        return INCOME_CATEGORIES.copy()
    
    def save_income_streams(self):
        with open(INCOME_STREAMS, 'w') as f:
            json.dump(self.income_streams, f, indent=2)
    
    def load_loans(self):
        if Path(LOANS_DB).exists():
            with open(LOANS_DB, 'r') as f:
                return json.load(f)
        return {}
    
    def save_loans(self):
        with open(LOANS_DB, 'w') as f:
            json.dump(self.loans, f, indent=2)
    
    def load_loan_payments(self):
        if Path(LOAN_PAYMENTS).exists():
            with open(LOAN_PAYMENTS, 'r') as f:
                return json.load(f)
        return {}
    
    def save_loan_payments(self):
        with open(LOAN_PAYMENTS, 'w') as f:
            json.dump(self.loan_payments, f, indent=2)
    
    def categorize_income(self, description, amount):
        """Categorize income into specific streams"""
        if amount <= 0:
            return None
        
        description_lower = description.lower()
        
        # Check custom income streams
        for category, keywords in self.income_streams.items():
            for keyword in keywords:
                if keyword.lower() in description_lower:
                    return category
        
        return 'Other_Income'
    
    def recategorize_income(self):
        """Re-categorize all income transactions with income streams"""
        if self.tracker.transaction_db.empty:
            return
        
        income_txns = self.tracker.transaction_db[self.tracker.transaction_db['Amount'] > 0].copy()
        
        for idx, row in income_txns.iterrows():
            income_category = self.categorize_income(row['Description'], row['Amount'])
            if income_category:
                # Store in a new column
                self.tracker.transaction_db.loc[idx, 'Income_Stream'] = income_category
        
        self.tracker.save_transaction_db()
    
    def get_income_breakdown(self, start_date=None, end_date=None):
        """Get breakdown of income by stream"""
        if self.tracker.transaction_db.empty:
            return {}
        
        df = self.tracker.transaction_db[self.tracker.transaction_db['Amount'] > 0].copy()
        
        if start_date:
            df = df[df['Date'] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df['Date'] <= pd.to_datetime(end_date)]
        
        # Recategorize if needed
        if 'Income_Stream' not in df.columns:
            self.recategorize_income()
            df = self.tracker.transaction_db[self.tracker.transaction_db['Amount'] > 0].copy()
            if start_date:
                df = df[df['Date'] >= pd.to_datetime(start_date)]
            if end_date:
                df = df[df['Date'] <= pd.to_datetime(end_date)]
        
        breakdown = df.groupby('Income_Stream')['Amount'].agg(['sum', 'count', 'mean']).to_dict('index')
        
        return breakdown
    
    def add_loan(self, name, principal, interest_rate, monthly_payment, 
                 start_date, loan_type='personal', min_payment=None):
        """Add a loan to track
        
        Args:
            name: Loan name (e.g., "Student Loan", "Car Loan")
            principal: Original loan amount
            interest_rate: Annual interest rate as decimal (e.g., 0.045 for 4.5%)
            monthly_payment: Regular payment amount
            start_date: When loan started (YYYY-MM-DD)
            loan_type: Type of loan (personal, student, auto, mortgage, credit_card)
            min_payment: Minimum payment required (optional)
        """
        loan_id = name.lower().replace(' ', '_')
        
        self.loans[loan_id] = {
            'name': name,
            'principal': principal,
            'current_balance': principal,
            'interest_rate': interest_rate,
            'monthly_payment': monthly_payment,
            'min_payment': min_payment or monthly_payment,
            'start_date': start_date,
            'loan_type': loan_type,
            'total_paid': 0,
            'total_interest_paid': 0,
            'payments': []
        }
        
        self.save_loans()
        print(f"✓ Added loan: {name}")
        return loan_id
    
    def record_payment(self, loan_id, amount, date, extra_principal=0):
        """Record a payment to a loan"""
        if loan_id not in self.loans:
            print(f"Error: Loan '{loan_id}' not found")
            return
        
        loan = self.loans[loan_id]
        
        # Calculate interest for the period
        monthly_rate = loan['interest_rate'] / 12
        interest_charge = loan['current_balance'] * monthly_rate
        principal_payment = amount - interest_charge + extra_principal
        
        # Update loan
        loan['current_balance'] -= principal_payment
        loan['total_paid'] += amount
        loan['total_interest_paid'] += interest_charge
        
        # Record payment
        payment = {
            'date': date,
            'amount': amount,
            'principal': principal_payment,
            'interest': interest_charge,
            'extra_principal': extra_principal,
            'balance_after': loan['current_balance']
        }
        
        loan['payments'].append(payment)
        
        self.save_loans()
        print(f"✓ Recorded payment: ${amount:.2f} to {loan['name']}")
    
    def auto_detect_loan_payments(self, loan_id, keywords):
        """Auto-detect loan payments from transaction history"""
        if loan_id not in self.loans:
            print(f"Error: Loan '{loan_id}' not found")
            return
        
        df = self.tracker.transaction_db.copy()
        
        # Find payments matching keywords
        mask = df['Description'].str.lower().str.contains('|'.join(keywords), case=False, na=False)
        payments = df[mask & (df['Amount'] < 0)].copy()
        
        print(f"Found {len(payments)} potential payments for {self.loans[loan_id]['name']}")
        
        for _, txn in payments.iterrows():
            amount = abs(txn['Amount'])
            date = txn['Date'].strftime('%Y-%m-%d')
            
            # Check if already recorded
            existing = [p for p in self.loans[loan_id]['payments'] if p['date'] == date]
            if not existing:
                self.record_payment(loan_id, amount, date)
    
    def calculate_payoff_timeline(self, loan_id, extra_monthly=0):
        """Calculate loan payoff timeline with optional extra payments"""
        if loan_id not in self.loans:
            print(f"Error: Loan '{loan_id}' not found")
            return None
        
        loan = self.loans[loan_id]
        balance = loan['current_balance']
        monthly_rate = loan['interest_rate'] / 12
        payment = loan['monthly_payment'] + extra_monthly
        
        timeline = []
        month = 0
        total_interest = 0
        
        while balance > 0 and month < 600:  # Cap at 50 years
            interest = balance * monthly_rate
            principal = payment - interest
            
            if principal <= 0:
                return {
                    'error': 'Payment too low to cover interest!',
                    'min_payment_needed': interest * 1.1
                }
            
            if balance < payment:
                payment = balance + interest
                principal = balance
            
            balance -= principal
            total_interest += interest
            month += 1
            
            timeline.append({
                'month': month,
                'payment': payment,
                'principal': principal,
                'interest': interest,
                'balance': max(0, balance)
            })
        
        payoff_date = datetime.now() + timedelta(days=30*month)
        
        return {
            'months_to_payoff': month,
            'payoff_date': payoff_date.strftime('%Y-%m-%d'),
            'total_interest': total_interest,
            'total_paid': sum(t['payment'] for t in timeline),
            'timeline': timeline
        }
    
    def compare_payoff_strategies(self, loan_id, extra_amounts=[0, 50, 100, 200, 500]):
        """Compare different extra payment strategies"""
        if loan_id not in self.loans:
            return None
        
        comparisons = []
        
        for extra in extra_amounts:
            result = self.calculate_payoff_timeline(loan_id, extra)
            
            if result and 'error' not in result:
                comparisons.append({
                    'extra_monthly': extra,
                    'months_to_payoff': result['months_to_payoff'],
                    'payoff_date': result['payoff_date'],
                    'total_interest': result['total_interest'],
                    'total_paid': result['total_paid'],
                    'interest_saved': comparisons[0]['total_interest'] - result['total_interest'] if comparisons else 0
                })
        
        return comparisons
    
    def get_loan_summary(self):
        """Get summary of all loans"""
        if not self.loans:
            return None
        
        summary = {
            'total_debt': sum(loan['current_balance'] for loan in self.loans.values()),
            'total_monthly_payment': sum(loan['monthly_payment'] for loan in self.loans.values()),
            'total_interest_paid': sum(loan['total_interest_paid'] for loan in self.loans.values()),
            'loans': []
        }
        
        for loan_id, loan in self.loans.items():
            # Calculate payoff with current payment
            payoff = self.calculate_payoff_timeline(loan_id, 0)
            
            loan_info = {
                'name': loan['name'],
                'balance': loan['current_balance'],
                'payment': loan['monthly_payment'],
                'rate': loan['interest_rate'] * 100,
                'months_to_payoff': payoff['months_to_payoff'] if payoff and 'months_to_payoff' in payoff else None,
                'payoff_date': payoff['payoff_date'] if payoff and 'payoff_date' in payoff else None
            }
            
            summary['loans'].append(loan_info)
        
        return summary
    
    def avalanche_strategy(self):
        """Suggest debt avalanche strategy (highest interest first)"""
        if not self.loans:
            return None
        
        # Sort by interest rate descending
        sorted_loans = sorted(
            self.loans.items(),
            key=lambda x: x[1]['interest_rate'],
            reverse=True
        )
        
        strategy = []
        for loan_id, loan in sorted_loans:
            strategy.append({
                'priority': len(strategy) + 1,
                'name': loan['name'],
                'balance': loan['current_balance'],
                'rate': loan['interest_rate'] * 100,
                'min_payment': loan['min_payment'],
                'recommendation': 'Pay minimum on others, attack this one first' if len(strategy) == 0 else 'Pay minimum only'
            })
        
        return strategy
    
    def snowball_strategy(self):
        """Suggest debt snowball strategy (lowest balance first)"""
        if not self.loans:
            return None
        
        # Sort by balance ascending
        sorted_loans = sorted(
            self.loans.items(),
            key=lambda x: x[1]['current_balance']
        )
        
        strategy = []
        for loan_id, loan in sorted_loans:
            strategy.append({
                'priority': len(strategy) + 1,
                'name': loan['name'],
                'balance': loan['current_balance'],
                'rate': loan['interest_rate'] * 100,
                'min_payment': loan['min_payment'],
                'recommendation': 'Pay off first for psychological win!' if len(strategy) == 0 else 'Pay minimum only'
            })
        
        return strategy

def main():
    import sys
    from advanced_tracker import AdvancedBudgetTracker
    
    if len(sys.argv) < 2:
        print("\n=== Income & Loan Tracker ===\n")
        print("Income Commands:")
        print("  income breakdown [YYYY-MM-DD] [YYYY-MM-DD]  - Show income by stream")
        print("  income learn <keyword> <stream>             - Teach income categorization\n")
        print("Loan Commands:")
        print("  loan add <name> <principal> <rate> <payment> <date> [type]")
        print("  loan pay <loan_id> <amount> <date> [extra_principal]")
        print("  loan auto <loan_id> <keyword1,keyword2>     - Auto-detect payments")
        print("  loan timeline <loan_id> [extra_monthly]     - Show payoff timeline")
        print("  loan compare <loan_id>                      - Compare strategies")
        print("  loan summary                                - All loans summary")
        print("  loan avalanche                              - Debt avalanche strategy")
        print("  loan snowball                               - Debt snowball strategy\n")
        return
    
    tracker = AdvancedBudgetTracker()
    income_loan = IncomeAndLoanTracker(tracker)
    
    command = sys.argv[1].lower()
    
    if command == 'income':
        if len(sys.argv) < 3:
            print("Usage: income breakdown | income learn <kw> <stream>")
            return
        
        subcommand = sys.argv[2].lower()
        
        if subcommand == 'breakdown':
            start = sys.argv[3] if len(sys.argv) > 3 else None
            end = sys.argv[4] if len(sys.argv) > 4 else None
            
            breakdown = income_loan.get_income_breakdown(start, end)
            
            print("\n💰 INCOME BREAKDOWN\n")
            total = 0
            for stream, stats in sorted(breakdown.items(), key=lambda x: x[1]['sum'], reverse=True):
                print(f"{stream:20} ${stats['sum']:10,.2f}  ({stats['count']} payments, avg ${stats['mean']:.2f})")
                total += stats['sum']
            print(f"\n{'TOTAL':20} ${total:10,.2f}")
        
        elif subcommand == 'learn':
            keyword = sys.argv[3]
            stream = sys.argv[4]
            
            if stream not in income_loan.income_streams:
                income_loan.income_streams[stream] = []
            
            income_loan.income_streams[stream].append(keyword)
            income_loan.save_income_streams()
            print(f"✓ Learned: '{keyword}' → {stream}")
    
    elif command == 'loan':
        if len(sys.argv) < 3:
            print("Usage: loan <add|pay|auto|timeline|compare|summary|avalanche|snowball>")
            return
        
        subcommand = sys.argv[2].lower()
        
        if subcommand == 'add':
            name = sys.argv[3]
            principal = float(sys.argv[4])
            rate = float(sys.argv[5])
            payment = float(sys.argv[6])
            date = sys.argv[7]
            loan_type = sys.argv[8] if len(sys.argv) > 8 else 'personal'
            
            income_loan.add_loan(name, principal, rate, payment, date, loan_type)
        
        elif subcommand == 'pay':
            loan_id = sys.argv[3]
            amount = float(sys.argv[4])
            date = sys.argv[5]
            extra = float(sys.argv[6]) if len(sys.argv) > 6 else 0
            
            income_loan.record_payment(loan_id, amount, date, extra)
        
        elif subcommand == 'auto':
            loan_id = sys.argv[3]
            keywords = sys.argv[4].split(',')
            
            income_loan.auto_detect_loan_payments(loan_id, keywords)
        
        elif subcommand == 'timeline':
            loan_id = sys.argv[3]
            extra = float(sys.argv[4]) if len(sys.argv) > 4 else 0
            
            result = income_loan.calculate_payoff_timeline(loan_id, extra)
            
            if result and 'error' not in result:
                print(f"\n📅 PAYOFF TIMELINE\n")
                print(f"Months to payoff: {result['months_to_payoff']}")
                print(f"Payoff date: {result['payoff_date']}")
                print(f"Total interest: ${result['total_interest']:,.2f}")
                print(f"Total paid: ${result['total_paid']:,.2f}")
                
                if extra > 0:
                    base = income_loan.calculate_payoff_timeline(loan_id, 0)
                    saved_months = base['months_to_payoff'] - result['months_to_payoff']
                    saved_interest = base['total_interest'] - result['total_interest']
                    print(f"\n💡 By paying ${extra:.2f} extra monthly:")
                    print(f"   - Pay off {saved_months} months earlier")
                    print(f"   - Save ${saved_interest:,.2f} in interest")
        
        elif subcommand == 'compare':
            loan_id = sys.argv[3]
            comparisons = income_loan.compare_payoff_strategies(loan_id)
            
            print(f"\n🔍 PAYOFF STRATEGY COMPARISON\n")
            print(f"{'Extra/Month':12} {'Months':8} {'Payoff Date':12} {'Total Interest':15} {'Interest Saved':15}")
            print("-" * 70)
            
            for comp in comparisons:
                print(f"${comp['extra_monthly']:10,.0f} {comp['months_to_payoff']:7} {comp['payoff_date']:12} "
                      f"${comp['total_interest']:13,.2f} ${comp['interest_saved']:13,.2f}")
        
        elif subcommand == 'summary':
            summary = income_loan.get_loan_summary()
            
            print("\n💳 LOAN SUMMARY\n")
            print(f"Total Debt: ${summary['total_debt']:,.2f}")
            print(f"Total Monthly Payment: ${summary['total_monthly_payment']:,.2f}")
            print(f"Total Interest Paid: ${summary['total_interest_paid']:,.2f}\n")
            
            for loan in summary['loans']:
                print(f"{loan['name']:20} ${loan['balance']:10,.2f}  Rate: {loan['rate']:.2f}%  Payment: ${loan['payment']:.2f}")
                if loan['payoff_date']:
                    print(f"{'':20} Payoff: {loan['payoff_date']} ({loan['months_to_payoff']} months)")
                print()
        
        elif subcommand == 'avalanche':
            strategy = income_loan.avalanche_strategy()
            
            print("\n🏔️ DEBT AVALANCHE STRATEGY (Highest Interest First)\n")
            for item in strategy:
                print(f"{item['priority']}. {item['name']:20} ${item['balance']:10,.2f}  Rate: {item['rate']:.2f}%")
                print(f"   {item['recommendation']}")
                print()
        
        elif subcommand == 'snowball':
            strategy = income_loan.snowball_strategy()
            
            print("\n⛄ DEBT SNOWBALL STRATEGY (Lowest Balance First)\n")
            for item in strategy:
                print(f"{item['priority']}. {item['name']:20} ${item['balance']:10,.2f}  Rate: {item['rate']:.2f}%")
                print(f"   {item['recommendation']}")
                print()

if __name__ == "__main__":
    main()

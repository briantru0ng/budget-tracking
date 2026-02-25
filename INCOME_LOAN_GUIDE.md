# 💰 Income & Loan Tracking Guide

## Multiple Income Streams

Your tracker now intelligently categorizes different types of income!

### Automatic Income Categories

When money comes in, it's automatically categorized:

**Salary** - Your main job
- Keywords: payroll, direct deposit, paychex, ADP, employer

**Side Income** - Freelance, consulting, gigs
- Keywords: freelance, upwork, fiverr, consulting, contract

**Investments** - Dividends, interest, capital gains
- Keywords: dividend, interest, capital gain, schwab, fidelity, vanguard

**Gifts** - Money from family/friends (mom, dad, etc!)
- Keywords: venmo, zelle, cash app, paypal, gift, mom, dad, parent

**Refunds** - Returns and reimbursements
- Keywords: refund, reimbursement, return

**Government** - Tax refunds, stimulus, benefits
- Keywords: tax refund, stimulus, social security, unemployment

**Rental** - Rental property income
- Keywords: rent payment, rental income

**Business** - Business revenue
- Keywords: stripe, square, business revenue, sales

### View Income Breakdown

```bash
# All time
python income_loan_tracker.py income breakdown

# Specific date range
python income_loan_tracker.py income breakdown 2025-01-01 2025-02-19
```

**Example Output:**
```
💰 INCOME BREAKDOWN

Salary                $5,200.00  (2 payments, avg $2,600.00)
Gifts                   $450.00  (5 payments, avg $90.00)
Side_Income            $1,200.00  (3 payments, avg $400.00)
Investments             $125.50  (12 payments, avg $10.46)
Refunds                  $89.99  (2 payments, avg $45.00)

TOTAL                 $7,065.49
```

### Teaching Income Streams

Got money from someone new? Teach the system:

```bash
# Mom sends you money via Zelle
python income_loan_tracker.py income learn "mom zelle" Gifts

# Dad uses Venmo
python income_loan_tracker.py income learn "dad venmo" Gifts

# Grandma sends checks
python income_loan_tracker.py income learn "grandma check" Gifts

# Friend pays you back
python income_loan_tracker.py income learn "john payback" Gifts

# New freelance client
python income_loan_tracker.py income learn "acme corp" Side_Income
```

### Real Examples

**Problem:** "ZELLE TRANSFER FROM ELIZABETH" shows as "Other Income"

**Solution:**
```bash
python income_loan_tracker.py income learn "elizabeth" Gifts
python income_loan_tracker.py income learn "mom" Gifts  # If Elizabeth is mom
```

Now all transfers from Elizabeth auto-categorize as Gifts!

---

## Loan Tracking & Payoff Planning

Track all your loans and see exactly when they'll be paid off!

### Add a Loan

```bash
python income_loan_tracker.py loan add <name> <principal> <rate> <monthly_payment> <start_date> [type]
```

**Example: Student Loan**
```bash
python income_loan_tracker.py loan add "Student Loan" 25000 0.045 350 2020-09-01 student

# Principal: $25,000
# Rate: 4.5% (enter as 0.045)
# Monthly payment: $350
# Started: Sept 1, 2020
# Type: student
```

**Example: Car Loan**
```bash
python income_loan_tracker.py loan add "Car Loan" 18000 0.039 425 2023-06-15 auto
```

**Example: Credit Card**
```bash
python income_loan_tracker.py loan add "Chase Freedom" 3500 0.199 150 2024-01-01 credit_card
```

**Loan Types:**
- personal
- student
- auto
- mortgage
- credit_card

### Record Payments

**Manual entry:**
```bash
python income_loan_tracker.py loan pay student_loan 350 2025-02-15

# With extra principal:
python income_loan_tracker.py loan pay student_loan 350 2025-02-15 50
```

**Auto-detect from transactions:**
```bash
# Find all payments matching keywords
python income_loan_tracker.py loan auto student_loan "navient,student loan payment,mohela"

# System scans transaction history and auto-records payments!
```

This is **huge** - you never have to manually track payments again. Just run this once and it finds everything!

### Payoff Timeline

See exactly when you'll be debt-free:

```bash
# Current payment schedule
python income_loan_tracker.py loan timeline student_loan

# With extra payments
python income_loan_tracker.py loan timeline student_loan 100
```

**Example Output:**
```
📅 PAYOFF TIMELINE

Months to payoff: 89
Payoff date: 2032-07-15
Total interest: $6,150.00
Total paid: $31,150.00

💡 By paying $100 extra monthly:
   - Pay off 23 months earlier
   - Save $1,847.50 in interest
```

### Compare Strategies

See impact of different extra payments:

```bash
python income_loan_tracker.py loan compare student_loan
```

**Output:**
```
🔍 PAYOFF STRATEGY COMPARISON

Extra/Month    Months  Payoff Date  Total Interest  Interest Saved
-------------------------------------------------------------------
$0              89     2032-07-15   $6,150.00       $0.00
$50             79     2031-09-15   $5,389.25       $760.75
$100            71     2031-01-15   $4,782.40       $1,367.60
$200            61     2030-03-15   $3,854.20       $2,295.80
$500            44     2028-10-15   $2,543.10       $3,606.90
```

See the power of extra payments!

### All Loans Summary

```bash
python income_loan_tracker.py loan summary
```

**Output:**
```
💳 LOAN SUMMARY

Total Debt: $46,500.00
Total Monthly Payment: $925.00
Total Interest Paid: $2,347.50

Student Loan         $25,000.00  Rate: 4.50%  Payment: $350.00
                     Payoff: 2032-07-15 (89 months)

Car Loan            $18,000.00  Rate: 3.90%  Payment: $425.00
                     Payoff: 2027-04-15 (26 months)

Chase Freedom        $3,500.00  Rate: 19.90%  Payment: $150.00
                     Payoff: 2027-11-15 (33 months)
```

### Debt Payoff Strategies

Two popular methods:

#### Avalanche (Save Most Money)
Pay highest interest rate first:

```bash
python income_loan_tracker.py loan avalanche
```

**Output:**
```
🏔️ DEBT AVALANCHE STRATEGY (Highest Interest First)

1. Chase Freedom     $3,500.00  Rate: 19.90%
   Pay minimum on others, attack this one first

2. Student Loan      $25,000.00  Rate: 4.50%
   Pay minimum only

3. Car Loan          $18,000.00  Rate: 3.90%
   Pay minimum only
```

Mathematically optimal - saves most interest!

#### Snowball (Psychological Wins)
Pay smallest balance first:

```bash
python income_loan_tracker.py loan snowball
```

**Output:**
```
⛄ DEBT SNOWBALL STRATEGY (Lowest Balance First)

1. Chase Freedom     $3,500.00  Rate: 19.90%
   Pay off first for psychological win!

2. Car Loan          $18,000.00  Rate: 3.90%
   Pay minimum only

3. Student Loan      $25,000.00  Rate: 4.50%
   Pay minimum only
```

Quick wins boost motivation!

---

## Real-World Examples

### Example 1: Mom Sends Monthly Help

**Setup:**
```bash
# Teach the system
python income_loan_tracker.py income learn "mom zelle" Gifts
python income_loan_tracker.py income learn "elizabeth" Gifts  # If her name is Elizabeth
```

**Result:**
```
Income Breakdown:
Gifts               $500.00  (2 payments from mom)
```

### Example 2: Student Loan Payoff Plan

**Add loan:**
```bash
python income_loan_tracker.py loan add "Sallie Mae" 32000 0.055 425 2019-09-01 student
```

**Auto-detect past payments:**
```bash
python income_loan_tracker.py loan auto sallie_mae "sallie mae,student loan,great lakes"

Found 48 potential payments for Sallie Mae
✓ Recorded 48 payments
```

**See payoff timeline:**
```bash
python income_loan_tracker.py loan timeline sallie_mae

Months to payoff: 94
Payoff date: 2033-08-01
Total interest: $7,850.00
```

**Optimize with extra payments:**
```bash
python income_loan_tracker.py loan compare sallie_mae

# You see that $200 extra/month saves $3,200 in interest!
```

### Example 3: Multiple Credit Cards

```bash
# Add all cards
python income_loan_tracker.py loan add "Chase Freedom" 3200 0.199 120 2024-01-01 credit_card
python income_loan_tracker.py loan add "Discover It" 1800 0.189 80 2023-06-01 credit_card
python income_loan_tracker.py loan add "Amex Blue" 2500 0.215 100 2024-03-01 credit_card

# Get debt avalanche recommendation
python income_loan_tracker.py loan avalanche

🏔️ DEBT AVALANCHE STRATEGY
1. Amex Blue (21.5% - attack first!)
2. Chase Freedom (19.9%)
3. Discover It (18.9%)
```

Pay off Amex first - highest rate!

---

## Dashboard Integration

The income and loan features integrate with your Streamlit dashboard:

### Income Tab
- Pie chart of income sources
- Monthly trend line
- Breakdown table

### Loans Tab
- All loans with progress bars
- Payoff timelines
- Strategy recommendations
- "What if" calculator

### Coming Soon
I can add these tabs to your dashboard - just let me know!

---

## Pro Tips

### For Income:
1. **Run breakdown monthly** - see where money comes from
2. **Teach once, works forever** - mom's Zelles auto-categorize
3. **Track side hustle separately** - motivates you to grow it
4. **Investment income visible** - know your passive income

### For Loans:
1. **Auto-detect first** - finds all past payments instantly
2. **Compare before committing** - see impact of extra $50, $100, $200
3. **Avalanche saves most** - but snowball feels good too
4. **Run summary quarterly** - track progress

### Automation:
```bash
# Monthly cron job
0 0 1 * * python income_loan_tracker.py income breakdown >> ~/income_report.txt
0 0 1 * * python income_loan_tracker.py loan summary >> ~/loan_report.txt
```

Get monthly reports automatically!

---

## Common Questions

**Q: Mom sends money irregularly via Venmo. Will it track?**  
A: Yes! Teach it once: `income learn "mom" Gifts` and all future payments auto-categorize.

**Q: I have multiple student loans. Add separately?**  
A: Yes, add each loan separately so you can track them individually and apply strategies.

**Q: Can I see how much interest I've paid?**  
A: Yes! `loan summary` shows total interest paid across all loans.

**Q: What if I miss recording a payment?**  
A: Use `loan auto <loan_id> <keywords>` to find and record all past payments automatically.

**Q: Should I do avalanche or snowball?**  
A: Avalanche saves more money (math), snowball feels better (psychology). Both work - pick what motivates you!

**Q: Can I track my mortgage?**  
A: Absolutely! Add it as type "mortgage" and it works the same way.

---

## Quick Command Reference

```bash
# INCOME
income breakdown [start] [end]           # Show income by source
income learn <keyword> <stream>          # Teach categorization

# LOANS
loan add <name> <amt> <rate> <pmt> <date> [type]  # Add loan
loan pay <id> <amt> <date> [extra]                # Record payment
loan auto <id> <keywords>                          # Auto-detect payments
loan timeline <id> [extra]                         # Show payoff timeline
loan compare <id>                                  # Compare strategies
loan summary                                       # All loans overview
loan avalanche                                     # Best math strategy
loan snowball                                      # Best psychological strategy
```

You're now tracking every dollar in AND out! 💰📊

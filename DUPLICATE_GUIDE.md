# 🔍 Duplicate Detection Guide

## How Duplicates Are Prevented

Your budget tracker has **multi-layered duplicate detection** to prevent accidental duplicates:

### Automatic Prevention (Built-in)

When you add a statement, the system automatically checks for duplicates using two methods:

#### Method 1: Exact Match
Checks if these **3 fields** match exactly:
- Date
- Description  
- Amount

**Example:**
```
2025-02-15 | STARBUCKS #1234 | -$5.75
2025-02-15 | STARBUCKS #1234 | -$5.75  ← DUPLICATE (skipped)
```

#### Method 2: Normalized Merchant Match
Even if raw descriptions differ, checks if:
- Date matches
- Amount matches
- Normalized merchant name matches

**Example:**
```
Existing: 2025-02-15 | AMZN MKTP US*2X4H8 | -$29.99 → Normalized: "Amazon"
New:      2025-02-15 | AMAZON.COM*3F9K2 | -$29.99  → Normalized: "Amazon"
                                                     ↑ DUPLICATE (skipped)
```

This catches duplicates even when:
- Chase says "AMZN MKTP"
- Bank of America says "AMAZON.COM"
- Both are the same purchase!

### What You'll See

**CLI:**
```bash
python advanced_tracker.py add feb_statement.pdf "Chase"

✓ Added 45 new transactions
⚠️  Skipped 3 duplicates:
   - 2025-02-15: STARBUCKS #1234 $5.75 (Exact match)
   - 2025-02-18: Amazon $29.99 (Same merchant/date/amount)
   - 2025-02-20: Shell Gas $45.00 (Exact match)
```

**Dashboard:**
- Upload statement in Settings
- See success message: "✓ Added 45 new transactions!"
- If duplicates: "⚠️ Skipped 3 duplicates"
- Click to expand and see details

## Manual Duplicate Checking

Run a comprehensive scan anytime:

```bash
python check_duplicates.py scan
```

This performs **4 checks**:

### Check 1: Exact Duplicates
Finds transactions with identical date + description + amount

### Check 2: Likely Duplicates  
Same date + amount + merchant, but different raw descriptions
(Most common with multiple bank accounts)

### Check 3: Suspicious Matches
Same date, amounts within $0.10
(Catches potential duplicates with rounding differences)

### Check 4: Multiple Purchases
Multiple transactions same merchant same day
(Usually legitimate, but worth reviewing)

## Example Scan Output

```
🔍 Method 1: Exact Match Duplicates
✓ No exact duplicates found

🔍 Method 2: Likely Duplicates (Same Date + Amount + Merchant)
⚠️  Found 2 likely duplicate pairs

  2025-02-15 | Amazon | -$29.99
    Source 1: Chase Credit Card - AMZN MKTP US*2X4H8F3
    Source 2: Chase Checking    - AMAZON.COM PURCHASE

  2025-02-18 | Starbucks | -$5.75
    Source 1: Amex - SQ *STARBUCKS #542
    Source 2: Chase - STARBUCKS STORE #542

🔍 Method 3: Suspicious Matches
✓ No suspicious matches found

🔍 Method 4: Multiple Purchases
ℹ️  Found 5 instances of multiple purchases from same merchant

  2025-02-14 | Amazon | 3 transactions
    -$19.99 - AMZN MKTP US*BOOK
    -$29.99 - AMZN MKTP US*ELECTRONICS  
    -$12.50 - AMAZON.COM GIFT CARD
```

## Removing Duplicates

### Automatic Removal
Remove all exact duplicates at once:

```bash
python check_duplicates.py auto
```

This will:
1. Find all exact duplicates
2. Show you what will be removed
3. Ask for confirmation
4. Keep the first occurrence, remove the rest

**Example:**
```bash
⚠️  Found 5 exact duplicates to remove:
  2025-02-15 | STARBUCKS #1234 | -$5.75
  2025-02-18 | NETFLIX.COM | -$15.99
  ...

Remove all 5 duplicates? (yes/no): yes

✓ Removed 5 duplicate transactions
Database now has 247 transactions
```

### Manual Removal
Remove a specific transaction by its ID:

```bash
# First, scan to see transaction IDs
python check_duplicates.py scan

# Then remove specific one
python check_duplicates.py remove 123
```

## Common Scenarios

### Scenario 1: Uploaded Same PDF Twice
**What happens:** All transactions skipped as exact duplicates
**Action:** Nothing needed - system handled it!

### Scenario 2: Same Purchase, Two Accounts
You have Chase credit card AND Chase checking linked to same card.

**What happens:** System detects via normalized merchant matching
**Action:** Nothing needed - duplicate skipped automatically

### Scenario 3: Two Real Purchases, Same Day/Merchant
Two coffees at Starbucks, $5.75 each, same day.

**What happens:** Both kept (different times even if same amount)
**Shows as:** "Multiple Purchases" in scan (for review)
**Action:** Review scan output, both are probably legitimate

### Scenario 4: Credit + Debit for Same Thing
Paid with debit, transaction pending, also shows as credit charge.

**What happens:** Depends on exact descriptions
- If identical → One skipped automatically
- If slightly different → Both kept, flagged as "likely duplicate" in scan
**Action:** Run `check_duplicates.py scan`, manually review, remove one with `remove <id>`

## Best Practices

### ✅ Do This:
- Upload statements from all sources monthly
- Run `check_duplicates.py scan` quarterly
- Review "likely duplicates" section
- Keep raw PDFs as backup

### ⚠️ Watch For:
- Refunds (appear as positive amounts, don't match original)
- Partial payments (same merchant, different amounts)
- Pending vs. posted (description might change)

### 🚫 Don't Worry About:
- Uploading same PDF twice (auto-skipped)
- Different sources for same purchase (auto-detected)
- Minor description differences (normalized matching)

## Understanding "Multiple Purchases"

If scan shows multiple same-day purchases:

**Usually legitimate:**
- Multiple Amazon orders
- Two Starbucks visits
- Gas + snacks at same station

**Possibly duplicate:**
- Exact same amount
- Same time of day (if shown in description)
- Both from same source account

**To verify:** Check your bank statement PDF to see if both charges are real.

## Export Duplicates for Review

Want to review in Excel?

```python
# Quick script
import pandas as pd
from advanced_tracker import AdvancedBudgetTracker

tracker = AdvancedBudgetTracker()
df = tracker.transaction_db

# Find exact duplicates
dups = df[df.duplicated(subset=['Date', 'Description', 'Amount'], keep=False)]
dups = dups.sort_values(['Date', 'Description'])

# Export
dups.to_csv('duplicates_review.csv', index=False)
print(f"Exported {len(dups)} potential duplicates to duplicates_review.csv")
```

## FAQs

**Q: Will I lose transactions if I upload the same PDF twice?**  
A: No, they'll all be skipped as duplicates. The first upload is kept.

**Q: What if I have the same transaction on two credit cards?**  
A: The first one uploaded is kept, the second is skipped with "Same merchant/date/amount" reason.

**Q: Can I undo an auto-removal?**  
A: Not automatically, but you kept the original PDFs, right? Re-upload them and it'll add back the transactions you removed.

**Q: How do I know if duplicates are real or false positives?**  
A: Run `check_duplicates.py scan` and review the "Likely Duplicates" section. Compare descriptions and sources.

**Q: What about subscriptions that auto-renew?**  
A: Those aren't duplicates! Same merchant, same amount, but different dates. System only flags same-date matches.

## Summary

Your system has **3 layers of protection**:

1. **Automatic (on add):** Prevents duplicates when uploading statements
2. **Manual scan:** Comprehensive check with 4 methods
3. **Auto-cleanup:** Remove confirmed duplicates with one command

You're protected! 🛡️

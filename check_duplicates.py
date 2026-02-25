#!/usr/bin/env python3
"""
Duplicate Checker Utility
Scans transaction database for potential duplicates with detailed reporting
"""
import pandas as pd
from pathlib import Path
from advanced_tracker import AdvancedBudgetTracker

def check_duplicates():
    """Comprehensive duplicate detection with multiple methods"""
    
    tracker = AdvancedBudgetTracker()
    
    if tracker.transaction_db.empty:
        print("No transactions in database yet!")
        return
    
    df = tracker.transaction_db.copy()
    
    print("\n" + "="*70)
    print("DUPLICATE DETECTION REPORT")
    print("="*70 + "\n")
    
    # Method 1: Exact duplicates (Date + Description + Amount)
    print("🔍 Method 1: Exact Match Duplicates (Date + Description + Amount)")
    print("-" * 70)
    
    exact_dups = df[df.duplicated(subset=['Date', 'Description', 'Amount'], keep=False)]
    exact_dups = exact_dups.sort_values(['Date', 'Description', 'Amount'])
    
    if not exact_dups.empty:
        print(f"⚠️  Found {len(exact_dups)} transactions that are exact duplicates\n")
        for _, dup in exact_dups.iterrows():
            print(f"  {dup['Date'].strftime('%Y-%m-%d')} | {dup['Description'][:40]:40} | ${dup['Amount']:8.2f} | {dup['Source']}")
    else:
        print("✓ No exact duplicates found\n")
    
    # Method 2: Same day + amount + normalized merchant
    print("\n🔍 Method 2: Likely Duplicates (Same Date + Amount + Merchant)")
    print("-" * 70)
    
    likely_dups = []
    df_sorted = df.sort_values(['Date', 'Amount'])
    
    for i in range(len(df_sorted) - 1):
        curr = df_sorted.iloc[i]
        next_txn = df_sorted.iloc[i + 1]
        
        if (curr['Date'] == next_txn['Date'] and 
            curr['Amount'] == next_txn['Amount'] and
            curr['Normalized_Merchant'].lower() == next_txn['Normalized_Merchant'].lower() and
            curr['Description'] != next_txn['Description']):  # Different raw descriptions
            
            likely_dups.append({
                'date': curr['Date'],
                'merchant': curr['Normalized_Merchant'],
                'amount': curr['Amount'],
                'desc1': curr['Description'],
                'desc2': next_txn['Description'],
                'source1': curr['Source'],
                'source2': next_txn['Source']
            })
    
    if likely_dups:
        print(f"⚠️  Found {len(likely_dups)} likely duplicate pairs\n")
        for dup in likely_dups:
            print(f"  {dup['date'].strftime('%Y-%m-%d')} | {dup['merchant'][:30]:30} | ${dup['amount']:8.2f}")
            print(f"    Source 1: {dup['source1'][:40]:40} - {dup['desc1'][:40]}")
            print(f"    Source 2: {dup['source2'][:40]:40} - {dup['desc2'][:40]}")
            print()
    else:
        print("✓ No likely duplicates found\n")
    
    # Method 3: Same day + similar amounts (within $0.10)
    print("\n🔍 Method 3: Suspicious Matches (Same Date + Amount ±$0.10)")
    print("-" * 70)
    
    suspicious = []
    
    for i in range(len(df_sorted) - 1):
        curr = df_sorted.iloc[i]
        next_txn = df_sorted.iloc[i + 1]
        
        if (curr['Date'] == next_txn['Date'] and 
            abs(curr['Amount'] - next_txn['Amount']) <= 0.10 and
            curr['Amount'] != next_txn['Amount'] and
            curr.name != next_txn.name):  # Different transactions
            
            suspicious.append({
                'date': curr['Date'],
                'amount1': curr['Amount'],
                'amount2': next_txn['Amount'],
                'desc1': curr['Description'],
                'desc2': next_txn['Description'],
                'diff': abs(curr['Amount'] - next_txn['Amount'])
            })
    
    if suspicious:
        print(f"🤔 Found {len(suspicious)} suspicious pairs (might be legit, but worth checking)\n")
        for sus in suspicious[:10]:  # Show first 10
            print(f"  {sus['date'].strftime('%Y-%m-%d')} | ${sus['amount1']:8.2f} vs ${sus['amount2']:8.2f} (diff: ${sus['diff']:.2f})")
            print(f"    {sus['desc1'][:50]}")
            print(f"    {sus['desc2'][:50]}")
            print()
        if len(suspicious) > 10:
            print(f"  ... and {len(suspicious) - 10} more")
    else:
        print("✓ No suspicious matches found\n")
    
    # Method 4: Multiple transactions same merchant same day
    print("\n🔍 Method 4: Multiple Purchases (Same Merchant, Same Day)")
    print("-" * 70)
    
    daily_merchant = df.groupby([df['Date'].dt.date, 'Normalized_Merchant']).size()
    multiples = daily_merchant[daily_merchant > 1]
    
    if not multiples.empty:
        print(f"ℹ️  Found {len(multiples)} instances of multiple purchases from same merchant on same day")
        print("   (These might be legitimate - e.g., two Amazon orders)\n")
        
        for (date, merchant), count in multiples.head(10).items():
            print(f"  {date} | {merchant[:40]:40} | {count} transactions")
            
            # Show the transactions
            day_txns = df[(df['Date'].dt.date == date) & (df['Normalized_Merchant'] == merchant)]
            for _, txn in day_txns.iterrows():
                print(f"    ${txn['Amount']:8.2f} - {txn['Description'][:50]}")
            print()
        
        if len(multiples) > 10:
            print(f"  ... and {len(multiples) - 10} more days with multiple purchases")
    else:
        print("✓ No multiple purchases from same merchant on same day\n")
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total transactions in database: {len(df)}")
    print(f"Exact duplicates: {len(exact_dups)}")
    print(f"Likely duplicates: {len(likely_dups)}")
    print(f"Suspicious matches: {len(suspicious)}")
    print(f"Multiple same-day purchases: {len(multiples)}")
    
    if len(exact_dups) > 0:
        print("\n⚠️  ACTION REQUIRED: Review exact duplicates and remove manually if needed")
    elif len(likely_dups) > 0:
        print("\n⚠️  REVIEW RECOMMENDED: Check likely duplicates")
    else:
        print("\n✅ Database looks clean!")
    
    print("\n" + "="*70 + "\n")

def remove_duplicate(transaction_id):
    """Remove a specific transaction by index"""
    tracker = AdvancedBudgetTracker()
    
    if transaction_id >= len(tracker.transaction_db):
        print(f"Error: Transaction ID {transaction_id} not found")
        return
    
    txn = tracker.transaction_db.iloc[transaction_id]
    print(f"\nRemoving transaction:")
    print(f"  Date: {txn['Date'].strftime('%Y-%m-%d')}")
    print(f"  Description: {txn['Description']}")
    print(f"  Amount: ${txn['Amount']:.2f}")
    print(f"  Source: {txn['Source']}")
    
    confirm = input("\nAre you sure? (yes/no): ")
    if confirm.lower() == 'yes':
        tracker.transaction_db = tracker.transaction_db.drop(transaction_id).reset_index(drop=True)
        tracker.save_transaction_db()
        print("✓ Transaction removed")
    else:
        print("Cancelled")

def deduplicate_auto():
    """Automatically remove exact duplicates (keeps first occurrence)"""
    tracker = AdvancedBudgetTracker()
    
    if tracker.transaction_db.empty:
        print("No transactions in database yet!")
        return
    
    before = len(tracker.transaction_db)
    
    # Get duplicates to report what's being removed
    exact_dups = tracker.transaction_db[
        tracker.transaction_db.duplicated(subset=['Date', 'Description', 'Amount'], keep='first')
    ]
    
    if exact_dups.empty:
        print("✓ No duplicates to remove")
        return
    
    print(f"\n⚠️  Found {len(exact_dups)} exact duplicates to remove:\n")
    for _, dup in exact_dups.head(10).iterrows():
        print(f"  {dup['Date'].strftime('%Y-%m-%d')} | {dup['Description'][:40]:40} | ${dup['Amount']:8.2f}")
    
    if len(exact_dups) > 10:
        print(f"  ... and {len(exact_dups) - 10} more")
    
    confirm = input(f"\nRemove all {len(exact_dups)} duplicates? (yes/no): ")
    
    if confirm.lower() == 'yes':
        tracker.transaction_db = tracker.transaction_db.drop_duplicates(
            subset=['Date', 'Description', 'Amount'], 
            keep='first'
        ).reset_index(drop=True)
        
        tracker.save_transaction_db()
        after = len(tracker.transaction_db)
        removed = before - after
        
        print(f"\n✓ Removed {removed} duplicate transactions")
        print(f"Database now has {after} transactions")
    else:
        print("Cancelled")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("\n=== Duplicate Checker Utility ===\n")
        print("Commands:")
        print("  python check_duplicates.py scan           - Scan for duplicates")
        print("  python check_duplicates.py auto           - Auto-remove exact duplicates")
        print("  python check_duplicates.py remove <id>    - Remove specific transaction\n")
        sys.exit(0)
    
    command = sys.argv[1].lower()
    
    if command == 'scan':
        check_duplicates()
    elif command == 'auto':
        deduplicate_auto()
    elif command == 'remove' and len(sys.argv) >= 3:
        transaction_id = int(sys.argv[2])
        remove_duplicate(transaction_id)
    else:
        print("Unknown command. Use: scan, auto, or remove <id>")

# Recurring Transactions

Tracks subscriptions, bills, and other repeating charges. Three tabs cover different levels of confidence.

## Subscriptions Tab

Shows transactions in the **Services** basket, broken into:

- **Monthly Subscriptions** — sub-categories with "monthly" in the name
- **Yearly Subscriptions** — sub-categories with "yearly" or "annual" in the name (also shows the monthly equivalent cost)
- **Other Services** — everything else in the Services basket

Top metrics: total subscription cost, percentage of income, and service count. Filtered by a period selector (month/year).

Requires the Services basket to have sub-categories set up in Settings > Baskets.

## Confirmed Recurring Tab

Auto-detected recurring transactions that appeared in 3+ consecutive months with similar amounts. Displays:

- Merchant, amount, category, frequency
- Sorted by absolute amount

Also shows **Missing This Month** — any confirmed recurring transaction that hasn't appeared yet in the current month, with the expected date and amount.

## Possibly Recurring Tab

Candidates that appeared 2+ times but don't yet meet the 3-consecutive-month threshold. Shows:

- Merchant, average amount, occurrence count
- Which months it appeared in and the average day of month
- Sample description and current category

Click "Add to Recurring" to manually promote a candidate to the confirmed recurring list.

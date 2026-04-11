# All Transactions

A filterable, interactive table of every imported transaction. Also the main place to recategorize, teach rules, tag taxes, and split transactions.

## Filters

Five filter dropdowns across the top, all defaulting to "All":

- **Year** — filter by transaction year
- **Month** — cascades from the selected year (only shows months with data)
- **Group** — top-level basket (e.g., Food, Services, Housing)
- **Category** — sub-categories within the selected group
- **Source** — bank/card the transaction came from

## Summary Metrics

Three columns: transaction count, total income, and total expenses for the current filter.

## Transaction Table

Sortable, scrollable dataframe showing: Date, Description, Merchant, Group, Category, Amount, Source, and Tax Deductible flag. Supports multi-row selection for batch operations.

## Recategorize

Select rows in the table, then pick a Group and Category to reassign them. Clicking "Apply" updates the transactions and saves immediately.

The "Skip / Exclude" option sets the category to SKIP, which removes the transaction from all totals and charts.

## Quick Actions

### Teach Categorization
Enter a keyword and category — future transactions matching that keyword will auto-categorize. Also retroactively applies to existing transactions with the same merchant.

### Normalize Merchant
Map a raw bank description (e.g., `AMZN MKTP US*2X4H8`) to a clean name (e.g., `Amazon`). Affects display and grouping.

## Tag Tax Deductible

Enter a row number from the table, toggle deductible on/off, and optionally add notes (e.g., "home office", "business travel").

## Split Transaction

Splits a single transaction into multiple rows with different categories. Useful for mixed purchases (e.g., a Costco run with both groceries and household items).

- Pick the row to split
- Set 2-5 split categories and amounts
- Amounts must sum exactly to the original transaction total
- The original row is replaced by the new split rows

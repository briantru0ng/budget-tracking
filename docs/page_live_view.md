# Live View Dashboard

The main at-a-glance page for your finances. Shows income, expenses, net, and savings rate for any selected period.

## Period Selector

A dropdown at the top lets you pick:

- **Individual months** (current year first, then older)
- **YTD** (year-to-date aggregate)
- **1 Year Ago** (quick comparison to the same month last year)
- **All Time** (every transaction ever imported)

Defaults to the current month.

## Top Metrics

Four columns across the top:

| Metric | What it shows |
|---|---|
| Income | Sum of all transactions in Income basket categories |
| Expenses | Sum of all negative (spending) transactions |
| Net | Income minus expenses, with delta vs. previous month |
| Savings Rate | Percentage of income going to Savings basket categories |

## Budget & Recurring Alerts

Only shown for single-month views:

- **Budget alerts** — if any category is on track to exceed its budget (set in Settings > Budgets), a warning appears with the projected overage.
- **Missing recurring** — if the current month is selected and expected recurring transactions haven't appeared yet, they're flagged.

## Tabs

### Income
Table and pie chart of income grouped by merchant/source.

### Main Expenses
Fixed/essential costs: Rent, Electric, Gas, Groceries, Insurance, Internet, Water, Natural Gas. Displayed as a table with a pie chart breakdown.

### Personal Expenses
Everything that isn't a main expense, income, transfer, or SKIP. Sorted by amount with a pie chart.

### Working With Costs
A waterfall-style summary:
```
  Income
- Main Expenses
- Personal Expenses
= Working With
```
Shows how much discretionary money remains. Color-coded: green if positive, red if over budget.

### Expected Savings
If savings goals are configured, this tab shows each goal's monthly contribution as a percentage of the "Working With" amount, plus progress bars for each goal. Links to the Savings Goals page if none are set up.

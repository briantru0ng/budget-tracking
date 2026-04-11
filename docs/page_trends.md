# Trends & Insights

Visualizes spending over time by category basket. Useful for spotting seasonal patterns, lifestyle creep, and forecasting future months.

## View Styles

Select one of three modes at the top:

| Mode | Description |
|---|---|
| **Custom Range** | Pick start/end month+year manually |
| **YTD** | January through current month of the current year |
| **3-Month Projection** | Last 6 months of actuals plus 3 predicted future months |

## Detailed vs. Monthly

- **Monthly** (default) — one data point per basket per month. Clean line chart.
- **Detailed (daily)** — cumulative spending per day within each month, resetting to zero at month boundaries. Shows intra-month spending velocity.

## Category Toggles

Right-side column of checkboxes, one per basket. Toggle baskets on/off to compare subsets. Income and Transfers are off by default. Each basket gets a distinct color with a color swatch shown under its checkbox.

## Projection Logic

When projecting future months, the algorithm picks the best estimate:

1. If the last 3 actual months are stable (within 10% of each other) AND differ from the historical same-calendar-month average, use the stable recent value.
2. Otherwise, average the same calendar month across all prior years.
3. Fallback: trailing 3-month average.

Projected months render as dashed lines connected to the last actual data point.

## Chart Details

- Plotly interactive chart with hover showing per-basket values.
- X-axis uses `Mon 'YY` format labels.
- Legend is horizontal above the chart.
- In detailed mode, cumulative spending resets to $0 at each month boundary.

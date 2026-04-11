import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime


# Distinct colors for each basket — visually separable on white background
BASKET_COLORS = [
    '#e6194b',  # red
    '#3cb44b',  # green
    '#4363d8',  # blue
    '#f58231',  # orange
    '#911eb4',  # purple
    '#42d4f4',  # cyan
    '#f032e6',  # magenta
    '#bfef45',  # lime
    '#fabed4',  # pink
    '#469990',  # teal
    '#dcbeff',  # lavender
    '#9A6324',  # brown
    '#800000',  # maroon
    '#aaffc3',  # mint
    '#808000',  # olive
    '#000075',  # navy
]


def _predict_month(target_month, basket, full_df, recent_3):
    """Predict spending for *target_month* (a pd.Period) for a given basket.

    Priority:
      1. If last 3 actual months are stable (within 10% of each other) AND
         that stable value differs from the historical same-month average,
         use the stable recent value.
      2. Otherwise, average the same calendar month across all prior years.
      3. Fallback: average of last 3 actual months.
    """
    cal_month = target_month.month  # e.g. 5 for May

    # --- historical same-month values across prior years ---
    hist = full_df[
        (full_df['Basket'] == basket) &
        (full_df['Budget_Date'].dt.month == cal_month) &
        (full_df['Budget_Date'].dt.to_period('M') < target_month)
    ]
    hist_values = hist.groupby(hist['Budget_Date'].dt.year)['Amount'].sum().tolist()
    hist_avg = sum(hist_values) / len(hist_values) if hist_values else None

    # --- stable recent trend (last 3 months within 10%) ---
    stable_value = None
    if len(recent_3) >= 3 and all(v > 0 for v in recent_3):
        mean_r = sum(recent_3) / 3
        if mean_r > 0 and all(abs(v - mean_r) / mean_r <= 0.10 for v in recent_3):
            stable_value = mean_r

    # --- decision ---
    if stable_value is not None and hist_avg is not None:
        # Stable recent trend exists AND differs from historical → favor stable
        if abs(stable_value - hist_avg) / max(hist_avg, 1) > 0.10:
            return round(stable_value, 2)
        # They roughly agree — use historical (more data points)
        return round(hist_avg, 2)

    if hist_avg is not None:
        return round(hist_avg, 2)

    if stable_value is not None:
        return round(stable_value, 2)

    # Fallback: trailing 3-month average
    if recent_3:
        return round(sum(recent_3) / len(recent_3), 2)

    return 0


def render(tracker):
    st.title("Trends & Insights")

    if tracker.transaction_db.empty:
        st.warning("No transactions yet!")
        st.stop()

    df = tracker.transaction_db.copy()
    df = df[df['Amount'] < 0].copy()  # expenses only
    df['Amount'] = df['Amount'].abs()

    # Map each transaction to its basket
    df['Basket'] = df['Category'].apply(tracker.get_basket_for_category)
    df = df[df['Basket'].notna()]

    # --- Style selector row ---------------------------------------------------
    style_col, detail_col, range_col = st.columns([2, 1, 3])

    with style_col:
        style = st.radio(
            "View style",
            ["Custom Range", "YTD", "3-Month Projection"],
            horizontal=True,
        )

    with detail_col:
        detailed = st.checkbox("Detailed (daily)", value=False, key="trend_detailed")

    # Determine date bounds based on style
    all_months = sorted(df['Budget_Date'].dt.to_period('M').unique())
    if not all_months:
        st.info("No expense data to chart.")
        st.stop()

    min_date = all_months[0]
    max_date = all_months[-1]

    if style == "YTD":
        now = datetime.now()
        start_period = pd.Period(f"{now.year}-01", freq='M')
        end_period = pd.Period(f"{now.year}-{now.month}", freq='M')
        with range_col:
            st.caption(f"Showing {start_period} to {end_period}")

    elif style == "Custom Range":
        with range_col:
            rc1, rc2, rc3, rc4 = st.columns(4)
            month_names = [
                "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
            ]
            available_years = sorted(set(m.year for m in all_months))
            with rc1:
                s_month = st.selectbox("Start month", month_names, index=min_date.month - 1, key="trend_sm")
            with rc2:
                s_year = st.selectbox("Start year", available_years, index=0, key="trend_sy")
            with rc3:
                e_month = st.selectbox("End month", month_names, index=max_date.month - 1, key="trend_em")
            with rc4:
                e_year = st.selectbox("End year", available_years, index=len(available_years) - 1, key="trend_ey")
            start_period = pd.Period(f"{s_year}-{month_names.index(s_month) + 1}", freq='M')
            end_period = pd.Period(f"{e_year}-{month_names.index(e_month) + 1}", freq='M')

    else:  # 3-Month Projection
        now = datetime.now()
        # Show last 6 months of actuals + 3 projected
        six_ago = pd.Period(f"{now.year}-{now.month}", freq='M') - 5
        start_period = max(min_date, six_ago)
        end_period = pd.Period(f"{now.year}-{now.month}", freq='M') + 3
        with range_col:
            st.caption(f"Actuals + 3-month projection ({start_period} to {end_period})")

    st.divider()

    # --- Category / basket toggles (sidebar-style, right column) ---------------
    chart_col, toggle_col = st.columns([3, 1])

    baskets = list(tracker.baskets.keys())
    # Exclude Income / Transfers from default selection
    default_off = {'Income', 'Transfers'}
    color_map = {b: BASKET_COLORS[i % len(BASKET_COLORS)] for i, b in enumerate(baskets)}

    with toggle_col:
        st.markdown("**Categories**")
        selected_baskets = []
        mid = (len(baskets) + 1) // 2
        col_left, col_right = st.columns(2)
        for idx, basket in enumerate(baskets):
            color = color_map[basket]
            default = basket not in default_off
            col = col_left if idx < mid else col_right
            with col:
                checked = st.checkbox(
                    basket,
                    value=default,
                    key=f"trend_basket_{basket}",
                )
                if checked:
                    selected_baskets.append(basket)
                st.markdown(
                    f'<div style="height:4px;width:40px;background:{color};'
                    f'border-radius:2px;margin-top:-10px;margin-bottom:8px;'
                    f'opacity:{"1" if checked else "0.25"}"></div>',
                    unsafe_allow_html=True,
                )

    # --- Build chart data ------------------------------------------------------
    df['Period'] = df['Budget_Date'].dt.to_period('M')
    mask = (df['Period'] >= start_period) & (df['Period'] <= end_period)
    filtered = df[mask]

    now_period = pd.Period(f"{datetime.now().year}-{datetime.now().month}", freq='M')

    # Per-basket: prediction starts after the later of now or last month with actual data
    df['Period'] = df['Budget_Date'].dt.to_period('M')
    _basket_cutoff = {}
    for b in tracker.baskets:
        bdata = df[df['Basket'] == b]
        if not bdata.empty:
            last_data = bdata['Period'].max()
            _basket_cutoff[b] = max(last_data, now_period)
        else:
            _basket_cutoff[b] = now_period

    fig = go.Figure()

    if detailed:
        # ---- DETAILED: day-by-day spending per basket, resets each month ----
        # Connected line across all days; cumulative resets per month
        all_range_months = pd.period_range(start_period, end_period, freq='M')

        for basket in selected_baskets:
            color = color_map[basket]
            bdata = filtered[filtered['Basket'] == basket].copy()
            bdata['Day'] = bdata['Budget_Date'].dt.date

            daily = bdata.groupby('Day')['Amount'].sum().reset_index()
            daily = daily.sort_values('Day')
            daily['YearMonth'] = pd.to_datetime(daily['Day']).dt.to_period('M')
            daily['Cumulative'] = daily.groupby('YearMonth')['Amount'].cumsum()

            # Build a continuous series: for each month, carry the cumulative,
            # then reset to 0 on the 1st of the next month
            all_x, all_y = [], []
            for _, row in daily.iterrows():
                day_str = str(row['Day'])
                # If new month and we have prior data, insert a reset point
                if all_x:
                    prev_period = pd.Period(all_x[-1], freq='D').to_timestamp().to_period('M')
                    curr_period = row['YearMonth']
                    if curr_period > prev_period:
                        # Reset: drop to 0 at the 1st of this new month
                        reset_date = curr_period.to_timestamp().date().isoformat()
                        all_x.append(reset_date)
                        all_y.append(0)
                all_x.append(day_str)
                all_y.append(row['Cumulative'])

            # Gather monthly totals for prediction
            monthly = bdata.groupby('YearMonth')['Amount'].sum()
            cutoff = _basket_cutoff.get(basket, now_period)
            past_actual = [monthly.get(m, 0) for m in all_range_months
                           if m <= cutoff and monthly.get(m, 0) > 0]

            # Append predicted future months as connected dashed extension
            proj_x, proj_y = [], []
            for m in all_range_months:
                if m > cutoff:
                    recent_3 = past_actual[-3:] if past_actual else []
                    pred_val = _predict_month(m, basket, df, recent_3)
                    past_actual.append(pred_val)
                    proj_x.append(m.to_timestamp().date().isoformat())
                    proj_y.append(pred_val)

            # Bridge: connect last actual point to first projected point
            if all_x and proj_x:
                bridge_x = [all_x[-1], proj_x[0]]
                bridge_y = [all_y[-1], proj_y[0]]
                fig.add_trace(go.Scatter(
                    x=bridge_x, y=bridge_y,
                    mode='lines',
                    line=dict(color=color, width=2, dash='dash'),
                    legendgroup=basket,
                    showlegend=False,
                    hoverinfo='skip',
                ))

            # Actual line
            if all_x:
                fig.add_trace(go.Scatter(
                    x=all_x, y=all_y,
                    mode='lines',
                    name=basket,
                    line=dict(color=color, width=2),
                    legendgroup=basket,
                ))

            # Projected line (dashed, future only)
            if proj_x:
                fig.add_trace(go.Scatter(
                    x=proj_x, y=proj_y,
                    mode='lines+markers',
                    name=f"{basket} (proj)",
                    line=dict(color=color, width=2, dash='dash'),
                    marker=dict(size=6),
                    legendgroup=basket,
                    showlegend=False,
                ))

        # Month boundary tick marks
        tick_vals = [m.to_timestamp().date().isoformat() for m in all_range_months]
        tick_text = [f"{m.strftime('%b')} '{str(m.year)[-2:]}" for m in all_range_months]

        fig.update_layout(
            xaxis=dict(title="Date", tickmode="array", tickvals=tick_vals, ticktext=tick_text),
            yaxis_title="Spending ($)",
            hovermode="x unified",
            hoverlabel=dict(namelength=-1),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            margin=dict(l=40, r=20, t=40, b=40),
            height=500,
        )

    else:
        # ---- MONTHLY: original monthly sum view ----
        grouped = (
            filtered.groupby(['Basket', 'Period'])['Amount']
            .sum()
            .reset_index()
        )
        grouped['Month'] = grouped['Period'].astype(str)

        all_range_months = pd.period_range(start_period, end_period, freq='M')
        month_labels = [str(m) for m in all_range_months]

        for basket in selected_baskets:
            color = color_map[basket]
            basket_data = grouped[grouped['Basket'] == basket]

            amounts = []
            for m in all_range_months:
                row = basket_data[basket_data['Period'] == m]
                if not row.empty:
                    amounts.append(row['Amount'].values[0])
                else:
                    amounts.append(0)

            cutoff = _basket_cutoff.get(basket, now_period)
            past_actual = [amounts[i] for i, m in enumerate(all_range_months)
                           if m <= cutoff and amounts[i] > 0]

            if style == "3-Month Projection":
                for i, m in enumerate(all_range_months):
                    if m > cutoff and amounts[i] == 0:
                        recent_3 = past_actual[-3:] if past_actual else []
                        amounts[i] = _predict_month(m, basket, df, recent_3)
                        past_actual.append(amounts[i])

                actual_x, actual_y = [], []
                proj_x, proj_y = [], []
                for i, m in enumerate(all_range_months):
                    if m <= cutoff:
                        actual_x.append(month_labels[i])
                        actual_y.append(amounts[i])
                    else:
                        proj_x.append(month_labels[i])
                        proj_y.append(amounts[i])

                if actual_x and proj_x:
                    fig.add_trace(go.Scatter(
                        x=[actual_x[-1], proj_x[0]],
                        y=[actual_y[-1], proj_y[0]],
                        mode='lines',
                        line=dict(color=color, width=2, dash='dash'),
                        legendgroup=basket,
                        showlegend=False,
                        hoverinfo='skip',
                    ))

                fig.add_trace(go.Scatter(
                    x=actual_x, y=actual_y,
                    mode='lines+markers',
                    name=basket,
                    line=dict(color=color, width=2),
                    legendgroup=basket,
                ))
                fig.add_trace(go.Scatter(
                    x=proj_x, y=proj_y,
                    mode='lines+markers',
                    name=f"{basket} (proj)",
                    line=dict(color=color, width=2, dash='dash'),
                    legendgroup=basket,
                    showlegend=False,
                ))
            else:
                # Only predict months beyond last actual data; past zeros stay as 0
                is_predicted = []
                for i, m in enumerate(all_range_months):
                    if amounts[i] == 0 and m > cutoff:
                        recent_3 = past_actual[-3:] if past_actual else []
                        amounts[i] = _predict_month(m, basket, df, recent_3)
                        past_actual.append(amounts[i])
                        is_predicted.append(True)
                    else:
                        if amounts[i] > 0:
                            past_actual.append(amounts[i])
                        is_predicted.append(False)

                # Split into segments: runs of actual vs predicted
                segments = []
                for i in range(len(amounts)):
                    pred = is_predicted[i]
                    if not segments or segments[-1][2] != pred:
                        if segments:
                            segments.append(
                                ([month_labels[i - 1], month_labels[i]],
                                 [amounts[i - 1], amounts[i]],
                                 pred)
                            )
                        else:
                            segments.append(([month_labels[i]], [amounts[i]], pred))
                    else:
                        segments[-1][0].append(month_labels[i])
                        segments[-1][1].append(amounts[i])

                first_actual = True
                for x_seg, y_seg, pred in segments:
                    if pred:
                        if len(x_seg) >= 2:
                            # Bridge from last actual to first projected (skip hover)
                            fig.add_trace(go.Scatter(
                                x=x_seg[:2], y=y_seg[:2],
                                mode='lines',
                                line=dict(color=color, width=2, dash='dash'),
                                legendgroup=basket,
                                showlegend=False,
                                hoverinfo='skip',
                            ))
                            # Future projected points (show hover)
                            fig.add_trace(go.Scatter(
                                x=x_seg[1:], y=y_seg[1:],
                                mode='lines+markers',
                                name=f"{basket} (proj)",
                                line=dict(color=color, width=2, dash='dash'),
                                legendgroup=basket,
                                showlegend=False,
                            ))
                        else:
                            # Single bridge point only — skip hover
                            fig.add_trace(go.Scatter(
                                x=x_seg, y=y_seg,
                                mode='lines+markers',
                                name=f"{basket} (proj)",
                                line=dict(color=color, width=2, dash='dash'),
                                legendgroup=basket,
                                showlegend=False,
                                hoverinfo='skip',
                            ))
                    else:
                        fig.add_trace(go.Scatter(
                            x=x_seg, y=y_seg,
                            mode='lines+markers',
                            name=basket,
                            line=dict(color=color, width=2),
                            legendgroup=basket,
                            showlegend=first_actual,
                        ))
                        first_actual = False

        # Month tick labels
        tick_labels = []
        for m in all_range_months:
            short_month = m.strftime('%b')
            short_year = str(m.year)[-2:]
            tick_labels.append(f"{short_month} '{short_year}")

        fig.update_layout(
            xaxis=dict(title="Month", tickmode="array", tickvals=month_labels, ticktext=tick_labels),
            yaxis_title="Spending ($)",
            hovermode="x unified",
            hoverlabel=dict(namelength=-1),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            margin=dict(l=40, r=20, t=40, b=40),
            height=500,
        )

    with chart_col:
        st.plotly_chart(fig, use_container_width=True)

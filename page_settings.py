import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta


def render(tracker, income_loan, savings_goals, load_budgets, save_budgets):
    st.title("⚙️ Settings & Tools")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🗂️ Baskets",
        "💰 Apply Interest",
        "🔍 Income Breakdown",
        "🧹 Duplicates",
        "🏷️ Categorization",
        "💾 Budgets",
    ])

    # TAB 1: Baskets
    with tab1:
        st.subheader("🗂️ Category Baskets")
        st.caption(
            "Baskets are top-level groupings. Sub-categories sit inside baskets "
            "and are what transactions actually get tagged with."
        )

        for basket_name, subs in tracker.baskets.items():
            with st.expander(f"**{basket_name}** ({len(subs)} sub-categories)"):
                if subs:
                    for sub in subs:
                        c1, c2 = st.columns([4, 1])
                        with c1:
                            st.write(f"  • {sub}")
                        with c2:
                            if st.button(
                                "✕", key=f"del_sub_{basket_name}_{sub}"
                            ):
                                tracker.baskets[basket_name].remove(sub)
                                tracker.save_baskets()
                                st.rerun()
                else:
                    st.write("*(empty — add sub-categories below)*")

                # Add sub-category inline
                ac1, ac2 = st.columns([3, 1])
                with ac1:
                    new_s = st.text_input(
                        "New sub-category",
                        key=f"add_sub_{basket_name}",
                        placeholder="e.g. Coffee, Subscriptions",
                        label_visibility="collapsed",
                    )
                with ac2:
                    if st.button("Add", key=f"add_sub_btn_{basket_name}"):
                        if new_s:
                            tracker.add_subcategory(basket_name, new_s)
                            st.success(f"✓ Added '{new_s}'")
                            st.rerun()

        st.divider()
        st.subheader("Create a new basket")
        bc1, bc2 = st.columns([3, 1])
        with bc1:
            new_basket = st.text_input(
                "Basket name",
                placeholder="e.g. Subscriptions, Pets, Education",
                key="new_basket_name",
            )
        with bc2:
            st.write("")
            st.write("")
            if st.button("Create", type="primary", key="create_basket_btn"):
                if new_basket:
                    if tracker.add_basket(new_basket):
                        st.success(f"✓ Created basket '{new_basket}'")
                        st.rerun()
                    else:
                        st.warning(f"'{new_basket}' already exists")

    # TAB 2: Apply Interest
    with tab2:
        st.subheader("💰 Apply Interest to Savings Goals")
        st.write("Manually compound interest on your savings goals (use for monthly interest payments)")

        all_goals = savings_goals.get_all_goals()
        interest_goals = [g for g in all_goals if g.get('interest_rate', 0) > 0]

        if not interest_goals:
            st.info("No goals with interest rates set. Add interest rates to your goals in the Savings Goals tab!")
        else:
            selected_goal_name = st.selectbox(
                "Select Goal",
                [g['name'] for g in interest_goals],
                key="interest_goal"
            )

            selected_goal = next(g for g in interest_goals if g['name'] == selected_goal_name)

            st.info(
                f"**{selected_goal['name']}**\n"
                f"- Current Balance: ${selected_goal['current_amount']:,.2f}\n"
                f"- Interest Rate: {selected_goal['interest_rate'] * 100:.2f}% APY"
            )

            months = st.number_input(
                "Number of Months to Compound",
                min_value=1, max_value=12, value=1,
                help="Typically 1 month for monthly interest payments"
            )

            monthly_rate = selected_goal['interest_rate'] / 12
            preview_interest = selected_goal['current_amount'] * monthly_rate * months
            preview_new_balance = selected_goal['current_amount'] + preview_interest

            st.write("**Preview:**")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Interest to Add", f"${preview_interest:.2f}")
            with col2:
                st.metric("New Balance", f"${preview_new_balance:.2f}")

            if st.button("Apply Interest", type="primary", key="apply_interest_btn"):
                interest_earned = savings_goals.apply_interest(selected_goal['goal_id'], months)
                if interest_earned:
                    st.success(f"✓ Applied {months} month(s) of interest")
                    st.success(f"💰 Interest earned: ${interest_earned:.2f}")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Failed to apply interest")

        st.divider()

        if interest_goals:
            st.subheader("Apply to All Goals")
            st.write("Apply 1 month of interest to all interest-bearing goals at once")

            if st.button("Apply to All Goals", key="apply_all_interest"):
                total_interest = 0
                for goal in interest_goals:
                    interest = savings_goals.apply_interest(goal['goal_id'], 1)
                    if interest:
                        total_interest += interest

                st.success(f"✓ Applied interest to {len(interest_goals)} goals")
                st.success(f"💰 Total interest earned: ${total_interest:.2f}")
                st.balloons()
                st.rerun()

    # TAB 3: Income Breakdown
    with tab3:
        st.subheader("🔍 Income Stream Analysis")

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=90))
        with col2:
            end_date = st.date_input("End Date", value=datetime.now())

        if st.button("Analyze Income", type="primary"):
            income_loan.recategorize_income()
            breakdown = income_loan.get_income_breakdown(
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )

            if breakdown:
                st.write(f"### Income Breakdown ({start_date} to {end_date})")

                data = []
                total = 0
                for stream, stats in breakdown.items():
                    data.append({
                        'Stream': stream,
                        'Total': stats['sum'],
                        'Count': stats['count'],
                        'Average': stats['mean']
                    })
                    total += stats['sum']

                df = pd.DataFrame(data).sort_values('Total', ascending=False)

                fig = px.pie(df, values='Total', names='Stream', title=f"Total Income: ${total:,.2f}")
                st.plotly_chart(fig, use_container_width=True)

                st.dataframe(
                    df.style.format({'Total': '${:,.2f}', 'Average': '${:,.2f}'}),
                    use_container_width=True
                )
            else:
                st.info("No income transactions found in this date range")

        st.divider()

        st.subheader("Teach Income Categorization")

        col1, col2 = st.columns(2)
        with col1:
            keyword = st.text_input("Keyword (e.g., 'mom', 'dad', 'venmo from john')")
        with col2:
            stream = st.selectbox(
                "Income Stream",
                ["Salary", "Side_Income", "Investments", "Gifts", "Refunds", "Government", "Rental", "Business"]
            )

        if st.button("Teach", key="teach_income"):
            if keyword:
                income_loan.income_streams[stream].append(keyword.lower())
                income_loan.save_income_streams()
                st.success(f"✓ Learned: '{keyword}' → {stream}")
                st.info("Tip: Go to All Transactions and use 'Recategorize All' to apply this rule")
            else:
                st.error("Please enter a keyword")

    # TAB 4: Duplicates
    with tab4:
        st.subheader("🧹 Duplicate Detection & Cleanup")

        if tracker.transaction_db.empty:
            st.info("No transactions to scan")
        else:
            if st.button("🔍 Scan for Duplicates", type="primary"):
                df = tracker.transaction_db.copy()

                exact_dups = df[df.duplicated(subset=['Date', 'Description', 'Amount'], keep=False)]
                exact_dups = exact_dups.sort_values(['Date', 'Description', 'Amount'])

                likely_dups = []
                df_sorted = df.sort_values(['Date', 'Amount'])
                for i in range(len(df_sorted) - 1):
                    curr = df_sorted.iloc[i]
                    next_txn = df_sorted.iloc[i + 1]

                    if (curr['Date'] == next_txn['Date'] and
                            curr['Amount'] == next_txn['Amount'] and
                            curr.get('Normalized_Merchant', '').lower() ==
                            next_txn.get('Normalized_Merchant', '').lower() and
                            curr['Description'] != next_txn['Description']):

                        likely_dups.append({
                            'Date': curr['Date'].strftime('%Y-%m-%d'),
                            'Merchant': curr.get('Normalized_Merchant', 'Unknown'),
                            'Amount': curr['Amount'],
                            'Desc1': curr['Description'],
                            'Desc2': next_txn['Description']
                        })

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Exact Duplicates", len(exact_dups))
                with col2:
                    st.metric("Likely Duplicates", len(likely_dups))

                if not exact_dups.empty:
                    st.warning(f"⚠️ Found {len(exact_dups)} exact duplicate transactions")
                    with st.expander("View Exact Duplicates"):
                        st.dataframe(exact_dups[['Date', 'Description', 'Amount', 'Source']], use_container_width=True)
                else:
                    st.success("✓ No exact duplicates found")

                if likely_dups:
                    st.warning(f"🤔 Found {len(likely_dups)} likely duplicate pairs")
                    with st.expander("View Likely Duplicates"):
                        for dup in likely_dups[:10]:
                            st.write(f"**{dup['Date']} - {dup['Merchant']} - ${dup['Amount']:.2f}**")
                            st.text(f"1: {dup['Desc1']}")
                            st.text(f"2: {dup['Desc2']}")
                            st.divider()
                else:
                    st.success("✓ No likely duplicates found")

                # Method 3: Suspicious matches (same date, amount within $0.10)
                suspicious = []
                for i in range(len(df_sorted) - 1):
                    curr = df_sorted.iloc[i]
                    next_txn = df_sorted.iloc[i + 1]
                    if (curr['Date'] == next_txn['Date'] and
                            abs(curr['Amount'] - next_txn['Amount']) <= 0.10 and
                            curr['Amount'] != next_txn['Amount'] and
                            curr.name != next_txn.name):
                        suspicious.append({
                            'Date': curr['Date'].strftime('%Y-%m-%d'),
                            'Amount 1': curr['Amount'],
                            'Amount 2': next_txn['Amount'],
                            'Diff': abs(curr['Amount'] - next_txn['Amount']),
                            'Desc 1': curr['Description'][:50],
                            'Desc 2': next_txn['Description'][:50],
                        })

                if suspicious:
                    st.warning(f"🤔 {len(suspicious)} suspicious pairs (same day, amount differs ≤$0.10)")
                    with st.expander("View Suspicious Matches"):
                        for s in suspicious[:10]:
                            st.write(
                                f"**{s['Date']}** — "
                                f"${s['Amount 1']:.2f} vs ${s['Amount 2']:.2f} "
                                f"(diff ${s['Diff']:.2f})"
                            )
                            st.text(f"  {s['Desc 1']}")
                            st.text(f"  {s['Desc 2']}")
                            st.divider()
                else:
                    st.success("✓ No suspicious amount matches found")

                # Method 4: Multiple purchases same merchant same day
                daily_merchant = df.groupby([df['Date'].dt.date, 'Normalized_Merchant']).size()
                multiples = daily_merchant[daily_merchant > 1]

                if not multiples.empty:
                    st.info(
                        f"ℹ️ {len(multiples)} cases of multiple purchases from "
                        "same merchant on same day (usually legitimate)"
                    )
                    with st.expander("View Multiple Same-Day Purchases"):
                        for (date, merchant), count in multiples.head(15).items():
                            st.write(f"**{date} — {merchant}** ({count} transactions)")
                            day_txns = df[
                                (df['Date'].dt.date == date) &
                                (df['Normalized_Merchant'] == merchant)
                            ]
                            for _, t in day_txns.iterrows():
                                st.text(f"  ${t['Amount']:.2f}  {t['Description'][:50]}")
                else:
                    st.success("✓ No multiple same-day purchases from same merchant")

        st.divider()

        st.subheader("Auto-Remove Duplicates")
        st.warning("⚠️ This will remove ALL exact duplicate transactions (keeps first occurrence)")

        if st.button("🗑️ Remove All Duplicates", key="remove_dups"):
            before = len(tracker.transaction_db)
            tracker.transaction_db = tracker.transaction_db.drop_duplicates(
                subset=['Date', 'Description', 'Amount'],
                keep='first'
            ).reset_index(drop=True)
            tracker.save_transaction_db()
            after = len(tracker.transaction_db)
            removed = before - after

            if removed > 0:
                st.success(f"✓ Removed {removed} duplicate transactions")
                st.info(f"Database now has {after} transactions")
                st.rerun()
            else:
                st.info("No duplicates to remove")

    # TAB 5: Categorization
    with tab5:
        st.subheader("🏷️ Categorization Management")

        st.write("**Quick Teach**")
        col1, col2 = st.columns(2)
        with col1:
            keyword = st.text_input("Merchant Keyword", placeholder="e.g., wegmans, starbucks")
        with col2:
            category = st.selectbox("Category", sorted(tracker.category_rules.keys()))

        if st.button("Add Keyword", type="primary", key="add_keyword"):
            if keyword:
                if tracker.learn_category(keyword, category):
                    st.success(f"✓ Learned: '{keyword}' → {category}")
                else:
                    st.info(f"'{keyword}' already in {category}")
            else:
                st.error("Please enter a keyword")

        st.divider()

        st.write("**Merchant Normalization**")
        st.caption("Clean up messy transaction names")

        col1, col2 = st.columns(2)
        with col1:
            raw_name = st.text_input("Raw Name", placeholder="e.g., AMZN MKTP US*2X4H8")
        with col2:
            clean_name = st.text_input("Clean Name", placeholder="e.g., Amazon")

        if st.button("Add Normalization", key="add_norm"):
            if raw_name and clean_name:
                tracker.learn_merchant_normalization(raw_name, clean_name)
                st.success(f"✓ Normalized: '{raw_name}' → '{clean_name}'")
            else:
                st.error("Please fill both fields")

        st.divider()

        st.write("**Apply All Rules**")
        st.info("Re-run categorization on ALL transactions with updated rules")

        if st.button("🔄 Recategorize All Transactions", key="recat_all"):
            with st.spinner("Recategorizing..."):
                tracker.recategorize_all()
                income_loan.recategorize_income()
                st.success("✓ Recategorized all transactions!")
                st.rerun()

        st.divider()

        st.write("**Uncategorized Transactions**")
        if not tracker.transaction_db.empty:
            uncategorized = tracker.transaction_db[tracker.transaction_db['Category'] == 'UNCATEGORIZED']

            st.metric("Uncategorized Count", len(uncategorized))

            if not uncategorized.empty:
                st.warning("These transactions need categorization:")
                st.dataframe(
                    uncategorized[['Date', 'Description', 'Amount', 'Source']].head(20),
                    use_container_width=True
                )
                if len(uncategorized) > 20:
                    st.caption(f"Showing first 20 of {len(uncategorized)} uncategorized transactions")
            else:
                st.success("✓ All transactions categorized!")

    # TAB 6: Budgets
    with tab6:
        st.subheader("💾 Budget Targets")
        st.write("Set monthly budget limits for each spending category")

        budgets = load_budgets()

        if not tracker.transaction_db.empty:
            categories = [
                cat for cat in tracker.transaction_db['Category'].unique()
                if cat not in ['Income', 'Other Income', 'UNCATEGORIZED']
            ]

            st.write("Enter your monthly budget for each category:")

            updated_budgets = {}
            cols = st.columns(2)
            for i, category in enumerate(sorted(categories)):
                with cols[i % 2]:
                    current_budget = budgets.get(category, 0)
                    new_budget = st.number_input(
                        category,
                        min_value=0.0,
                        value=float(current_budget),
                        step=50.0,
                        key=f"budget_{category}"
                    )
                    if new_budget > 0:
                        updated_budgets[category] = new_budget

            if st.button("💾 Save Budgets", type="primary", key="save_budgets"):
                save_budgets(updated_budgets)
                st.success("✓ Budgets saved!")
                st.info("Budget alerts will now appear in Live View")
                st.rerun()
        else:
            st.info("Add transactions first to set budgets")

        st.divider()

        if budgets:
            st.write("**Current Budgets**")
            total_budget = sum(budgets.values())
            st.metric("Total Monthly Budget", f"${total_budget:,.2f}")

            budget_df = pd.DataFrame([
                {'Category': cat, 'Budget': amt}
                for cat, amt in sorted(budgets.items(), key=lambda x: x[1], reverse=True)
            ])

            st.dataframe(
                budget_df.style.format({'Budget': '${:,.2f}'}),
                use_container_width=True,
                hide_index=True
            )

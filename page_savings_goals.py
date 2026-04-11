import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta

# Emoji palette organized by category (Teams-style)
# Flags are stored as ("emoji", "label") tuples so we can render them via Twemoji
# on Windows (which doesn't display flag emoji natively).
# Regular emoji categories are plain string lists.

_FLAG_ASIA = [
    ("🇻🇳", "VN"), ("🇯🇵", "JP"), ("🇰🇷", "KR"), ("🇨🇳", "CN"),
    ("🇹🇼", "TW"), ("🇹🇭", "TH"), ("🇵🇭", "PH"), ("🇮🇩", "ID"),
    ("🇲🇾", "MY"), ("🇸🇬", "SG"), ("🇮🇳", "IN"), ("🇵🇰", "PK"),
    ("🇧🇩", "BD"), ("🇱🇰", "LK"), ("🇲🇲", "MM"), ("🇰🇭", "KH"),
    ("🇱🇦", "LA"), ("🇲🇳", "MN"), ("🇳🇵", "NP"), ("🇭🇰", "HK"),
]

_FLAG_EUROPE = [
    ("🇨🇿", "CZ"), ("🇨🇭", "CH"), ("🇬🇧", "GB"), ("🇫🇷", "FR"),
    ("🇩🇪", "DE"), ("🇮🇹", "IT"), ("🇪🇸", "ES"), ("🇵🇹", "PT"),
    ("🇳🇱", "NL"), ("🇧🇪", "BE"), ("🇦🇹", "AT"), ("🇵🇱", "PL"),
    ("🇸🇪", "SE"), ("🇳🇴", "NO"), ("🇩🇰", "DK"), ("🇫🇮", "FI"),
    ("🇮🇪", "IE"), ("🇬🇷", "GR"), ("🇭🇺", "HU"), ("🇷🇴", "RO"),
    ("🇭🇷", "HR"), ("🇷🇸", "RS"), ("🇧🇬", "BG"), ("🇸🇰", "SK"),
    ("🇸🇮", "SI"), ("🇺🇦", "UA"), ("🇱🇹", "LT"), ("🇱🇻", "LV"),
    ("🇪🇪", "EE"), ("🇮🇸", "IS"),
]

_FLAG_AMERICAS = [
    ("🇺🇸", "US"), ("🇨🇦", "CA"), ("🇲🇽", "MX"), ("🇧🇷", "BR"),
    ("🇦🇷", "AR"), ("🇨🇴", "CO"), ("🇨🇱", "CL"), ("🇵🇪", "PE"),
    ("🇨🇺", "CU"), ("🇯🇲", "JM"), ("🇵🇷", "PR"), ("🇨🇷", "CR"),
    ("🇵🇦", "PA"), ("🇪🇨", "EC"), ("🇧🇴", "BO"), ("🇺🇾", "UY"),
    ("🇵🇾", "PY"), ("🇻🇪", "VE"), ("🇬🇹", "GT"), ("🇩🇴", "DO"),
]

_FLAG_OTHER = [
    ("🇦🇺", "AU"), ("🇳🇿", "NZ"), ("🇿🇦", "ZA"), ("🇪🇬", "EG"),
    ("🇳🇬", "NG"), ("🇰🇪", "KE"), ("🇲🇦", "MA"), ("🇬🇭", "GH"),
    ("🇪🇹", "ET"), ("🇹🇿", "TZ"), ("🇸🇦", "SA"), ("🇦🇪", "AE"),
    ("🇮🇱", "IL"), ("🇹🇷", "TR"), ("🇶🇦", "QA"), ("🇯🇴", "JO"),
    ("🇱🇧", "LB"), ("🇺🇳", "UN"),
]

EMOJI_CATEGORIES = {
    "Money": [
        "💰", "💵", "💴", "💶", "💷", "💸", "💳", "🏦", "🪙", "💎", "📈", "📉", "🏧", "🤑",
    ],
    "Goals": [
        "🎯", "🏆", "🥇", "⭐", "🌟", "✨", "🔥", "🚀", "💪", "👑", "🎓", "🎉", "🏅", "📌",
    ],
    "Alerts": [
        "🚨", "⚠️", "🔔", "🔕", "📢", "📣", "🆘", "❗", "❓", "‼️", "⁉️", "🛑",
        "🚩", "🏁", "✅", "❌", "⭕", "🔴", "🟢", "🟡", "🔵", "🟠", "🟣", "⚡",
    ],
    "Globe": [
        "🌍", "🌎", "🌏", "🗺️", "🧭", "🌐",
    ],
    "Travel": [
        "✈️", "🏖️", "🏔️", "🌴", "🧳", "🚗", "🛳️", "🏕️", "🎢", "🌅",
        "🗼", "🗽", "🏰", "⛩️", "🕌", "🛕", "🗻", "🏝️", "🚂", "🚁",
    ],
    "Home": [
        "🏠", "🏡", "🔑", "🛋️", "🏗️", "🧱", "🪴", "🛏️", "🚿", "💡", "🏢", "🪟",
    ],
    "Health": [
        "❤️", "🩺", "💊", "🏃", "🧘", "🍎", "🥗", "💉", "🦷", "👶", "🐾", "🧬",
    ],
    "Tech": [
        "💻", "📱", "🎮", "🖥️", "⌚", "📷", "🎧", "🕹️", "🤖", "📡", "🔋", "💿",
    ],
    "Fun": [
        "🎵", "🎨", "📚", "🎬", "🎸", "🎪", "🎲", "🧩", "🎭", "🎹", "📖", "🎤",
    ],
    "Food": [
        "☕", "🍕", "🍔", "🍣", "🍰", "🍷", "🥂", "🍻", "🧁", "🥑", "🌮", "🍜",
    ],
    "Nature": [
        "🌻", "🌈", "☀️", "🌙", "⛅", "🌊", "🦋", "🐝", "🌸", "🍀", "🌵", "🦜",
    ],
}

# Flag categories stored separately (tuples with country codes for Twemoji rendering)
FLAG_CATEGORIES = {
    "Flags Asia": _FLAG_ASIA,
    "Flags Europe": _FLAG_EUROPE,
    "Flags Americas": _FLAG_AMERICAS,
    "Flags Other": _FLAG_OTHER,
}

# Twemoji CDN base — converts unicode codepoints to PNG URLs
_TWEMOJI_BASE = "https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/72x72"


def _emoji_to_twemoji_url(emoji_char):
    """Convert a unicode emoji to a Twemoji CDN image URL."""
    codepoints = []
    for char in emoji_char:
        cp = ord(char)
        if cp == 0xFE0F:
            continue  # skip variation selector
        codepoints.append(f"{cp:x}")
    return f"{_TWEMOJI_BASE}/{'-'.join(codepoints)}.png"


def _render_twemoji(emoji_char, size=24):
    """Return an <img> tag that renders the emoji via Twemoji."""
    url = _emoji_to_twemoji_url(emoji_char)
    return (
        f'<img src="{url}" alt="{emoji_char}" '
        f'style="width:{size}px;height:{size}px;vertical-align:middle">'
    )


def _emoji_picker(key_prefix, default="💰"):
    """Render a Teams-style emoji picker grid. Returns the selected emoji."""
    session_key = f"{key_prefix}_selected_emoji"
    if session_key not in st.session_state:
        st.session_state[session_key] = default

    current = st.session_state[session_key]
    # Use Twemoji for the large preview so flags render on Windows
    preview_img = _render_twemoji(current, size=48)
    st.markdown(
        f'<div style="text-align:center;padding:8px 0">{preview_img}</div>',
        unsafe_allow_html=True,
    )

    # CSS to make emoji buttons bigger and centered
    st.markdown(
        """<style>
        div[data-testid="stExpander"] button[kind="secondary"] {
            min-height: 48px;
            font-size: 1.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 6px 2px;
        }
        </style>""",
        unsafe_allow_html=True,
    )

    with st.expander("Pick an emoji"):
        all_cat_names = list(EMOJI_CATEGORIES.keys()) + list(FLAG_CATEGORIES.keys())
        selected_cat = st.selectbox(
            "Category",
            all_cat_names,
            key=f"{key_prefix}_emoji_cat",
            label_visibility="collapsed",
        )

        num_cols = 6

        if selected_cat in FLAG_CATEGORIES:
            # Render flags as Twemoji image buttons via HTML grid + real buttons
            flags = FLAG_CATEGORIES[selected_cat]
            for row_start in range(0, len(flags), num_cols):
                row_flags = flags[row_start:row_start + num_cols]
                cols = st.columns(num_cols)
                for j, col in enumerate(cols):
                    idx = row_start + j
                    if idx < len(flags):
                        emoji_char, label = flags[idx]
                        img = _render_twemoji(emoji_char, size=24)
                        with col:
                            if st.button(
                                label,
                                key=f"{key_prefix}_{selected_cat}_{idx}",
                                use_container_width=True,
                                help=f"{img}",
                            ):
                                st.session_state[session_key] = emoji_char
                                st.rerun()
                # Show flag images above the buttons for reference
                imgs_html = ""
                for j, (emoji_char, label) in enumerate(row_flags):
                    img = _render_twemoji(emoji_char, size=30)
                    cell_width = f"{100 / num_cols:.1f}%"
                    imgs_html += (
                        f'<div style="width:{cell_width};text-align:center;display:inline-block">'
                        f'{img}</div>'
                    )
                st.markdown(imgs_html, unsafe_allow_html=True)
        else:
            # Regular emoji — render as normal buttons
            emojis = EMOJI_CATEGORIES[selected_cat]
            for row_start in range(0, len(emojis), num_cols):
                cols = st.columns(num_cols)
                for j, col in enumerate(cols):
                    idx = row_start + j
                    if idx < len(emojis):
                        with col:
                            if st.button(
                                emojis[idx],
                                key=f"{key_prefix}_{selected_cat}_{idx}",
                                use_container_width=True,
                            ):
                                st.session_state[session_key] = emojis[idx]
                                st.rerun()

    return st.session_state[session_key]


def render(savings_goals):
    # Inject Twemoji auto-parse so flag emojis render as images on Windows
    st.markdown(
        '<script src="https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/twemoji.min.js"'
        ' crossorigin="anonymous"></script>'
        '<script>document.addEventListener("DOMContentLoaded",function(){twemoji.parse(document.body,{size:"72x72"})});</script>',
        unsafe_allow_html=True,
    )
    st.title("💰 Savings Goals")

    all_goals = savings_goals.get_all_goals()

    if all_goals:
        col1, col2, col3, col4 = st.columns(4)

        total_target = savings_goals.get_total_savings_target()
        total_saved = savings_goals.get_total_saved()
        progress = (total_saved / total_target * 100) if total_target > 0 else 0

        with col1:
            st.metric("Total Goals", len(all_goals))
        with col2:
            st.metric("Total Target", f"${total_target:,.2f}")
        with col3:
            st.metric("Total Saved", f"${total_saved:,.2f}")
        with col4:
            st.metric("Overall Progress", f"{progress:.1f}%")

        st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(["Active Goals", "Add New Goal", "Contribute", "Allocation Suggestion"])

    # TAB 1: Active Goals
    with tab1:
        if not all_goals:
            st.info("No savings goals yet! Create one in the 'Add New Goal' tab.")
        else:
            for goal in sorted(all_goals, key=lambda x: x['progress_pct'], reverse=True):
                icon = '✅' if goal['status'] == 'completed' else goal.get('emoji', '💰')
                with st.expander(f"{icon} {goal['name']} - {goal['progress_pct']:.1f}%", expanded=(goal['status'] != 'completed')):
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.progress(min(goal['progress_pct'] / 100, 1.0))
                        st.write(f"**Target:** ${goal['target_amount']:,.2f}")
                        st.write(f"**Current:** ${goal['current_amount']:,.2f}")
                        st.write(f"**Remaining:** ${goal['remaining']:,.2f}")
                        st.write(f"**Deadline:** {goal['target_date']} ({goal['days_remaining']} days)")

                        if goal.get('interest_rate', 0) > 0:
                            st.write(f"**Interest Rate:** {goal['interest_rate'] * 100:.2f}% APY 💰")
                            if goal.get('interest_earned', 0) > 0:
                                st.write(f"**Interest Earned:** ${goal['interest_earned']:,.2f}")

                        status_colors = {
                            'completed': '🎉 Completed!',
                            'overdue': '⚠️ Overdue',
                            'urgent': '🔥 Urgent (< 30 days)',
                            'active': '✅ On Track' if goal['on_track'] else '⚠️ Behind Schedule'
                        }
                        st.write(f"**Status:** {status_colors[goal['status']]}")

                    with col2:
                        fig = go.Figure(data=[go.Pie(
                            values=[goal['current_amount'], goal['remaining']],
                            labels=['Saved', 'Remaining'],
                            hole=0.5,
                            marker_colors=['#00D9FF', '#E0E0E0']
                        )])
                        fig.update_layout(showlegend=False, height=200, margin=dict(l=0, r=0, t=0, b=0))
                        st.plotly_chart(fig, width="stretch")

                    if goal['status'] != 'completed':
                        if goal.get('interest_rate', 0) > 0:
                            st.info(f"💡 Save ${goal['monthly_needed']:.2f}/month to reach your goal (with {goal['interest_rate']*100:.1f}% interest helping!)")

                            if st.button("📊 See Projection", key=f"proj_{goal['goal_id']}"):
                                projection = savings_goals.project_with_interest(goal['goal_id'])
                                if projection:
                                    st.write(f"**With {goal['interest_rate']*100:.1f}% APY:**")
                                    st.write(f"- You'll contribute: ${projection['total_contributed']:,.2f}")
                                    st.write(f"- Interest will add: ${projection['total_interest']:,.2f} 💰")
                                    st.write(f"- Total saved: ${projection['final_balance']:,.2f}")
                                    st.success(f"Interest earns you ${projection['total_interest']:,.2f} for free!")
                        else:
                            st.info(f"💡 Save ${goal['monthly_needed']:.2f}/month to reach your goal")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("Edit", key=f"edit_{goal['goal_id']}"):
                            st.session_state[f'editing_{goal["goal_id"]}'] = True
                    with col2:
                        if st.button("Add Contribution", key=f"contrib_{goal['goal_id']}"):
                            st.session_state[f'contributing_{goal["goal_id"]}'] = True
                    with col3:
                        if st.button("🗑️ Delete", key=f"delete_{goal['goal_id']}"):
                            savings_goals.delete_goal(goal['goal_id'])
                            st.success(f"Deleted {goal['name']}")
                            st.rerun()

                    if st.session_state.get(f'editing_{goal["goal_id"]}', False):
                        st.write("**Edit Goal**")
                        edit_key = f"edit_goal_{goal['goal_id']}"
                        edit_emoji_col, edit_form_col = st.columns([1, 3])
                        with edit_emoji_col:
                            new_emoji = _emoji_picker(
                                edit_key,
                                default=goal.get('emoji', '💰'),
                            )
                        with edit_form_col:
                            new_target = st.number_input("Target Amount", value=float(goal['target_amount']), key=f"edit_target_{goal['goal_id']}")
                            new_date = st.date_input("Target Date", value=datetime.strptime(goal['target_date'], '%Y-%m-%d'), key=f"edit_date_{goal['goal_id']}")

                        if st.button("Save Changes", key=f"save_{goal['goal_id']}"):
                            # Read the emoji from session state directly
                            saved_emoji = st.session_state.get(f"{edit_key}_selected_emoji", new_emoji)
                            savings_goals.update_goal(
                                goal['goal_id'],
                                target_amount=new_target,
                                target_date=new_date.strftime('%Y-%m-%d'),
                                emoji=saved_emoji,
                            )
                            # Clean up session state
                            st.session_state.pop(f"{edit_key}_selected_emoji", None)
                            st.session_state[f'editing_{goal["goal_id"]}'] = False
                            st.success("Goal updated!")
                            st.rerun()

                    if st.session_state.get(f'contributing_{goal["goal_id"]}', False):
                        st.write("**Add Contribution**")
                        contrib_amount = st.number_input("Amount", min_value=0.01, key=f"contrib_amt_{goal['goal_id']}")
                        contrib_notes = st.text_input("Notes (optional)", key=f"contrib_notes_{goal['goal_id']}")

                        if st.button("Add", key=f"add_contrib_{goal['goal_id']}"):
                            milestone = savings_goals.add_contribution(goal['goal_id'], contrib_amount, notes=contrib_notes)
                            st.session_state[f'contributing_{goal["goal_id"]}'] = False

                            if milestone:
                                st.balloons()
                                st.success(f"🎉 Milestone reached: {milestone}!")
                            else:
                                st.success(f"Added ${contrib_amount:.2f}!")
                            st.rerun()

    # TAB 2: Add New Goal
    with tab2:
        st.subheader("Create New Savings Goal")

        st.markdown("**Goal Icon**")
        selected_emoji = _emoji_picker("new_goal")

        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            goal_name = st.text_input("Goal Name", placeholder="e.g., Emergency Fund, Europe Trip")
            target_amount = st.number_input("Target Amount ($)", min_value=1.0, value=1000.0, step=100.0)
            target_date = st.date_input("Target Date", value=datetime.now() + timedelta(days=365))

        with col2:
            category = st.selectbox("Category", ["emergency", "vacation", "house", "car", "education", "wedding", "general"])
            priority = st.selectbox("Priority", ["high", "medium", "low"])
            current_amount = st.number_input("Current Amount (if any)", min_value=0.0, value=0.0)
            interest_rate = st.number_input(
                "Interest Rate (% APY)",
                min_value=0.0, max_value=20.0, value=0.0, step=0.1,
                help="Enter interest rate for HYSA, savings accounts, or investment accounts"
            )

        notes = st.text_area("Notes (optional)")

        if st.button("Create Goal", type="primary"):
            if goal_name:
                # Read emoji from session state in case it was picked then form submitted
                final_emoji = st.session_state.get("new_goal_selected_emoji", selected_emoji)
                goal_id = savings_goals.add_goal(
                    goal_name, target_amount, target_date.strftime('%Y-%m-%d'),
                    category, current_amount, priority, notes,
                    interest_rate / 100, emoji=final_emoji
                )
                st.success(f"✓ Created goal: {goal_name}")
                summary = savings_goals.get_goal_summary(goal_id)
                if interest_rate > 0:
                    st.info(f"💡 With {interest_rate:.1f}% APY, you'll need to save ${summary['monthly_needed']:.2f}/month (interest helps!)")
                else:
                    st.info(f"💡 You'll need to save ${summary['monthly_needed']:.2f}/month to reach your goal")
                st.rerun()
            else:
                st.error("Please enter a goal name")

    # TAB 3: Quick Contribute
    with tab3:
        st.subheader("Add Contribution")

        if not all_goals:
            st.info("Create a goal first!")
        else:
            goal_options = {goal['name']: goal['goal_id'] for goal in all_goals if goal['status'] != 'completed'}

            if not goal_options:
                st.success("🎉 All goals completed!")
            else:
                selected_goal_name = st.selectbox("Select Goal", list(goal_options.keys()))
                selected_goal_id = goal_options[selected_goal_name]

                amount = st.number_input("Contribution Amount ($)", min_value=0.01, value=50.0, step=10.0)
                contrib_date = st.date_input("Date", value=datetime.now())
                contrib_notes = st.text_input("Notes (optional)")

                if st.button("Add Contribution", type="primary"):
                    milestone = savings_goals.add_contribution(
                        selected_goal_id, amount,
                        contrib_date.strftime('%Y-%m-%d'), contrib_notes
                    )

                    if milestone:
                        st.balloons()
                        st.success(f"🎉 Milestone reached: {milestone}!")
                    else:
                        st.success(f"✓ Added ${amount:.2f} to {selected_goal_name}")

                    summary = savings_goals.get_goal_summary(selected_goal_id)
                    st.info(f"Progress: {summary['progress_pct']:.1f}% - ${summary['current_amount']:,.2f} / ${summary['target_amount']:,.2f}")
                    st.rerun()

    # TAB 4: Allocation Suggestion
    with tab4:
        st.subheader("Smart Allocation Suggestion")

        if not all_goals:
            st.info("Create goals first to get allocation suggestions!")
        else:
            st.write("Enter how much you can save monthly, and we'll suggest how to allocate it across your goals based on priority and urgency.")

            monthly_budget = st.number_input("Monthly Savings Budget ($)", min_value=0.0, value=500.0, step=50.0)

            if st.button("Get Suggestion"):
                allocations = savings_goals.suggest_allocation(monthly_budget)

                st.write("### 💡 Suggested Allocation")

                data = []
                for goal_id, amount in allocations.items():
                    goal = savings_goals.goals[goal_id]
                    data.append({
                        'Goal': goal['name'],
                        'Suggested': amount,
                        'Needed': goal['monthly_contribution_needed'],
                        'Priority': goal['priority']
                    })

                df = pd.DataFrame(data)

                fig = px.bar(
                    df, x='Goal', y=['Suggested', 'Needed'],
                    barmode='group',
                    title="Suggested vs Needed Monthly Contributions"
                )
                st.plotly_chart(fig, width="stretch")

                st.dataframe(
                    df.style.format({'Suggested': '${:,.2f}', 'Needed': '${:,.2f}'}),
                    width="stretch"
                )

                total_allocated = df['Suggested'].sum()
                if total_allocated < monthly_budget:
                    st.success(f"💰 Surplus: ${monthly_budget - total_allocated:.2f} available for additional savings or other goals")
                elif total_allocated == monthly_budget:
                    st.info(f"✅ Perfect! Full budget allocated: ${total_allocated:.2f}")
                else:
                    st.warning(f"⚠️ Goals need ${total_allocated:.2f}/month but budget is ${monthly_budget:.2f}")

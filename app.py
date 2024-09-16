import streamlit as st
import pandas as pd
import math
import altair as alt

tiers = ["Bronze", "Iron", "Steel", "Mithril", "Adamant", "Rune", "Dragon"]

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = False

def initialize_state():
    if not st.session_state.initialized:
        st.session_state.interaction_xp = 10
        st.session_state.base_timer = 2.4
        st.session_state.base_lvl = 10
        st.session_state.amounts = {tier: 0 for tier in tiers}
        st.session_state.initialized = True

def format_time(seconds):
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, remainder = divmod(remainder, 60)
    return f"{int(days)}d {int(hours)}h {int(minutes)}m {int(remainder)}s"

def calculate_xp_for_level(level):
    if level < 2:
        return 0
    return math.floor(1 / 4 * (level - 1 + 300 * 2 ** ((level - 1) / 7)))

def calculate_total_xp(level):
    return sum(calculate_xp_for_level(l) for l in range(2, level + 1))

def calculate_level(xp):
    if xp == 0:
        return 1
    left, right = 1, 99
    while left <= right:
        mid = (left + right) // 2
        mid_xp = calculate_total_xp(mid)
        if mid_xp == xp:
            return mid
        elif mid_xp < xp:
            left = mid + 1
        else:
            right = mid - 1
    return left - 1

st.title("Advanced Skilling Boosts Timer Calculator")

initialize_state()

try:
    col_xp, col_time, col_lvl = st.columns(3)

    with col_xp:
        st.session_state.interaction_xp = st.number_input("Base XP per interaction:", value=st.session_state.interaction_xp, min_value=1)
    with col_time:
        st.session_state.base_timer = st.number_input("Base seconds per action:", value=st.session_state.base_timer, min_value=0.6, step=0.1)
    with col_lvl:
        st.session_state.base_lvl = st.number_input("Base Level for resource:", value=st.session_state.base_lvl, min_value=1, max_value=99)
        base_xp = calculate_total_xp(st.session_state.base_lvl)
        st.metric("Base XP", f"{base_xp:.0f}")

    boosts = {
        "Bronze": 1, "Iron": 1.1, "Steel": 1.2, "Mithril": 1.4,
        "Adamant": 1.7, "Rune": 2, "Dragon": 3
    }

    st.subheader("Enter the amount for each tier:")

    col1, col2, col3, col4, col5 = st.columns(5)
    columns = [col1, col2, col3, col4, col5]

    for i, tier in enumerate(tiers):
        with columns[i % 5]:
            st.session_state.amounts[tier] = st.number_input(
                f"{tier}",
                value=st.session_state.amounts[tier],
                min_value=0,
                max_value=10000 if tier != "Dragon" else None,
                key=f"input_{tier}"
            )

    total_xp = sum(st.session_state.amounts[tier] * st.session_state.interaction_xp for tier in tiers) + base_xp
    total_level = calculate_level(total_xp)

    st.subheader("Results:")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Level", f"{total_level:.2f}")
    with col2:
        st.metric("Total XP", f"{total_xp:.0f}")
    with col3:
        total_time = sum(st.session_state.amounts[tier] * st.session_state.base_timer / boosts[tier] for tier in tiers)
        st.metric("Total Time", format_time(total_time))

    if st.button("Calculate"):
        st.success(f"Calculation complete! Total XP: {total_xp:.0f}, Total Level: {total_level:.2f}, Total Time: {format_time(total_time)}")

    st.subheader("Boost Breakdown:")
    breakdown = pd.DataFrame({
        "Tier to hit": tiers,
        "Amount": [st.session_state.amounts[tier] for tier in tiers],
        "Boost Multiplier": [boosts[tier] for tier in tiers],
        "Time per Action (s)": [st.session_state.base_timer / boosts[tier] for tier in tiers],
        "Total Time (s)": [st.session_state.amounts[tier] * st.session_state.base_timer / boosts[tier] for tier in tiers],
        "XP per Action": [st.session_state.interaction_xp for tier in tiers],
        "Total XP Contribution": [st.session_state.amounts[tier] * st.session_state.interaction_xp for tier in tiers]
    })

    cumulative_xp = base_xp
    cumulative_time = 0.0
    breakdown["Cumulative XP"] = base_xp
    breakdown["Cumulative Level"] = float(st.session_state.base_lvl)
    breakdown["Cumulative Time"] = 0.0

    for i, row in breakdown.iterrows():
        cumulative_xp += row["Total XP Contribution"]
        cumulative_time += row["Total Time (s)"]
        breakdown.at[i, "Cumulative XP"] = cumulative_xp
        breakdown.at[i, "Cumulative Level"] = calculate_level(cumulative_xp)
        breakdown.at[i, "Cumulative Time"] = cumulative_time

    breakdown["Formatted Cumulative Time"] = breakdown["Cumulative Time"].apply(format_time)

    st.dataframe(breakdown)

    st.subheader("Time Progression Chart:")
    chart_data = pd.DataFrame({
        "Tier": tiers,
        "Cumulative Time (s)": breakdown["Cumulative Time"].apply(format_time),
        "Cumulative XP": breakdown["Cumulative XP"],
        "Cumulative Level": breakdown["Cumulative Level"]
    })

    time_chart = alt.Chart(chart_data).mark_line(point=True).encode(
        x=alt.X('Tier', sort=alt.EncodingSortField(field="Cumulative Time (s)", op="sum", order="ascending")),
        y='Cumulative Time (s)',
        tooltip=['Tier', 'Cumulative Time (s)', 'Cumulative XP', 'Cumulative Level']
    ).properties(title="Time Progression by Tier (Sorted by Time)")

    st.altair_chart(time_chart, use_container_width=True)

except Exception as e:
    st.error(f"An error occurred: {str(e)}. Please try refreshing the page.")

st.write("The level is calculated based on the cumulative XP using the game's level-up formula.")
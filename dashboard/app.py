"""Interactive dashboard for the marketing campaign EDA.

Run it from the repo root:

    streamlit run dashboard/app.py
"""

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Streamlit puts dashboard/ on the import path, not the repo root, so add the root to reuse src/
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from plotly.subplots import make_subplots  # noqa: E402

from src.dashboard_data import (  # noqa: E402
    decile_budget_summary,
    dimension_gaps,
    evaluate_rule,
    filter_campaigns,
    group_summary,
    kpi_summary,
    split_half_medians,
)
from src.holidays import load_us_holidays  # noqa: E402
from src.pipeline import HOLIDAYS_PATH, RAW_PATH, build_dataset  # noqa: E402

# Same colours as the notebook and the executive report
PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#0d366b", "#d55181", "#008300", "#4a3aa7", "#e34948"]
BLUE, ORANGE, GREEN, RED = PALETTE[0], PALETTE[1], PALETTE[5], PALETTE[7]
LIGHT_GRAY, GRAY = "#c3c2b7", "#6b6a63"
GRID = "rgba(128,128,128,0.2)"
DIMENSIONS = {
    "Customer_Segment": "Customer segment",
    "Target_Audience": "Target audience",
    "Location": "City",
    "Language": "Language",
}
MIN_CAMPAIGNS = 100  # below this, medians and deciles are too noisy to show
MIN_COMBINATIONS = 25  # one channel or one audience filter leaves 25; fewer makes the ranking check meaningless

st.set_page_config(page_title="Marketing Campaign Performance", page_icon="📊", layout="wide")


@st.cache_data(show_spinner="Loading and cleaning 200,000 campaigns...")
def load_data() -> pd.DataFrame:
    """Build the clean dataset with the same pipeline as the notebook.

    It starts from the raw CSV in the repo, so the app does not depend on the
    processed file (which is not committed). The cache runs it only once.
    """
    raw = pd.read_csv(RAW_PATH)
    holidays = load_us_holidays(2021, HOLIDAYS_PATH)
    return build_dataset(raw, holidays)


df = load_data()

# Colour follows the channel, not its rank, so filtering never repaints the bars
CHANNELS = sorted(df["Channel_Used"].unique())
CHANNEL_COLORS = dict(zip(CHANNELS, PALETTE))

# ---------- Sidebar filters ----------
st.sidebar.header("Filters")
st.sidebar.caption("Leave a filter empty to include every value.")
channels = st.sidebar.multiselect("Channel", CHANNELS)
audiences = st.sidebar.multiselect("Target audience", sorted(df["Target_Audience"].unique()))
cities = st.sidebar.multiselect("City", sorted(df["Location"].unique()))
spend_min, spend_max = float(df["Acquisition_Cost"].min()), float(df["Acquisition_Cost"].max())
spend_range = st.sidebar.slider(
    "Campaign budget (USD)", spend_min, spend_max, (spend_min, spend_max), step=100.0, format="$%.0f"
)

filtered = filter_campaigns(df, channels=channels, audiences=audiences, cities=cities, spend_range=spend_range)

# ---------- Header ----------
st.title("Where does the advertising budget go?")
st.markdown(
    "Results of **200,000 synthetic marketing campaigns** (Kaggle, 2021). "
    "Use the filters on the left to explore any channel, audience, city or budget range."
)

if len(filtered) < MIN_CAMPAIGNS:
    st.warning(f"Only {len(filtered):,} campaigns match these filters. Widen them to see the analysis.")
    st.stop()

# ---------- KPI row ----------
kpis = kpi_summary(filtered)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Campaigns", f"{kpis['campaigns']:,}")
col2.metric("Total budget", f"${kpis['spend'] / 1e6:,.1f} M")
col3.metric("Conversions", f"{kpis['conversions'] / 1e6:,.2f} M")
col4.metric("Median cost per conversion", f"${kpis['median_cost_per_conversion']:,.1f}")

# ---------- Budget leak ----------
st.header("1. The budget leak")
col1, col2, col3 = st.columns(3)
col1.metric("High-cost campaigns", f"{kpis['high_cost_campaign_share']:.1f}% of campaigns")
col2.metric("Budget they take", f"{kpis['high_cost_spend_share']:.1f}% of budget")
col3.metric("Conversions they bring", f"{kpis['high_cost_conversion_share']:.1f}% of conversions")

deciles = decile_budget_summary(filtered)
labels = [f"D{d}" for d in deciles.index]
fig = go.Figure()
fig.add_bar(
    x=labels, y=deciles["Spend_Share"], name="Share of budget", marker_color=ORANGE,
    hovertemplate="%{x}: %{y:.1f}% of budget<extra></extra>",
)
fig.add_bar(
    x=labels, y=deciles["Conversion_Share"], name="Share of conversions", marker_color=BLUE,
    hovertemplate="%{x}: %{y:.1f}% of conversions<extra></extra>",
)
fig.update_layout(
    title="Budget vs conversions by decile of cost per conversion",
    xaxis_title="Decile (D1 = 10% cheapest campaigns per conversion, D10 = 10% most expensive)",
    yaxis_title="Share of total (%)",
    barmode="group", bargap=0.25, bargroupgap=0.05,
    legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="right", x=1),
    margin=dict(t=80),
)
fig.update_yaxes(rangemode="tozero", gridcolor="rgba(128,128,128,0.2)")
st.plotly_chart(fig)

d1, d10 = deciles.loc[1], deciles.loc[10]
st.caption(
    f"**Reading:** the 10% cheapest campaigns use {d1['Spend_Share']:.1f}% of the budget and bring "
    f"{d1['Conversion_Share']:.1f}% of the conversions; the 10% most expensive use {d10['Spend_Share']:.1f}% "
    f"and bring {d10['Conversion_Share']:.1f}%. High-cost campaigns are the IQR outliers of cost per "
    "conversion, flagged on the full dataset."
)

# ---------- Channels ----------
st.header("2. Does the channel matter?")
by_channel = group_summary(filtered, "Channel_Used").sort_values("Median_Cost_per_Conversion", ascending=False)
fig = go.Figure(
    go.Bar(
        x=by_channel["Median_Cost_per_Conversion"], y=by_channel.index, orientation="h",
        marker_color=[CHANNEL_COLORS[c] for c in by_channel.index],
        customdata=by_channel[["Campaigns", "High_Cost_Share"]],
        hovertemplate=(
            "<b>%{y}</b><br>Median cost per conversion: $%{x:.1f}<br>"
            "Campaigns: %{customdata[0]:,}<br>High-cost campaigns: %{customdata[1]:.1f}%<extra></extra>"
        ),
    )
)
fig.update_layout(
    title="Median cost per conversion by channel",
    xaxis_title="Median cost per conversion (USD)", yaxis_title=None, showlegend=False,
)
fig.update_xaxes(rangemode="tozero", gridcolor="rgba(128,128,128,0.2)")
st.plotly_chart(fig)

cheapest, priciest = by_channel.index[-1], by_channel.index[0]
low, high = by_channel["Median_Cost_per_Conversion"].min(), by_channel["Median_Cost_per_Conversion"].max()
st.caption(
    f"**Reading:** the median goes from ${low:,.1f} ({cheapest}) to ${high:,.1f} ({priciest}), "
    f"a gap of {(high - low) / low * 100:.1f}%. On the full dataset the Kruskal-Wallis test finds no real "
    "difference between channels (notebook section 4.1)."
)

# ---------- Audiences ----------
st.header("3. Does the audience matter?")
# A dimension needs at least two groups to compare (a filter can leave only one)
dims = [d for d in DIMENSIONS if filtered[d].nunique() >= 2]
gaps = dimension_gaps(filtered, dims)
overall_median = filtered["Cost_per_Conversion"].median()
x_limit = max(5.0, gaps["Gap"].abs().max() * 1.25)

fig = make_subplots(
    rows=2, cols=2, horizontal_spacing=0.18, vertical_spacing=0.14,
    subplot_titles=[f"{DIMENSIONS[d]} · p = {gaps.loc[gaps['Dimension'] == d, 'p_value'].iloc[0]:.2f}" for d in dims],
)
for i, dimension in enumerate(dims):
    part = gaps[gaps["Dimension"] == dimension].sort_values("Gap", ascending=False)
    fig.add_bar(
        x=part["Gap"], y=part["Group"], orientation="h", marker_color=PALETTE[i],
        customdata=part["Median_Cost_per_Conversion"],
        hovertemplate="<b>%{y}</b><br>Median: $%{customdata:.1f}<br>Gap: %{x:+.1f} USD<extra></extra>",
        row=i // 2 + 1, col=i % 2 + 1,
    )
fig.update_xaxes(range=[-x_limit, x_limit], zeroline=True, zerolinecolor=GRAY, gridcolor=GRID)
fig.update_layout(
    title=f"Gap to the overall median cost per conversion (${overall_median:,.1f})",
    showlegend=False, height=620, margin=dict(t=110),
)
fig.add_annotation(
    text="USD per conversion, left = cheaper than the median", xref="paper", yref="paper",
    x=0.5, y=-0.08, showarrow=False, font=dict(color=GRAY),
)
st.plotly_chart(fig)

largest = gaps.loc[gaps["Gap"].abs().idxmax()]
significant = gaps.groupby("Dimension")["p_value"].first().lt(0.05).sum()
st.caption(
    f"**Reading:** the largest gap is {largest['Gap']:+.1f} USD ({largest['Group']}), "
    f"{abs(largest['Gap']) / overall_median:.1%} of the median. "
    f"{significant} of {len(dims)} dimensions show a difference with p < 0.05 (Kruskal-Wallis test)."
)

# ---------- Combinations ----------
st.header("4. Is there a winning formula?")
st.markdown(
    "Each point is one **channel | campaign type | audience** combination. The campaigns are split at random "
    "into two halves. If a combination were really better, it would be cheap in both halves and the points "
    "would sit on the diagonal."
)
halves = split_half_medians(filtered)
if len(halves) < MIN_COMBINATIONS:
    st.info(
        f"These filters leave {len(halves)} combinations. Comparing rankings needs at least {MIN_COMBINATIONS}: "
        "keep at most one of the channel and audience filters to see this chart."
    )
else:
    # Top 10 on the full data; with fewer combinations, the cheapest 20% so the top stays a small group
    top_n = min(10, len(halves) // 5)
    best_a = halves.nsmallest(top_n, "Half_A").index
    best_b = halves.nsmallest(top_n, "Half_B").index
    winner, loser = halves["Median_All"].idxmin(), halves["Median_All"].idxmax()
    others = halves.index.difference(best_a.union(best_b).union([winner, loser]))
    hover = "<b>%{text}</b><br>Half A: $%{x:.1f}<br>Half B: $%{y:.1f}<extra></extra>"

    fig = go.Figure()
    groups = [
        (others, LIGHT_GRAY, 7, "Other combinations"),
        (best_a.difference([winner, loser]), BLUE, 10, f"{top_n} cheapest in half A"),
        (best_b.difference([winner, loser]), ORANGE, 10, f"{top_n} cheapest in half B"),
        ([winner], GREEN, 14, f"Apparent winner: {winner}"),
        ([loser], RED, 14, f"Apparent loser: {loser}"),
    ]
    for index, color, size, name in groups:
        part = halves.loc[list(index)]
        fig.add_scatter(
            x=part["Half_A"], y=part["Half_B"], mode="markers", name=name, text=part.index,
            marker=dict(color=color, size=size, line=dict(color="white", width=1)), hovertemplate=hover,
        )
    low = min(halves["Half_A"].min(), halves["Half_B"].min()) * 0.97
    high = max(halves["Half_A"].max(), halves["Half_B"].max()) * 1.03
    fig.add_scatter(
        x=[low, high], y=[low, high], mode="lines", name="Same cost in both halves",
        line=dict(color=GRAY, dash="dash", width=1.5), hoverinfo="skip",
    )
    fig.update_layout(
        title="Median cost per conversion of each combination in two random halves",
        xaxis_title="Half A: median cost per conversion (USD)",
        yaxis_title="Half B: median cost per conversion (USD)",
        height=620, legend=dict(orientation="h", yanchor="top", y=-0.15),
    )
    fig.update_xaxes(range=[low, high], gridcolor=GRID)
    fig.update_yaxes(range=[low, high], gridcolor=GRID, scaleanchor="x")
    st.plotly_chart(fig)

    n = len(halves)
    in_common = len(set(best_a) & set(best_b))
    agreement = halves["Half_A"].corr(halves["Half_B"], method="spearman")
    # 0.3 is a common cut-off for a weak correlation; below it the two rankings do not agree
    verdict = (
        "The ranking does not repeat from one half to the other, so it reflects chance, not a winning formula."
        if agreement < 0.3
        else "The two rankings partly agree: worth checking with new data before acting on it."
    )
    st.caption(
        f"**Reading:** the agreement between the two rankings is {agreement:.3f} "
        f"(Spearman; 1 = same order, 0 = no relation) and {in_common} of the {top_n} cheapest combinations repeat. "
        f"The apparent winner ranks {halves.loc[winner, 'Rank_A']} and {halves.loc[winner, 'Rank_B']} of {n} "
        f"in the two halves; the apparent loser ranks {halves.loc[loser, 'Rank_A']} and {halves.loc[loser, 'Rank_B']}. "
        f"{verdict}"
    )

# ---------- Alert rule ----------
st.header("5. Can a simple rule spot the expensive campaigns?")
st.markdown(
    "High-cost campaigns convert badly. Choose a **conversion rate threshold**: every campaign at or below it "
    "is flagged, and the cards show how well that rule picks out the high-cost campaigns."
)
threshold = st.slider("Flag campaigns with a conversion rate of at most", 0.01, 0.10, 0.02, step=0.01, format="%.2f")
rule = evaluate_rule(filtered, filtered["Conversion_Rate"] <= threshold + 1e-9)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Campaigns flagged", f"{rule['campaigns_flagged']:.1f}%")
col2.metric("High-cost campaigns caught", f"{rule['high_cost_caught']:.1f}%")
col3.metric("Flagged that are high-cost", f"{rule['precision']:.1f}%")
col4.metric("Budget in flagged campaigns", f"{rule['budget_flagged']:.1f}%")

table = pd.DataFrame(
    {f"≤ {t:.0%}": evaluate_rule(filtered, filtered["Conversion_Rate"] <= t + 1e-9) for t in (0.01, 0.02, 0.03)}
).T.rename(
    columns={
        "campaigns_flagged": "Campaigns flagged (%)",
        "high_cost_caught": "High-cost caught (%)",
        "precision": "Flagged that are high-cost (%)",
        "budget_flagged": "Budget flagged (%)",
    }
)
table.index.name = "Conversion rate"
st.dataframe(table.round(1))
st.caption(
    "**Reading:** a stricter threshold flags fewer campaigns and is right more often, but misses more of the "
    "expensive ones. This rule uses the **final** conversion rate: the dataset has only end-of-campaign results, "
    "so whether the signal shows up early enough to act on is a hypothesis to test with a pilot that records "
    "conversion during the first week."
)

with st.expander("About the data"):
    st.markdown(
        "- Synthetic dataset: the original columns were generated independently, so most comparisons are flat.\n"
        "- Cost per conversion = budget / (clicks × conversion rate). Budget is assumed to be the total spend in USD.\n"
        "- No retention data and no daily results: the dataset only has the final result of each campaign.\n"
        "- Full analysis and data quality report: `notebooks/01_eda_marketing_campaigns.ipynb`."
    )

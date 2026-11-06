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

from src.dashboard_data import decile_budget_summary, filter_campaigns, group_summary, kpi_summary  # noqa: E402
from src.holidays import load_us_holidays  # noqa: E402
from src.pipeline import HOLIDAYS_PATH, RAW_PATH, build_dataset  # noqa: E402

# Same colours as the notebook and the executive report
PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#0d366b", "#d55181", "#008300", "#4a3aa7", "#e34948"]
BLUE, ORANGE = PALETTE[0], PALETTE[1]
MIN_CAMPAIGNS = 100  # below this, medians and deciles are too noisy to show

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

with st.expander("About the data"):
    st.markdown(
        "- Synthetic dataset: the original columns were generated independently, so most comparisons are flat.\n"
        "- Cost per conversion = budget / (clicks × conversion rate). Budget is assumed to be the total spend in USD.\n"
        "- No retention data and no daily results: the dataset only has the final result of each campaign.\n"
        "- Full analysis and data quality report: `notebooks/01_eda_marketing_campaigns.ipynb`."
    )

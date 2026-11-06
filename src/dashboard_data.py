"""Calculations behind the Streamlit dashboard.

The app only draws; every number it shows comes from these functions, so the
logic can be tested with pytest and matches the notebook.
"""

import pandas as pd


def filter_campaigns(
    df: pd.DataFrame,
    channels: list[str] | None = None,
    audiences: list[str] | None = None,
    cities: list[str] | None = None,
    spend_range: tuple[float, float] | None = None,
) -> pd.DataFrame:
    """Keep the campaigns that match the selected filters.

    An empty or missing selection means "no filter" for that column, so
    clearing a filter in the app shows every campaign instead of none.
    The spend range includes both ends.
    """
    mask = pd.Series(True, index=df.index)
    for column, selected in [("Channel_Used", channels), ("Target_Audience", audiences), ("Location", cities)]:
        if selected:
            mask &= df[column].isin(selected)
    if spend_range is not None:
        low, high = spend_range
        mask &= df["Acquisition_Cost"].between(low, high)
    return df[mask]


def kpi_summary(df: pd.DataFrame) -> dict:
    """Headline numbers: totals and how much the high-cost campaigns take."""
    spend = df["Acquisition_Cost"].sum()
    conversions = df["Conversions"].sum()
    high_cost = df[df["High_Cost_Outlier"]]
    return {
        "campaigns": len(df),
        "spend": spend,
        "conversions": conversions,
        "median_cost_per_conversion": df["Cost_per_Conversion"].median(),
        "high_cost_campaign_share": len(high_cost) / len(df) * 100 if len(df) else 0.0,
        "high_cost_spend_share": high_cost["Acquisition_Cost"].sum() / spend * 100 if spend else 0.0,
        "high_cost_conversion_share": high_cost["Conversions"].sum() / conversions * 100 if conversions else 0.0,
    }


def decile_budget_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Share of budget and of conversions in each decile of cost per conversion.

    Decile 1 holds the 10% of campaigns with the lowest cost per conversion,
    decile 10 the 10% with the highest. Same calculation as notebook section 4.6.
    """
    decile = pd.qcut(df["Cost_per_Conversion"], 10, labels=range(1, 11))
    deciles = df.groupby(decile, observed=True).agg(
        Spend=("Acquisition_Cost", "sum"), Conversions=("Conversions", "sum")
    )
    deciles["Spend_Share"] = deciles["Spend"] / df["Acquisition_Cost"].sum() * 100
    deciles["Conversion_Share"] = deciles["Conversions"] / df["Conversions"].sum() * 100
    deciles.index = deciles.index.astype(int)
    deciles.index.name = "Decile"
    return deciles


def group_summary(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    """Campaigns, median cost per conversion and % of high-cost campaigns per group.

    Sorted from the cheapest to the most expensive median cost per conversion.
    """
    summary = df.groupby(group_col).agg(
        Campaigns=("Cost_per_Conversion", "size"),
        Median_Cost_per_Conversion=("Cost_per_Conversion", "median"),
        High_Cost_Share=("High_Cost_Outlier", lambda s: s.mean() * 100),
    )
    return summary.sort_values("Median_Cost_per_Conversion")

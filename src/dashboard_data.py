"""Calculations behind the Streamlit dashboard.

The app only draws; every number it shows comes from these functions, so the
logic can be tested with pytest and matches the notebook.
"""

import numpy as np
import pandas as pd

from src.significance import compare_groups

COMBINATION_KEYS = ["Channel_Used", "Campaign_Type", "Target_Audience"]


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


def dimension_gaps(df: pd.DataFrame, dimensions: list[str]) -> pd.DataFrame:
    """Gap of each group's median cost per conversion to the overall median.

    Negative gap = cheaper than the overall median. Each row also carries the
    Kruskal-Wallis p-value of its dimension, to tell a real gap from noise.
    """
    overall_median = df["Cost_per_Conversion"].median()
    parts = []
    for dimension in dimensions:
        medians = df.groupby(dimension)["Cost_per_Conversion"].median()
        p_value = compare_groups(df, dimension, ["Cost_per_Conversion"]).loc["Cost_per_Conversion", "p_value"]
        parts.append(
            pd.DataFrame(
                {
                    "Dimension": dimension,
                    "Group": medians.index.astype(str),
                    "Median_Cost_per_Conversion": medians.to_numpy(),
                    "Gap": medians.to_numpy() - overall_median,
                    "p_value": p_value,
                }
            )
        )
    return pd.concat(parts, ignore_index=True)


def split_half_medians(df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """Median cost per conversion of each channel | type | audience combination in two random halves.

    If a ranking of combinations were real, the best ones in half A would also
    be the best in half B. Same split as notebook section 4.6 (seed 42).
    Rank 1 = cheapest. Median_All is the median on all rows, which is what a
    plain ranking table would show.
    """
    combination = df[COMBINATION_KEYS[0]].astype(str)
    for key in COMBINATION_KEYS[1:]:
        combination = combination + " | " + df[key].astype(str)

    rng = np.random.default_rng(seed)
    in_half_a = rng.random(len(df)) < 0.5
    cost = df["Cost_per_Conversion"]
    halves = pd.DataFrame(
        {
            "Half_A": cost[in_half_a].groupby(combination[in_half_a]).median(),
            "Half_B": cost[~in_half_a].groupby(combination[~in_half_a]).median(),
            "Median_All": cost.groupby(combination).median(),
        }
    ).dropna()
    halves["Rank_A"] = halves["Half_A"].rank().astype(int)
    halves["Rank_B"] = halves["Half_B"].rank().astype(int)
    halves.index.name = "Combination"
    return halves


def evaluate_rule(df: pd.DataFrame, flagged: pd.Series) -> dict:
    """How well a rule (True = flagged campaign) picks out the high-cost campaigns.

    - campaigns_flagged: % of campaigns the rule marks
    - high_cost_caught: % of high-cost campaigns it marks (coverage)
    - precision: % of marked campaigns that really are high-cost
    - budget_flagged: % of the budget that sits in marked campaigns
    """
    flagged = pd.Series(flagged.to_numpy(), index=df.index)
    high = df["High_Cost_Outlier"]
    hits = (flagged & high).sum()
    n_flagged, n_high, spend = flagged.sum(), high.sum(), df["Acquisition_Cost"].sum()
    return {
        "campaigns_flagged": n_flagged / len(df) * 100 if len(df) else 0.0,
        "high_cost_caught": hits / n_high * 100 if n_high else 0.0,
        "precision": hits / n_flagged * 100 if n_flagged else 0.0,
        "budget_flagged": df.loc[flagged, "Acquisition_Cost"].sum() / spend * 100 if spend else 0.0,
    }

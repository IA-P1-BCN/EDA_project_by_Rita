"""Derived metrics (feature engineering) for the cleaned campaign data.

Assumptions, because the dataset does not define them:
- Conversion_Rate is conversions / clicks (the usual marketing definition).
- Acquisition_Cost is the total spend of the campaign, in USD.
"""

import pandas as pd


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of the cleaned data with the derived metrics added.

    - CTR: clicks / impressions
    - Conversions: clicks * conversion rate (estimated number of customers)
    - CPC: cost per click (USD)
    - Cost_per_Conversion: cost per acquired customer (USD)
    - CPM: cost per 1,000 impressions (USD), to compare reach costs fairly
    - Month and Weekday: taken from Date, for seasonality
    """
    out = df.copy()
    out["CTR"] = out["Clicks"] / out["Impressions"]
    out["Conversions"] = out["Clicks"] * out["Conversion_Rate"]
    out["CPC"] = out["Acquisition_Cost"] / out["Clicks"]
    out["Cost_per_Conversion"] = out["Acquisition_Cost"] / out["Conversions"]
    out["CPM"] = out["Acquisition_Cost"] / out["Impressions"] * 1000
    out["Month"] = out["Date"].dt.month
    out["Weekday"] = out["Date"].dt.day_name()
    return out

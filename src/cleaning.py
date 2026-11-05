"""Reusable cleaning functions for the marketing campaign dataset.

The notebook and the pipeline import these functions, so the cleaning
logic lives in one place and is covered by tests in tests/test_cleaning.py.
"""

import pandas as pd


def parse_currency(values: pd.Series) -> pd.Series:
    """Convert text like "$16,174.00" into the float 16174.0."""
    return (
        values.str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .astype("float64")
    )


def parse_duration_days(values: pd.Series) -> pd.Series:
    """Convert text like "30 days" into the integer 30."""
    return values.str.extract(r"(\d+)", expand=False).astype("int64")


def clean_campaigns(df: pd.DataFrame) -> pd.DataFrame:
    """Return a cleaned copy of the raw campaign data.

    - Acquisition_Cost: text with "$" and commas -> float (USD)
    - Duration: text like "30 days" -> integer, renamed to Duration_days
    - Date: text "YYYY-MM-DD" -> datetime
    The original DataFrame is not modified.
    """
    clean = df.copy()
    clean["Acquisition_Cost"] = parse_currency(clean["Acquisition_Cost"])
    clean["Duration"] = parse_duration_days(clean["Duration"])
    clean = clean.rename(columns={"Duration": "Duration_days"})
    clean["Date"] = pd.to_datetime(clean["Date"], format="%Y-%m-%d")
    return clean

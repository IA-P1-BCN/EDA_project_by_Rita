"""Tests for the cleaning functions in src/cleaning.py.

Each test builds a tiny example with the same format as the real CSV,
runs one cleaning function and checks the result.
"""

import pandas as pd

from src.cleaning import clean_campaigns, parse_currency, parse_duration_days


def test_parse_currency_removes_symbol_and_commas():
    raw = pd.Series(["$16,174.00", "$8,168.00", "$500.50"])
    result = parse_currency(raw)
    assert result.tolist() == [16174.0, 8168.0, 500.5]


def test_parse_currency_returns_float():
    result = parse_currency(pd.Series(["$1,000.00"]))
    assert result.dtype == "float64"


def test_parse_duration_days_extracts_number():
    raw = pd.Series(["15 days", "30 days", "60 days"])
    result = parse_duration_days(raw)
    assert result.tolist() == [15, 30, 60]


def test_parse_duration_days_returns_integer():
    result = parse_duration_days(pd.Series(["45 days"]))
    assert result.dtype == "int64"


def make_raw_campaigns():
    """Two rows with the same text formats as the original CSV."""
    return pd.DataFrame(
        {
            "Campaign_ID": [1, 2],
            "Duration": ["30 days", "15 days"],
            "Acquisition_Cost": ["$16,174.00", "$11,566.00"],
            "Date": ["2021-01-01", "2021-12-31"],
        }
    )


def test_clean_campaigns_converts_types():
    clean = clean_campaigns(make_raw_campaigns())
    assert clean["Acquisition_Cost"].dtype == "float64"
    assert clean["Duration_days"].dtype == "int64"
    assert pd.api.types.is_datetime64_any_dtype(clean["Date"])


def test_clean_campaigns_renames_duration():
    clean = clean_campaigns(make_raw_campaigns())
    assert "Duration_days" in clean.columns
    assert "Duration" not in clean.columns


def test_clean_campaigns_does_not_modify_original():
    raw = make_raw_campaigns()
    clean_campaigns(raw)
    assert raw["Acquisition_Cost"].tolist() == ["$16,174.00", "$11,566.00"]
    assert "Duration" in raw.columns

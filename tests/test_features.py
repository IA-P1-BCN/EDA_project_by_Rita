"""Tests for the derived metrics in src/features.py."""

import pandas as pd
import pytest

from src.features import add_features


def make_clean_campaigns():
    """One clean row with easy numbers, so the expected results are obvious."""
    return pd.DataFrame(
        {
            "Clicks": [500],
            "Impressions": [2000],
            "Conversion_Rate": [0.10],
            "Acquisition_Cost": [10000.0],
            "Date": pd.to_datetime(["2021-03-15"]),  # a Monday
        }
    )


def test_ctr_is_clicks_over_impressions():
    result = add_features(make_clean_campaigns())
    assert result["CTR"].iloc[0] == pytest.approx(0.25)  # 500 / 2000


def test_conversions_are_clicks_times_conversion_rate():
    result = add_features(make_clean_campaigns())
    assert result["Conversions"].iloc[0] == pytest.approx(50)  # 500 * 0.10


def test_cpc_is_cost_over_clicks():
    result = add_features(make_clean_campaigns())
    assert result["CPC"].iloc[0] == pytest.approx(20)  # 10000 / 500


def test_cost_per_conversion_is_cost_over_conversions():
    result = add_features(make_clean_campaigns())
    assert result["Cost_per_Conversion"].iloc[0] == pytest.approx(200)  # 10000 / 50


def test_cpm_is_cost_per_thousand_impressions():
    result = add_features(make_clean_campaigns())
    assert result["CPM"].iloc[0] == pytest.approx(5000)  # 10000 / 2000 * 1000


def test_month_and_weekday_come_from_date():
    result = add_features(make_clean_campaigns())
    assert result["Month"].iloc[0] == 3
    assert result["Weekday"].iloc[0] == "Monday"


def test_add_features_does_not_modify_original():
    clean = make_clean_campaigns()
    add_features(clean)
    assert "CTR" not in clean.columns

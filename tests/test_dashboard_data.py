"""Tests for the dashboard calculations, written before the functions (TDD)."""

import pandas as pd
import pytest

from src.dashboard_data import decile_budget_summary, filter_campaigns, group_summary, kpi_summary


@pytest.fixture
def campaigns():
    """Small dataset: 10 campaigns with known spend, conversions and flags."""
    return pd.DataFrame(
        {
            "Channel_Used": ["Email", "Email", "YouTube", "YouTube", "Website"] * 2,
            "Target_Audience": ["All Ages", "Men 18-24"] * 5,
            "Location": ["Chicago"] * 5 + ["Miami"] * 5,
            "Acquisition_Cost": [100.0, 200.0, 300.0, 400.0, 500.0, 600.0, 700.0, 800.0, 900.0, 1000.0],
            "Conversions": [10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 1.0],
            "Cost_per_Conversion": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 1000.0],
            "High_Cost_Outlier": [False] * 9 + [True],
        }
    )


def test_filter_campaigns_keeps_only_selected_values(campaigns):
    result = filter_campaigns(campaigns, channels=["Email"], cities=["Chicago"])
    assert len(result) == 2
    assert set(result["Channel_Used"]) == {"Email"}
    assert set(result["Location"]) == {"Chicago"}


def test_filter_campaigns_empty_selection_means_no_filter(campaigns):
    assert len(filter_campaigns(campaigns, channels=[], audiences=None)) == len(campaigns)


def test_filter_campaigns_spend_range_is_inclusive(campaigns):
    result = filter_campaigns(campaigns, spend_range=(200.0, 400.0))
    assert result["Acquisition_Cost"].tolist() == [200.0, 300.0, 400.0]


def test_kpi_summary_totals_and_high_cost_shares(campaigns):
    kpis = kpi_summary(campaigns)
    assert kpis["campaigns"] == 10
    assert kpis["spend"] == 5500.0
    assert kpis["conversions"] == 91.0
    assert kpis["median_cost_per_conversion"] == 55.0
    assert kpis["high_cost_campaign_share"] == pytest.approx(10.0)
    assert kpis["high_cost_spend_share"] == pytest.approx(1000 / 5500 * 100)
    assert kpis["high_cost_conversion_share"] == pytest.approx(1 / 91 * 100)


def test_kpi_summary_handles_empty_data(campaigns):
    kpis = kpi_summary(campaigns.iloc[0:0])
    assert kpis["campaigns"] == 0
    assert kpis["high_cost_spend_share"] == 0.0


def test_decile_budget_summary_shares_add_up_to_100(campaigns):
    deciles = decile_budget_summary(campaigns)
    assert len(deciles) == 10
    assert deciles["Spend_Share"].sum() == pytest.approx(100.0)
    assert deciles["Conversion_Share"].sum() == pytest.approx(100.0)
    # The most expensive decile holds the 1,000 USD campaign with 1 conversion
    assert deciles.loc[10, "Spend_Share"] == pytest.approx(1000 / 5500 * 100)
    assert deciles.loc[10, "Conversion_Share"] == pytest.approx(1 / 91 * 100)


def test_group_summary_sorted_by_median_cost(campaigns):
    summary = group_summary(campaigns, "Channel_Used")
    assert list(summary.index) == ["Email", "YouTube", "Website"]
    assert summary.loc["Email", "Campaigns"] == 4
    assert summary.loc["Website", "High_Cost_Share"] == pytest.approx(50.0)

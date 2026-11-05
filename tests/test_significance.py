"""Tests for the group comparison helper in src/significance.py."""

import numpy as np
import pandas as pd

from src.significance import compare_groups


def make_groups(shift_b):
    """Two groups of 200 values; group B is moved up by `shift_b`."""
    rng = np.random.default_rng(42)
    return pd.DataFrame(
        {
            "group": ["A"] * 200 + ["B"] * 200,
            "metric": np.concatenate([rng.normal(0, 1, 200), rng.normal(shift_b, 1, 200)]),
        }
    )


def test_compare_groups_detects_a_real_difference():
    result = compare_groups(make_groups(shift_b=2), "group", ["metric"])
    row = result.loc["metric"]
    assert row["p_value"] < 0.05
    assert bool(row["significant"]) is True


def test_compare_groups_finds_no_difference_between_equal_groups():
    result = compare_groups(make_groups(shift_b=0), "group", ["metric"])
    row = result.loc["metric"]
    assert row["p_value"] >= 0.05
    assert bool(row["significant"]) is False


def test_compare_groups_returns_one_row_per_metric():
    df = make_groups(shift_b=0)
    df["other"] = df["metric"] * 2
    result = compare_groups(df, "group", ["metric", "other"])
    assert result.index.tolist() == ["metric", "other"]
    assert {"H", "p_value", "epsilon_squared", "significant"} <= set(result.columns)


def test_effect_size_is_larger_for_a_bigger_difference():
    small = compare_groups(make_groups(shift_b=0.3), "group", ["metric"]).loc["metric", "epsilon_squared"]
    large = compare_groups(make_groups(shift_b=2), "group", ["metric"]).loc["metric", "epsilon_squared"]
    assert large > small

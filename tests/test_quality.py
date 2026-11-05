"""Tests for the outlier helpers in src/quality.py."""

import pandas as pd
import pytest

from src.quality import flag_outliers_iqr, iqr_bounds


def test_iqr_bounds_on_simple_values():
    # Q1 = 20, Q3 = 40, IQR = 20 -> bounds are 20 - 30 and 40 + 30
    low, high = iqr_bounds(pd.Series([10, 20, 30, 40, 50]))
    assert low == pytest.approx(-10)
    assert high == pytest.approx(70)


def test_iqr_bounds_with_custom_multiplier():
    # Same quartiles, but 3 * IQR = 60
    low, high = iqr_bounds(pd.Series([10, 20, 30, 40, 50]), k=3)
    assert low == pytest.approx(-40)
    assert high == pytest.approx(100)


def test_flag_outliers_iqr_marks_only_extreme_values():
    values = pd.Series([10, 20, 30, 40, 50, 1000])
    flags = flag_outliers_iqr(values)
    assert flags.tolist() == [False, False, False, False, False, True]


def test_flag_outliers_iqr_returns_booleans_with_same_index():
    values = pd.Series([10, 20, 30, 40, 50], index=[5, 6, 7, 8, 9])
    flags = flag_outliers_iqr(values)
    assert flags.dtype == bool
    assert flags.index.tolist() == [5, 6, 7, 8, 9]

"""Data quality helpers: outlier detection with the IQR rule."""

import pandas as pd


def iqr_bounds(values: pd.Series, k: float = 1.5) -> tuple[float, float]:
    """Return the (low, high) limits of the IQR rule.

    IQR = Q3 - Q1. A value is an outlier if it is below Q1 - k * IQR
    or above Q3 + k * IQR. The usual choice is k = 1.5.
    """
    q1 = values.quantile(0.25)
    q3 = values.quantile(0.75)
    iqr = q3 - q1
    return q1 - k * iqr, q3 + k * iqr


def flag_outliers_iqr(values: pd.Series, k: float = 1.5) -> pd.Series:
    """Return True for each value outside the IQR limits, False otherwise."""
    low, high = iqr_bounds(values, k)
    return (values < low) | (values > high)

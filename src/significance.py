"""Statistical comparison of groups with the Kruskal-Wallis test.

Kruskal-Wallis compares groups using ranks instead of raw values, so it does
not assume normal data and is not distorted by outliers. With 200,000 rows
even tiny differences can be "significant", so the effect size (epsilon
squared) is reported too: about 0.01 is small, 0.08 moderate, 0.26 large.
"""

import pandas as pd
from scipy import stats


def compare_groups(df: pd.DataFrame, group_col: str, metrics: list[str], alpha: float = 0.05) -> pd.DataFrame:
    """Run a Kruskal-Wallis test for each metric across the groups in `group_col`.

    Returns one row per metric with the H statistic, the p-value, the effect
    size (epsilon squared) and whether the difference is significant.
    """
    n = len(df)
    k = df[group_col].nunique()
    rows = []
    for metric in metrics:
        samples = [values.to_numpy() for _, values in df.groupby(group_col)[metric]]
        h, p_value = stats.kruskal(*samples)
        rows.append(
            {
                "metric": metric,
                "H": h,
                "p_value": p_value,
                "epsilon_squared": max((h - k + 1) / (n - k), 0.0),
                "significant": p_value < alpha,
            }
        )
    return pd.DataFrame(rows).set_index("metric")

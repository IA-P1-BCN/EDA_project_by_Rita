"""Reproducible data pipeline: raw CSV -> processed CSV in one command.

Run it from the repo root:

    python -m src.pipeline

Steps: load raw data, fix types, add derived metrics, flag high-cost
outliers, add US federal holidays, and save the result.
"""

from pathlib import Path

import pandas as pd

from src.cleaning import clean_campaigns
from src.features import add_features
from src.holidays import add_holiday_flag, load_us_holidays
from src.quality import flag_outliers_iqr

ROOT = Path(__file__).resolve().parent.parent
RAW_PATH = ROOT / "data" / "marketing_campaign_dataset.csv"
HOLIDAYS_PATH = ROOT / "data" / "us_holidays_2021.csv"
OUTPUT_PATH = ROOT / "data" / "processed" / "campaigns_clean.csv"


def build_dataset(raw: pd.DataFrame, holidays: pd.DataFrame) -> pd.DataFrame:
    """Apply every processing step, in order, to the raw campaign data."""
    df = clean_campaigns(raw)
    df = add_features(df)
    df["High_Cost_Outlier"] = flag_outliers_iqr(df["Cost_per_Conversion"])
    df = add_holiday_flag(df, holidays)
    return df


def run_pipeline(raw_path=RAW_PATH, holidays_path=HOLIDAYS_PATH, output_path=OUTPUT_PATH) -> pd.DataFrame:
    """Load the inputs, build the dataset and save it as CSV."""
    raw = pd.read_csv(raw_path)
    holidays = load_us_holidays(2021, holidays_path)
    df = build_dataset(raw, holidays)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    return df


if __name__ == "__main__":
    result = run_pipeline()
    print(f"Saved {len(result):,} rows and {result.shape[1]} columns to {OUTPUT_PATH.relative_to(ROOT)}")

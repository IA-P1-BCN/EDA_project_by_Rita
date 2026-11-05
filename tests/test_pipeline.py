"""Tests for the end-to-end pipeline in src/pipeline.py.

They use a tiny raw CSV in a temporary folder and a holidays file that
already exists, so no network call is made.
"""

import pandas as pd

from src.pipeline import build_dataset, run_pipeline

RAW_CSV = """Campaign_ID,Company,Campaign_Type,Target_Audience,Duration,Channel_Used,Conversion_Rate,Acquisition_Cost,ROI,Location,Language,Clicks,Impressions,Engagement_Score,Customer_Segment,Date
1,TechCorp,Email,Men 18-24,30 days,Google Ads,0.10,"$10,000.00",5.0,Chicago,Spanish,500,2000,6,Foodies,2021-01-01
2,TechCorp,Search,All Ages,15 days,YouTube,0.05,"$8,000.00",4.0,Miami,English,200,4000,3,Foodies,2021-01-02
"""

HOLIDAYS_CSV = """Date,Holiday_Name
2021-01-01,New Year's Day
"""


def write_inputs(tmp_path):
    raw_path = tmp_path / "raw.csv"
    holidays_path = tmp_path / "holidays.csv"
    raw_path.write_text(RAW_CSV)
    holidays_path.write_text(HOLIDAYS_CSV)
    return raw_path, holidays_path


def test_build_dataset_adds_all_processing_steps(tmp_path):
    raw_path, holidays_path = write_inputs(tmp_path)
    raw = pd.read_csv(raw_path)
    holidays = pd.read_csv(holidays_path, parse_dates=["Date"])

    result = build_dataset(raw, holidays)

    # One column from each step: cleaning, features, outliers, holidays
    for col in ["Duration_days", "Cost_per_Conversion", "High_Cost_Outlier", "Is_Holiday"]:
        assert col in result.columns
    assert len(result) == 2
    assert result["Is_Holiday"].tolist() == [True, False]


def test_run_pipeline_writes_the_processed_file(tmp_path):
    raw_path, holidays_path = write_inputs(tmp_path)
    out_path = tmp_path / "processed" / "campaigns_clean.csv"

    run_pipeline(raw_path, holidays_path, out_path)

    assert out_path.exists()
    saved = pd.read_csv(out_path)
    assert len(saved) == 2
    assert saved["Acquisition_Cost"].tolist() == [10000.0, 8000.0]

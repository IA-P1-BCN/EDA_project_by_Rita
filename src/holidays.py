"""Second data source: US public holidays from the Nager.Date API.

API docs: https://date.nager.at/Api
Only federal holidays ("global": true) are kept, because the campaigns run
in 5 cities of 5 different states and state-only holidays do not apply to all.
"""

from pathlib import Path

import pandas as pd
import requests

API_URL = "https://date.nager.at/api/v3/PublicHolidays/{year}/US"


def parse_holidays(api_response: list[dict]) -> pd.DataFrame:
    """Turn the API JSON into a table with one row per federal holiday date."""
    holidays = pd.DataFrame(api_response)
    holidays = holidays[holidays["global"]]
    holidays = holidays.rename(columns={"date": "Date", "name": "Holiday_Name"})
    holidays["Date"] = pd.to_datetime(holidays["Date"], format="%Y-%m-%d")
    # One row per date, otherwise the merge would duplicate campaigns
    holidays = holidays.drop_duplicates(subset="Date")
    return holidays[["Date", "Holiday_Name"]].reset_index(drop=True)


def fetch_us_holidays(year: int, get=requests.get) -> pd.DataFrame:
    """Download the US public holidays of one year from the API.

    `get` is requests.get by default; the tests pass a fake one.
    """
    response = get(API_URL.format(year=year), timeout=10)
    response.raise_for_status()
    return parse_holidays(response.json())


def load_us_holidays(year: int, cache_path: Path, get=requests.get) -> pd.DataFrame:
    """Read the holidays from a local CSV, downloading them first if it does not exist."""
    cache_path = Path(cache_path)
    if not cache_path.exists():
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        fetch_us_holidays(year, get=get).to_csv(cache_path, index=False)
    return pd.read_csv(cache_path, parse_dates=["Date"])


def add_holiday_flag(df: pd.DataFrame, holidays: pd.DataFrame) -> pd.DataFrame:
    """Add Is_Holiday and Holiday_Name to each campaign, matching on Date.

    A left merge keeps every campaign exactly once; dates that are not a
    holiday get Holiday_Name "None".
    """
    out = df.merge(holidays, on="Date", how="left", validate="many_to_one")
    out["Is_Holiday"] = out["Holiday_Name"].notna()
    out["Holiday_Name"] = out["Holiday_Name"].fillna("None")
    return out

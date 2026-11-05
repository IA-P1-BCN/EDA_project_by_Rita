"""Tests for the holiday helpers in src/holidays.py.

The API is never called here: the tests use a small fake response with the
same format as https://date.nager.at, so they run offline and always give
the same result.
"""

import pandas as pd

from src.holidays import add_holiday_flag, fetch_us_holidays, load_us_holidays, parse_holidays

FAKE_API_RESPONSE = [
    {"date": "2021-01-01", "name": "New Year's Day", "global": True},
    {"date": "2021-02-12", "name": "Lincoln's Birthday", "global": False},
    {"date": "2021-10-11", "name": "Columbus Day", "global": False},
    {"date": "2021-10-11", "name": "Columbus Day", "global": True},
    {"date": "2021-10-11", "name": "Indigenous Peoples' Day", "global": False},
]


def test_parse_holidays_keeps_only_federal_holidays():
    holidays = parse_holidays(FAKE_API_RESPONSE)
    assert holidays["Holiday_Name"].tolist() == ["New Year's Day", "Columbus Day"]


def test_parse_holidays_has_one_row_per_date():
    holidays = parse_holidays(FAKE_API_RESPONSE)
    assert holidays["Date"].is_unique


def test_parse_holidays_returns_datetime_dates():
    holidays = parse_holidays(FAKE_API_RESPONSE)
    assert pd.api.types.is_datetime64_any_dtype(holidays["Date"])


class FakeResponse:
    """Minimal stand-in for requests.Response."""

    def raise_for_status(self):
        pass

    def json(self):
        return FAKE_API_RESPONSE


def test_fetch_us_holidays_calls_the_right_url():
    called_urls = []

    def fake_get(url, timeout):
        called_urls.append(url)
        return FakeResponse()

    holidays = fetch_us_holidays(2021, get=fake_get)
    assert called_urls == ["https://date.nager.at/api/v3/PublicHolidays/2021/US"]
    assert len(holidays) == 2


def test_load_us_holidays_downloads_once_then_reads_the_cache(tmp_path):
    cache = tmp_path / "holidays.csv"
    calls = []

    def fake_get(url, timeout):
        calls.append(url)
        return FakeResponse()

    first = load_us_holidays(2021, cache, get=fake_get)
    second = load_us_holidays(2021, cache, get=fake_get)

    assert len(calls) == 1  # the second call used the CSV, not the API
    assert cache.exists()
    assert second["Date"].tolist() == first["Date"].tolist()


def make_campaigns():
    return pd.DataFrame(
        {
            "Campaign_ID": [1, 2, 3],
            "Date": pd.to_datetime(["2021-01-01", "2021-01-02", "2021-10-11"]),
        }
    )


def test_add_holiday_flag_keeps_every_campaign_once():
    holidays = parse_holidays(FAKE_API_RESPONSE)
    result = add_holiday_flag(make_campaigns(), holidays)
    assert len(result) == 3
    assert result["Campaign_ID"].tolist() == [1, 2, 3]


def test_add_holiday_flag_marks_holiday_dates():
    holidays = parse_holidays(FAKE_API_RESPONSE)
    result = add_holiday_flag(make_campaigns(), holidays)
    assert result["Is_Holiday"].tolist() == [True, False, True]
    assert result["Holiday_Name"].tolist() == ["New Year's Day", "None", "Columbus Day"]

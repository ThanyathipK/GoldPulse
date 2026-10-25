import pandas as pd

from goldpulse.cleaning import clean_records, daily_close
from goldpulse.forecast import evaluate_and_forecast


def test_clean_rejects_invalid_and_deduplicates():
    base = {"announcement_date": "2025-01-02", "announcement_time": "10:00", "announcement_round": 1, "bar_buy": 42000, "bar_sell": 42100, "ornament_buy": 41000, "ornament_sell": 42600, "gold_spot_usd_oz": 2600, "usd_thb": 34, "source_url": "x", "collected_at": "2025-01-02T03:00:00Z", "data_status": "observed"}
    duplicate = dict(base, bar_sell=42200, collected_at="2025-01-02T04:00:00Z")
    invalid = dict(base, announcement_round=2, bar_sell=41000)
    valid, rejected = clean_records(pd.DataFrame([base, duplicate, invalid]))
    assert len(valid) == 1 and valid.iloc[0].bar_sell == 42200
    assert len(rejected) == 1


def test_forecast_is_time_ordered():
    dates = pd.bdate_range("2025-01-01", periods=60)
    daily = pd.DataFrame({"announcement_date": dates, "value": range(40000, 40060)})
    result = evaluate_and_forecast(daily)
    assert result.comparison.date.is_monotonic_increasing
    assert len(result.future) == 3
    assert set(result.metrics.model) == {"Naive last value", "Ridge autoregression"}


def test_official_2026_monthly_data_is_distinct_and_complete():
    monthly = pd.read_csv("data/official_2026_monthly.csv", parse_dates=["month"])
    assert monthly.month.dt.year.eq(2026).all()
    assert monthly.month.is_monotonic_increasing
    assert len(monthly) == 9
    assert monthly.data_status.eq("official_monthly_average").all()
    assert monthly.source_url.str.contains("goldtraders.or.th", regex=False).all()


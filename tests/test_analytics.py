import pandas as pd

from goldpulse.analytics import (
    cost_average_weight,
    filter_events,
    monthly_summary,
    period_stats,
    unrealized_difference,
)
from goldpulse.insights import period_insight


def series(values):
    return pd.DataFrame({
        "announcement_date": pd.date_range("2026-01-01", periods=len(values), freq="MS"),
        "value": values,
    })


def test_all_negative_period_never_calls_a_decrease_an_increase():
    data = series([100.0, 90.0, 80.0])
    text = period_insight(data, period_stats(data), "Gold bar · Selling", True, "Official.")
    assert "No month-to-month increase was observed" in text
    assert "largest month-to-month decrease" in text
    assert "fell ฿20" in text


def test_single_month_has_no_movement_claim():
    data = series([100.0])
    stats = period_stats(data)
    text = period_insight(data, stats, "Gold bar · Selling", True, "Official.")
    assert stats.changes.dropna().empty
    assert "Only one valid observation" in text


def test_monthly_summary_preserves_missing_months():
    data = pd.DataFrame({
        "announcement_date": pd.to_datetime(["2026-01-01", "2026-03-01"]),
        "value": [100.0, 120.0],
    })
    result = monthly_summary(data, monthly_resolution=True)
    assert result.Month.dt.month.tolist() == [1, 3]
    assert len(result) == 2


def test_event_filter_is_inclusive():
    events = pd.DataFrame({
        "date": pd.to_datetime(["2026-01-01", "2026-02-01", "2026-03-01"]),
        "title": ["a", "b", "c"],
    })
    result = filter_events(events, "2026-02-01", "2026-03-01")
    assert result.title.tolist() == ["b", "c"]


def test_calculators_require_inputs_and_apply_documented_formulas():
    assert cost_average_weight(0, 12, 50_000) is None
    assert cost_average_weight(5_000, 12, 50_000) == 1.2
    assert unrealized_difference(55_000, 0, 1) is None
    assert unrealized_difference(55_000, 50_000, 2) == 10_000


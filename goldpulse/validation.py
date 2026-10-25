"""Validation rules for official monthly-average datasets."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


OFFICIAL_PRICE_COLUMNS = ("bar_buy", "bar_sell", "ornament_buy", "ornament_sell")
OPTIONAL_REFERENCE_COLUMNS = ("gold_spot_usd_oz", "usd_thb")


@dataclass(frozen=True)
class ValidationReport:
    row_count: int
    first_month: str
    last_month: str


def validate_official_monthly(frame: pd.DataFrame) -> ValidationReport:
    """Validate monthly resolution and basic market-data invariants.

    The function deliberately does not fill gaps or synthesize observations.
    """
    required = {
        "month", *OFFICIAL_PRICE_COLUMNS, *OPTIONAL_REFERENCE_COLUMNS,
        "source_url", "accessed_at", "data_status",
    }
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    if frame.empty:
        raise ValueError("Official monthly dataset is empty")

    months = pd.to_datetime(frame["month"], errors="coerce", utc=False)
    if months.isna().any():
        raise ValueError("month contains invalid dates")
    if not months.dt.is_month_start.all():
        raise ValueError("month values must be the first calendar day of each month")
    periods = months.dt.to_period("M")
    if periods.duplicated().any():
        raise ValueError("month must contain one observation per month")
    if not months.is_monotonic_increasing:
        raise ValueError("months must be sorted in increasing order")

    numeric_columns = (*OFFICIAL_PRICE_COLUMNS, *OPTIONAL_REFERENCE_COLUMNS)
    numeric = frame.loc[:, numeric_columns].apply(pd.to_numeric, errors="coerce")
    if numeric.isna().any().any() or numeric.le(0).any().any():
        raise ValueError("price and reference fields must be positive numbers")
    if (numeric["bar_sell"] < numeric["bar_buy"]).any():
        raise ValueError("bar_sell cannot be below bar_buy")
    if (numeric["ornament_sell"] < numeric["ornament_buy"]).any():
        raise ValueError("ornament_sell cannot be below ornament_buy")
    if not frame["data_status"].eq("official_monthly_average").all():
        raise ValueError("data_status must be official_monthly_average")
    if frame["source_url"].isna().any() or frame["source_url"].eq("").any():
        raise ValueError("source_url is required for every row")
    if pd.to_datetime(frame["accessed_at"], errors="coerce", utc=True).isna().any():
        raise ValueError("accessed_at must contain valid timestamps")

    return ValidationReport(
        row_count=len(frame),
        first_month=periods.iloc[0].strftime("%Y-%m"),
        last_month=periods.iloc[-1].strftime("%Y-%m"),
    )

from __future__ import annotations

import pandas as pd

from .schema import PRICE_COLUMNS, REQUIRED_COLUMNS


def clean_records(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (valid, rejected) without silently imputing missing prices."""
    data = frame.copy()
    for column in REQUIRED_COLUMNS:
        if column not in data:
            data[column] = pd.NA

    data["announcement_date"] = pd.to_datetime(
        data["announcement_date"], errors="coerce"
    ).dt.date
    parsed_time = pd.to_datetime(data["announcement_time"], format="%H:%M", errors="coerce")
    data["announcement_time"] = parsed_time.dt.strftime("%H:%M")
    data["announcement_round"] = pd.to_numeric(
        data["announcement_round"], errors="coerce"
    ).astype("Int64")

    numeric = PRICE_COLUMNS + ["gold_spot_usd_oz", "usd_thb"]
    for column in numeric:
        data[column] = pd.to_numeric(
            data[column].astype(str).str.replace(",", "", regex=False), errors="coerce"
        )
    data["collected_at"] = pd.to_datetime(data["collected_at"], errors="coerce", utc=True)

    key = ["announcement_date", "announcement_time", "announcement_round"]
    malformed = (
        data["announcement_date"].isna()
        | data["announcement_time"].isna()
        | data["announcement_round"].isna()
        | data["bar_buy"].isna()
        | data["bar_sell"].isna()
        | (data["bar_buy"] <= 0)
        | (data["bar_sell"] < data["bar_buy"])
    )
    rejected = data.loc[malformed].copy()
    rejected["rejection_reason"] = "missing or invalid required price/key"
    valid = data.loc[~malformed].copy()
    valid = valid.sort_values("collected_at").drop_duplicates(key, keep="last")
    return valid[REQUIRED_COLUMNS].sort_values(key).reset_index(drop=True), rejected


def daily_close(frame: pd.DataFrame, column: str = "bar_sell") -> pd.DataFrame:
    ordered = frame.assign(
        timestamp=pd.to_datetime(
            frame["announcement_date"].astype(str) + " " + frame["announcement_time"]
        )
    ).sort_values("timestamp")
    daily = ordered.groupby("announcement_date", as_index=False).agg(
        value=(column, "last"),
        open=(column, "first"),
        high=(column, "max"),
        low=(column, "min"),
        announcements=("announcement_round", "nunique"),
    )
    daily["announcement_date"] = pd.to_datetime(daily["announcement_date"])
    daily["change"] = daily["value"].diff()
    daily["change_pct"] = daily["value"].pct_change() * 100
    return daily


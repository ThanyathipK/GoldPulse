from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from .schema import REQUIRED_COLUMNS


def initialize(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS gold_prices (
              announcement_date TEXT NOT NULL,
              announcement_time TEXT NOT NULL,
              announcement_round INTEGER NOT NULL,
              bar_buy REAL, bar_sell REAL, ornament_buy REAL, ornament_sell REAL,
              gold_spot_usd_oz REAL, usd_thb REAL,
              source_url TEXT NOT NULL, collected_at TEXT NOT NULL,
              data_status TEXT NOT NULL,
              PRIMARY KEY (announcement_date, announcement_time, announcement_round)
            )
        """)


def upsert(frame: pd.DataFrame, path: str | Path) -> int:
    initialize(path)
    rows = frame[REQUIRED_COLUMNS].copy()
    rows["announcement_date"] = rows["announcement_date"].astype(str)
    rows["collected_at"] = rows["collected_at"].astype(str)
    placeholders = ",".join("?" for _ in REQUIRED_COLUMNS)
    updates = ",".join(f"{c}=excluded.{c}" for c in REQUIRED_COLUMNS[3:])
    sql = f"INSERT INTO gold_prices ({','.join(REQUIRED_COLUMNS)}) VALUES ({placeholders}) ON CONFLICT(announcement_date, announcement_time, announcement_round) DO UPDATE SET {updates}"
    with sqlite3.connect(path) as connection:
        connection.executemany(sql, rows.itertuples(index=False, name=None))
    return len(rows)


def load(path: str | Path) -> pd.DataFrame:
    with sqlite3.connect(path) as connection:
        return pd.read_sql_query(
            "SELECT * FROM gold_prices ORDER BY announcement_date, announcement_time",
            connection,
            parse_dates=["announcement_date", "collected_at"],
        )


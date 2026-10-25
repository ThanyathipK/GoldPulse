from __future__ import annotations

REQUIRED_COLUMNS = [
    "announcement_date", "announcement_time", "announcement_round",
    "bar_buy", "bar_sell", "ornament_buy", "ornament_sell",
    "gold_spot_usd_oz", "usd_thb", "source_url", "collected_at",
    "data_status",
]

PRICE_COLUMNS = ["bar_buy", "bar_sell", "ornament_buy", "ornament_sell"]

UNITS = {
    "bar_buy": "THB per baht-weight (96.5%)",
    "bar_sell": "THB per baht-weight (96.5%)",
    "ornament_buy": "THB per baht-weight (96.5%)",
    "ornament_sell": "THB per baht-weight (96.5%)",
    "gold_spot_usd_oz": "USD per troy ounce",
    "usd_thb": "THB per USD",
}


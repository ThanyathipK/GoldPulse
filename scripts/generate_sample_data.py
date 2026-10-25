"""Generate reproducible synthetic data for offline review; not market observations."""
from pathlib import Path

import numpy as np
import pandas as pd

OUTPUT = Path(__file__).parents[1] / "data" / "sample_gold_prices.csv"
rng = np.random.default_rng(42)
days = pd.bdate_range("2025-01-02", periods=260)
rows = []
price = 43_000.0
for day_index, day in enumerate(days):
    price += 22 + 180 * np.sin(day_index / 18) + rng.normal(0, 115)
    rounds = int(rng.integers(2, 7))
    spot = 2630 + day_index * 1.8 + 55 * np.sin(day_index / 22) + rng.normal(0, 8)
    fx = 34.2 - day_index * 0.003 + 0.45 * np.sin(day_index / 30) + rng.normal(0, .05)
    for round_no in range(1, rounds + 1):
        intraday = rng.choice([-100, -50, 0, 50, 100])
        bar_sell = round((price + intraday) / 50) * 50
        hour, minute = 9 + round_no, int(rng.integers(0, 60))
        rows.append({
            "announcement_date": day.date().isoformat(),
            "announcement_time": f"{hour:02d}:{minute:02d}",
            "announcement_round": round_no,
            "bar_buy": bar_sell - 100,
            "bar_sell": bar_sell,
            "ornament_buy": round((bar_sell - 850) / 10) * 10,
            "ornament_sell": bar_sell + 500,
            "gold_spot_usd_oz": round(spot + rng.normal(0, 3), 2),
            "usd_thb": round(fx + rng.normal(0, .02), 4),
            "source_url": "synthetic://goldpulse-demo",
            "collected_at": "2026-01-15T00:00:00Z",
            "data_status": "synthetic_demo",
        })
pd.DataFrame(rows).to_csv(OUTPUT, index=False)
print(f"Wrote {len(rows)} rows to {OUTPUT}")


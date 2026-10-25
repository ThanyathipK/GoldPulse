"""Pure analytical transformations used by the dashboard."""
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class PeriodStats:
    first: pd.Series
    latest: pd.Series
    changes: pd.Series
    change: float
    change_pct: float
    typical_move: float


def period_stats(series: pd.DataFrame) -> PeriodStats:
    """Calculate selection-level statistics without inventing observations."""
    first, latest = series.iloc[0], series.iloc[-1]
    changes = series["value"].diff()
    change = float(latest.value - first.value)
    pct = change / float(first.value) * 100 if first.value else float("nan")
    valid = changes.dropna()
    typical = float(valid.abs().mean()) if not valid.empty else float("nan")
    return PeriodStats(first, latest, changes, change, pct, typical)


def monthly_summary(series: pd.DataFrame, monthly_resolution: bool) -> pd.DataFrame:
    if monthly_resolution:
        result = series[["announcement_date", "value"]].rename(
            columns={"announcement_date": "Month", "value": "Average"}
        )
        result["Change"] = result["Average"].diff()
        result["Change (%)"] = result["Average"].pct_change() * 100
        return result
    result = (series.set_index("announcement_date").value.resample("ME")
              .agg(Open="first", Close="last", High="max", Low="min")
              .dropna().reset_index(names="Month"))
    result["Change (%)"] = (result.Close / result.Open - 1) * 100
    return result


def filter_events(events: pd.DataFrame, start, end) -> pd.DataFrame:
    """Return context events inside an inclusive selected period."""
    dates = pd.to_datetime(events["date"], errors="coerce")
    return events.loc[dates.between(pd.Timestamp(start), pd.Timestamp(end))].copy()


def cost_average_weight(budget: float, purchases: int, price: float) -> float | None:
    """Return accumulated baht-weight, or None until all inputs are positive."""
    if budget <= 0 or purchases <= 0 or price <= 0:
        return None
    return budget * purchases / price


def unrealized_difference(market_price: float, purchase_price: float,
                          weight: float) -> float | None:
    """Return simple price difference before fees, or None for empty inputs."""
    if market_price <= 0 or purchase_price <= 0 or weight <= 0:
        return None
    return (market_price - purchase_price) * weight


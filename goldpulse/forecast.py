from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error


@dataclass
class ForecastResult:
    comparison: pd.DataFrame
    metrics: pd.DataFrame
    future: pd.DataFrame
    selected_model: str


def evaluate_and_forecast(daily: pd.DataFrame, horizon: int = 3, test_size: int = 20) -> ForecastResult:
    series = daily.set_index("announcement_date")["value"].dropna().sort_index().astype(float)
    if len(series) < 35:
        raise ValueError("At least 35 daily observations are required for forecasting.")
    split = max(5, min(test_size, len(series) // 4))
    train, test = series.iloc[:-split], series.iloc[-split:]

    naive_pred = np.repeat(train.iloc[-1], len(test))
    full = pd.concat([train, test])
    lag_frame = pd.DataFrame({"y": full, "lag1": full.shift(1), "lag2": full.shift(2), "lag3": full.shift(3), "trend": np.arange(len(full))}).dropna()
    train_rows = lag_frame.index <= train.index[-1]
    model = Ridge(alpha=10.0).fit(lag_frame.loc[train_rows].drop(columns="y"), lag_frame.loc[train_rows, "y"])
    ridge_pred = model.predict(lag_frame.loc[~train_rows].drop(columns="y"))
    aligned_test = lag_frame.loc[~train_rows, "y"]

    def scores(name: str, actual: pd.Series, predicted: np.ndarray) -> dict:
        return {"model": name, "MAE": mean_absolute_error(actual, predicted), "RMSE": mean_squared_error(actual, predicted) ** 0.5}

    naive_aligned = naive_pred[-len(aligned_test):]
    metrics = pd.DataFrame([
        scores("Naive last value", aligned_test, naive_aligned),
        scores("Ridge autoregression", aligned_test, ridge_pred),
    ]).sort_values("MAE")
    selected = metrics.iloc[0]["model"]
    residuals = aligned_test.to_numpy() - (naive_aligned if selected == "Naive last value" else ridge_pred)
    margin = max(100.0, float(np.quantile(np.abs(residuals), 0.90)))

    history = list(series.values)
    future_values = []
    future_model = Ridge(alpha=10.0).fit(lag_frame.drop(columns="y"), lag_frame["y"])
    for i in range(horizon):
        if selected == "Naive last value":
            value = history[-1]
        else:
            features = pd.DataFrame(
                [[history[-1], history[-2], history[-3], len(history)]],
                columns=["lag1", "lag2", "lag3", "trend"],
            )
            value = future_model.predict(features)[0]
        future_values.append(value)
        history.append(value)
    last_date = pd.to_datetime(str(series.index[-1]))
    dates = pd.bdate_range(last_date + pd.offsets.BDay(1), periods=horizon)
    future = pd.DataFrame({"date": dates, "forecast": future_values})
    future["lower"] = future["forecast"] - margin
    future["upper"] = future["forecast"] + margin
    comparison = pd.DataFrame({"date": aligned_test.index, "actual": aligned_test.values, "naive": naive_aligned, "ridge": ridge_pred})
    return ForecastResult(comparison, metrics.reset_index(drop=True), future, selected)


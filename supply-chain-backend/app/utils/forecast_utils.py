"""
Forecast Feature Engineering

Reusable utilities for preparing time-series features from demand data.
Supports lag features, rolling statistics, and calendar-based signals.
"""

import numpy as np
import pandas as pd
from typing import List


# Ordered feature columns used for model training and inference
FEATURE_COLUMNS: List[str] = [
    "day_of_week",
    "month",
    "day_of_month",
    "quarter",
    "is_weekend",
    "days_since_start",
    "lag_1",
    "lag_7",
    "lag_30",
    "rolling_mean_7",
    "rolling_mean_30",
    "rolling_std_7",
]


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate time-series features from a demand DataFrame.

    Args:
        df: DataFrame with columns ['date', 'demand'] sorted ascending by date.

    Returns:
        DataFrame with FEATURE_COLUMNS added.
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    # Calendar features
    df["day_of_week"] = df["date"].dt.dayofweek          # 0=Mon … 6=Sun
    df["month"] = df["date"].dt.month                    # 1–12
    df["day_of_month"] = df["date"].dt.day               # 1–31
    df["quarter"] = df["date"].dt.quarter                # 1–4
    df["is_weekend"] = (df["date"].dt.dayofweek >= 5).astype(int)
    df["days_since_start"] = (df["date"] - df["date"].min()).dt.days

    # Lag features
    df["lag_1"] = df["demand"].shift(1)
    df["lag_7"] = df["demand"].shift(7)
    df["lag_30"] = df["demand"].shift(30)

    # Rolling statistics
    df["rolling_mean_7"] = df["demand"].rolling(7, min_periods=1).mean()
    df["rolling_mean_30"] = df["demand"].rolling(30, min_periods=1).mean()
    df["rolling_std_7"] = df["demand"].rolling(7, min_periods=2).std().fillna(0.0)

    return df


def build_future_feature_row(
    future_date,
    base_date,
    demand_history: List[float],
) -> List[float]:
    """
    Build a single feature vector for a future date during inference.

    Args:
        future_date: datetime for the day to predict.
        base_date: earliest date used when training (for days_since_start).
        demand_history: list of known/predicted demand values up to this point.

    Returns:
        List of feature values aligned with FEATURE_COLUMNS.
    """
    history = demand_history if demand_history else [0.0]

    lag_1 = history[-1]
    lag_7 = history[-7] if len(history) >= 7 else float(np.mean(history))
    lag_30 = history[-30] if len(history) >= 30 else float(np.mean(history))
    rolling_mean_7 = float(np.mean(history[-7:])) if history else 0.0
    rolling_mean_30 = float(np.mean(history[-30:])) if history else 0.0
    rolling_std_7 = float(np.std(history[-7:])) if len(history) >= 2 else 0.0
    days_since_start = (future_date - base_date).days

    return [
        future_date.weekday(),
        future_date.month,
        future_date.day,
        (future_date.month - 1) // 3 + 1,
        1 if future_date.weekday() >= 5 else 0,
        days_since_start,
        lag_1,
        lag_7,
        lag_30,
        rolling_mean_7,
        rolling_mean_30,
        rolling_std_7,
    ]

from __future__ import annotations

import numpy as np
import pandas as pd

from model import h_switch


def rolling_percentile_trigger(current: pd.Series, window_minutes: int = 180, quantile: float = 0.7) -> pd.Series:
    return current.rolling(window=window_minutes, min_periods=1).quantile(quantile)


# def weighted_running_average_trigger(current: pd.Series, window_minutes: int = 180, power: float = 1.0) -> pd.Series:
#     k = np.arange(1, window_minutes + 1)
#     weights = (1.0 / k) ** power
#     weights = weights / weights.sum()
#     return current.shift(1).rolling(window=window_minutes, min_periods=1).apply(lambda x: np.dot(x[::-1], weights[: len(x)]), raw=True)


def theta_from_current(current: pd.Series, trigger: pd.Series, delta_i: float = 1.25e5) -> pd.Series:
    values = [h_switch(i_value, ic_value, delta_i) for i_value, ic_value in zip(current, trigger)]
    return pd.Series(values, index=current.index, name="theta")

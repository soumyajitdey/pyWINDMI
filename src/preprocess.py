from __future__ import annotations

import datetime as dt
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

def compute_windmi_delay(data: pd.DataFrame) -> pd.Series:
    """Compute the WINDMI time-delay (seconds).

    Requires columns: 'Np', 'Vx', 'Bz'.
    """
    Dp = 1.67e-6 * data['Np'] * data['Vx']**2  # dynamic pressure in nPa
    R_subsolar = (10.22 + 1.29*np.tanh(0.184*(data['Bz'] + 8.14))) * (Dp**(-1/6.6))  # subsolar magnetopause standoff distance in RE
    t_delay_windmi = -((250.0 - R_subsolar) * 6380.0) / data['Vx'].rolling(window=20, min_periods=1, center=True).mean()  # time delay array for WINDMI model
    return t_delay_windmi

def apply_windmi_time_shift(data, t_delay_windmi):
    '''Apply time shift to WINDMI data based on the computed time delay. 
    This time delay accounts for the time it takes for solar wind disturbances to propagate
    from the ACE spacecraft (L1 point) to the Earth's magnetosphere.'''
    data_shifted = data.copy()
    # Shift time index by time-varying delay (seconds)
    data_shifted.index = data_shifted.index + pd.to_timedelta(
        t_delay_windmi, unit="s")
    data_shifted = data_shifted.sort_index()
    data_shifted = data_shifted[~data_shifted.index.isna()]
    #remove duplicate indices after shifting
    data_shifted = data_shifted[~data_shifted.index.duplicated(keep='first')]

    t_start = data_shifted.index.min().floor("min")
    t_end   = data_shifted.index.max().ceil("min")
    x0 = np.array((data_shifted.index - t_start)/dt.timedelta(seconds=1))  # original time index in seconds
    x1_time = pd.date_range(t_start, t_end, freq="1min")      # <- whole minutes
    x1 = np.array((x1_time - t_start)/dt.timedelta(seconds=1))  # resampled time index in seconds
    df = pd.DataFrame(index=x1_time)
    for col in data_shifted.columns:
        y0 = data_shifted[col].values
        y1 = interp1d(x0, y0, kind="linear", bounds_error=False, fill_value=np.nan)(x1)
        df[col] = y1
    #remove rows with NaN values

    df = df.dropna().reset_index()
    df = df.set_index('index')
    return df

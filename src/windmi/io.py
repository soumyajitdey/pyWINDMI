from __future__ import annotations

import os
import datetime as dt
import pandas as pd

def load_ace_csv(year: int, data_dir: str = "data", start=None, stop=None) -> pd.DataFrame:
    """Load ACE data file named ACE_<year>.csv from data_dir.

    This matches the notebook expectation:
      - CSV contains column 'Time' parseable as datetime
      - After loading, index is datetime and 'Time' column is dropped.

    If start/stop are provided, it applies the same padding window as the notebook:
      start - 2 hours to stop + 2 hours.
    """
    fname = os.path.join(data_dir, f"ACE_{year}.csv")
    data = pd.read_csv(fname)
    data.index = pd.to_datetime(data.Time)
    data.drop(columns=["Time"], inplace=True)
    if start is not None and stop is not None:
        data = data.iloc[(data.index >= start-dt.timedelta(hours=2)) & (data.index <= stop + dt.timedelta(hours=2))]
    return data

def load_supermag_csv(year: int, data_dir: str = "data") -> pd.DataFrame:
    """Load SuperMAG file named SuperMag_<year>.csv from data_dir.

    This matches the notebook expectation:
      - CSV contains column 'Date_UTC' parseable as datetime
      - After loading, index is datetime and 'Date_UTC' is dropped.
    """
    fname = os.path.join(data_dir, f"SuperMag_{year}.csv")
    SuperMag = pd.read_csv(fname)
    SuperMag.index = pd.to_datetime(SuperMag.Date_UTC)
    SuperMag.drop(columns=["Date_UTC"], inplace=True)
    return SuperMag

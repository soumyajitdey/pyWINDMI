from __future__ import annotations

import os
import datetime as dt
import pandas as pd

def load_ace_csv(year: int, data_dir: str = "data", start=None, stop=None) -> pd.DataFrame:
    """Load ACE data file named ACE_<year>.csv from folder 'data'.

    If start/stop are provided, it applies a padding window: start - 2 hours to stop + 2 hours.
    """
    fname = os.path.join(data_dir, f"ACE_{year}.csv")
    ACE = pd.read_csv(fname)
    ACE.index = pd.to_datetime(ACE.Time)
    ACE.drop(columns=["Time"], inplace=True)
    if start is not None and stop is not None:
        ACE = ACE.iloc[(ACE.index >= start-dt.timedelta(hours=2)) & (ACE.index <= stop + dt.timedelta(hours=2))]
    return ACE

def load_supermag_csv(year: int, data_dir: str = "data", start=None, stop=None) -> pd.DataFrame:
    """Load SuperMAG file named SuperMag_<year>.csv from folder 'data'.
    """
    fname = os.path.join(data_dir, f"SuperMag_{year}.csv")
    SuperMag = pd.read_csv(fname)
    SuperMag.index = pd.to_datetime(SuperMag.Date_UTC)
    SuperMag.drop(columns=["Date_UTC"], inplace=True)
    if start is not None and stop is not None:
        SuperMag = SuperMag.iloc[(SuperMag.index >= start-dt.timedelta(hours=2)) & (SuperMag.index <= stop + dt.timedelta(hours=2))]
    return SuperMag

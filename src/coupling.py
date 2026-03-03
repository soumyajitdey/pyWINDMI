from __future__ import annotations

import numpy as np
import pandas as pd

def add_coupling_inputs(data: pd.DataFrame) -> pd.DataFrame:
    """Add coupling input columns to the ACE dataframe for WINDMI model.
    Adds:
      - data['vBs'] : chosen input voltage for WINDMI (VBs formula)
    Requires columns:
      Bz (nT), Vx (km/s) from ACE data.
    """
    data = data.copy()

    Bz = data['Bz']; # IMF z-component in nT
    Vx = data['Vx']; # Solar wind velocity x-component in km/s

    R_E = 6380.0e3  # Earth radius in m
    Ly = 10.0 * R_E # effective width of magnetosphere in solar wind dynamo

    # VBs formula
    Bz_input = 0.5 * (np.abs(Bz) - Bz)  # if Bz < 0, Bz_input = |Bz| else Bz_input = 0
    Vsw0 = 4000.0 + (1.0e-6 * Ly * np.abs(Vx * Bz_input))  # Solar wind coupling function

    data['vBs'] = Vsw0; 
    return data

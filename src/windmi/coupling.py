from __future__ import annotations

import numpy as np
import pandas as pd

def add_coupling_inputs(data: pd.DataFrame) -> pd.DataFrame:
    """Add coupling input columns to the ACE dataframe, EXACTLY as in windmi_pub.ipynb.

    Adds:
      - data['vBs'] : chosen input voltage for WINDMI (VBs formula) (this matches the notebook).
    Requires columns:
      Bx, By, Bz (nT), Vx, Vy, Vz (km/s), Np (cm^-3)
    """
    data = data.copy()

    Bx = data['Bx']; By = data['By']; Bz = data['Bz']; # IMF components in nT
    Vx = data['Vx']; Vy = data['Vy']; Vz = data['Vz']; # Solar wind velocity components in km/s
    Np = data['Np']; # Solar wind proton density in cm^-3

    # Input voltages
    R_E = 6380.0e3  # Earth radius in m
    Ly = 10.0 * R_E # effective width of magnetosphere in solar wind dynamo

    # VBs formula
    Bz_input = 0.5 * (np.abs(Bz) - Bz)  # if Bz < 0, Bz_input = |Bz| else Bz_input = 0
    Vsw0 = 4000.0 + (1.0e-6 * Ly * np.abs(Vx * Bz_input))  # Solar wind coupling function

    # Siscoe-Hill formula
    m_p = 1.67e-27  # mass of proton in kg
    B_abs = np.abs(Bx**2 + By**2 + Bz**2) # magnitude of IMF in nT
    theta = np.arccos(Bz/B_abs)  # IMF clock angle in radians
    v_sw = np.sqrt(Vx**2 + Vy**2 + Vz**2)  # solar wind speed in km/s
    Esw = (v_sw*1e3) * (np.sqrt(By**2 + Bz**2)*1e-9) * np.sin(theta/2.0);
    Psw = m_p * (Np * 1.0e6) * ((v_sw*1.0e3)**2)  # solar wind dynamic pressure in Pa
    Phi_M = 30.0 + (57.6 * (Esw*1.0e3) * ((1.0e9 * Psw) ** (-1.0 / 6.0))) # magnetospheric potential in kV
    Vsw1 = 1e3*Phi_M;

    C0 = 0.77;
    F107 = 172.42; # its supposed to be monthly mean
    SigmaP = C0 * np.sqrt(F107);
    Phi_S = 1600.0 * ((Psw*1.0e9)**(1/3))/SigmaP # saturation voltage
    Phi_H = (Phi_M * Phi_S) / (Phi_M + Phi_S)  # Hill potential

    # Newell et al. 2007
    DPhi_mp = (np.abs(Vx)**(4/3)) * (B_abs**(2/3)) * (np.sin(theta / 2.0)**(8/3))  # dayside reconnection rate in kV
    Vsw2 = 4000.0 + (np.mean(Vsw0)/np.mean(DPhi_mp))*DPhi_mp;  # scaled Newell coupling function

    data['vBs'] = Vsw0;  # choose VBs as input voltage for WINDMI model
    return data

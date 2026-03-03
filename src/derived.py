from __future__ import annotations

import numpy as np
from numpy import sin, pi, log, arccos, sqrt
import pandas as pd

def calc_L_C_Sigma(data,
                    L_x=80.0,
                    L_y=50.0,
                    L_z=1.0,
                    r = 40.0,
                    B_x0 = 10.0e-9,
                    B_z0 = 0.1e-9
):
    '''Calculate the inductance (L), capacitance (C), and conductance (Sigma)
      of the near-Earth plasma sheet based on solar wind parameters.'''
    mu0 = 4*pi*1.0e-7  # permeability of free space
    R_E = 6380.0e3;  # Earth radius in m
    L_x = L_x * R_E; # length of the plasma sheet in the Sun-Earth direction
    L_y = L_y * R_E; # length of the plasma sheet in the y-direction (dawn-dusk)
    L_z = L_z * R_E; # length of the plasma sheet in the z-direction (north-south)
    e = 1.6e-19;  # elementary charge in C
    k_B = 1.38e-23  # Boltzmann constant in J/K
    m_p = 1.67e-27;  # mass of proton in kg

    Dp = 1.67e-6 * data['Np'] * data['Vx']**2  # dynamic pressure in nPa
    r_0 = (10.22 + 1.29*np.tanh(0.184*(data['Bz'] + 8.14))) * (Dp**(-1/6.6))  # subsolar magnetopause standoff distance in RE (Shue et al., 1997)
    alpha_s = (0.58 - (0.007*data['Bz']))*(1 + (0.024*log(Dp)))  # level of tail flaring (Shue et al., 1997)

    r_lobe = r * sin(arccos(2*((r_0/r)**(1/alpha_s)) - 1)) # lobe radius at distance r in R_E
    A_lobe = pi * ((r_lobe*R_E)**2)/2  # semi-circle area of the lobe at distance r
    L = mu0 * A_lobe  / L_x  # inductance of the lobe cavity

    n_ps = 0.292 * (data['Np']**0.49);  # plasma sheet density in cm^-3 from Borovsky et al. (1998)
    n_ps = n_ps * 1.0e6;  # convert to m^-3
    rho_ps = n_ps * m_p;  # plasma sheet mass density in kg/m^3
    C = pi * (L_x*L_z/L_y) * (rho_ps/(B_x0*B_z0))  # effective capacitance of the plasma sheet

    v_sw = sqrt(data['Vx']**2 + data['Vy']**2 + data['Vz']**2)  # solar wind speed in km/s
    T_cps = 2.17 + (0.0223*v_sw)  # central plasma sheet temperature in keV from Brorovsky et al. (1998)
    T_cps = T_cps * 1.0e3 * e / k_B  # convert to Kelvin
    rho_i = sqrt(m_p * k_B * T_cps) / (e * B_x0)  # ion gyroradius in m
    Sigma = 0.1 * (L_x*L_z/L_y) * (e*n_ps/B_x0) * sqrt(rho_i/L_z)
    return L, C, Sigma

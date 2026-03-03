"""Default WINDMI parameter dictionary.

This file preserves the constant parameter values
"""

from __future__ import annotations

def default_params() -> dict:
    # create a dictionary of inputs (EXACTLY as in the notebook)
    p = {
        # --- Inductances ---
        "L": 90.0,                    # Inductance of the lobe cavity
        "L1": 20.0,                    # Region-1 current inductance
        "L2": 8.0,                     # Ring current inductance

        "L_y": 3.2e7,                  # Cross-tail length scale [m]

        # --- Capacitances ---
        "C": 5.0e4,                   # Plasma sheet capacitance
        "C1": 8.0e2,                   # capacitance of R1 current loop

        # --- Resistances ---
        "R_prc": 0.1,                  # Partial ring current resistance
        "R_A2": 0.3,                   # Region-2 Alfven resistance

        "M": 0.1,                      # mutual inductance between I and I1 (in the paper its 1.0?)

        # --- Currents ---
        "DeltaI": 1.25e5,              # Delta I in theta function

        # --- Conductances ---
        "Sigma": 8.0,                  # Plasma sheet conductance
        "SigmaI": 3.0,                 # pedersen conductance of westward electrojet current

        # --- Magnetic / EM constants ---
        "u0": 4.2e-9,                 # heat flux limit paramter
        "Aeff": 8.14e13,              # Effective cross-sectional area [m^2]
        "Btr": 5.0e-9,                # Trigger magnetic field threshold [T]

        # --- Energetics ---
        "Omega_cps": 2.6e24,           # Plasma sheet volume
        "Alpha": 8.0e11,               # Energy coupling coefficient

        # --- Time constants ---
        "tauE": 30.0 * 60.0,          # Energy decay timescale [s]
        "tauk": 10.0 * 60.0,          # confinement time of parallel flow [s]
        "taurc": 12.0 * 3600.0,       # Ring current decay time [s]

        "beta_sw": 0.7,               # Coupling factor for SW across magnetopause

        "Ic_trig": 2.0e7              # Threshold current for substorm onset in A    
    }
    return p

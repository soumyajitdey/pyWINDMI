from __future__ import annotations

import numpy as np
from scipy.integrate import solve_ivp
from scipy.interpolate import interp1d

# change these at your own risk
DEFAULT_PARAMS = {
    "L": 90.0,
    "L1": 20.0,
    "L2": 8.0,
    "L_y": 3.2e7,
    "C": 5.0e4,
    "C1": 8.0e2,
    "R_prc": 0.1,
    "R_A2": 0.3,
    "M": 0.1,
    "DeltaI": 1.25e5,
    "Sigma": 8.0,
    "SigmaI": 3.0,
    "u0": 4.2e-9,
    "Aeff": 8.14e13,
    "Btr": 5.0e-9,
    "Omega_cps": 2.6e24,
    "Alpha": 8.0e11,
    "tauE": 30.0 * 60.0,
    "tauk": 10.0 * 60.0,
    "taurc": 12.0 * 3600.0,
    "beta_sw": 0.7,
    "Ic_trig": 2.0e7,
}

STATE_KEYS = ["I", "V", "I1", "VI", "pres", "Kk", "I2", "Wrc"]


def h_switch(i_value: float, ic_value: float, delta_i: float) -> float:
    return 0.5 * (1.0 + np.tanh((i_value - ic_value) / delta_i))


def windmi_rhs(t: float, params: dict, x: np.ndarray, vsw: float) -> np.ndarray:
    '''Compute the right-hand side of the WINDMI model equations (Horton et al. 1998) 
    I know the re-assignment of params are redundant, but its useful for modifications.
    returns the derivatives of the state variables as a numpy array.
    '''
    i_val, v_val, i1_val, vi_val, pres, kk, i2_val, wrc = x

    l_val = params["L"]
    l1_val = params["L1"]
    l2_val = params["L2"]
    ly_val = params["L_y"]
    c_val = params["C"]
    c1_val = params["C1"]
    r_prc = params["R_prc"]
    r_a2 = params["R_A2"]
    mutual = params["M"]
    delta_i = params["DeltaI"]
    sigma = params["Sigma"]
    sigma_i = params["SigmaI"]
    u0 = params["u0"]
    aeff = params["Aeff"]
    btr = params["Btr"]
    omega_cps = params["Omega_cps"]
    alpha = params["Alpha"]
    tau_e = params["tauE"]
    tau_k = params["tauk"]
    tau_rc = params["taurc"]
    beta_sw = params["beta_sw"]
    ic_trig = params["Ic_trig"]

    trigger = h_switch(i_val, ic_trig, delta_i)
    pres = max(pres, 0.0) # Ensure pressure remains non-negative
    kk = max(kk, 0.0) # Ensure Kk remains non-negative
    wrc = max(wrc, 0.0) # Ensure Wrc remains non-negative

    i_ps = alpha * np.sqrt(pres)
    inj_ps = (pres * v_val * aeff) / (omega_cps * btr * ly_val)
    inj_rc = (pres * v_val * aeff) / (btr * ly_val)

    a = np.array([[l_val, -mutual], [-mutual, l1_val]], dtype=float)
    b = np.array([beta_sw * vsw - v_val, v_val - vi_val], dtype=float)
    det_a = a[0, 0] * a[1, 1] - a[0, 1] * a[1, 0]
    if abs(det_a) < 1e-12 or np.linalg.cond(a) > 1e12:
        di_dt, di1_dt = np.linalg.lstsq(a, b, rcond=None)[0]
    else:
        di_dt, di1_dt = np.linalg.solve(a, b)

    dv_dt = (i_val - i1_val - i_ps - sigma * v_val) / c_val
    dp_dt = (2.0 / 3.0) * (((sigma * v_val * v_val) / omega_cps) - (u0 * pres * np.sqrt(kk) * trigger) - inj_ps - ((3.0 * pres) / (2.0 * tau_e)))
    dkk_dt = i_ps * v_val - (kk / tau_k)
    dvi_dt = (i1_val - i2_val - (sigma_i * vi_val)) / c1_val
    di2_dt = (vi_val - ((r_prc + r_a2) * i2_val)) / l2_val
    dwrc_dt = (r_prc * (i2_val ** 2)) + inj_rc - (wrc / tau_rc)
    
    return np.array([di_dt, dv_dt, di1_dt, dvi_dt, dp_dt, dkk_dt, di2_dt, dwrc_dt], dtype=float)


def solve_windmi_rk45(t_seconds, params: dict, vsw, x0=None, rtol: float = 1e-6, atol: float = 1e-9, ic_trig=None, l_value=None, c_value=None, sigma_value=None):
    '''Solve the WINDMI model equations using the RK45 method.
    Parameters:
    - t_seconds: array-like, time points in seconds at which to evaluate the solution.
    - params: dict, model parameters (see DEFAULT_PARAMS for reference).
    - vsw: array-like, solar wind speed values corresponding to t_seconds.
    - x0: array-like, initial conditions for the state variables (optional, defaults to zeros).
    - rtol: float, relative tolerance for the solver (default: 1e-6).
    - atol: float, absolute tolerance for the solver (default: 1e-9).
    - ic_trig: float, optional override for the Ic_trig parameter.
    - l_value: float, optional override for the L parameter.
    - c_value: float, optional override for the C parameter.
    - sigma_value: float, optional override for the Sigma parameter.
    Returns:
    - out: dict, containing time points and state variable values at those points.
    - local_params: dict, the parameters used for the simulation (including any overrides).
    '''
    t_seconds = np.asarray(t_seconds, dtype=float)
    vsw = np.asarray(vsw, dtype=float)
    if x0 is None:
        x0 = np.zeros(8, dtype=float)
    else:
        x0 = np.asarray(x0, dtype=float)
        if x0.shape != (8,):
            raise ValueError("x0 must have shape (8,)")

    local_params = params.copy()
    updates = {"Ic_trig": ic_trig, "L": l_value, "C": c_value, "Sigma": sigma_value}
    local_params.update({k: v for k, v in updates.items() if v is not None})

    vsw_of_t = interp1d(t_seconds, vsw, kind="linear", bounds_error=False, fill_value=(vsw[0], vsw[-1]))

    def rhs(t, x):
        return windmi_rhs(t, local_params, x, float(vsw_of_t(t)))

    sol = solve_ivp(rhs, (t_seconds[0], t_seconds[-1]), y0=x0, t_eval=t_seconds, rtol=rtol, atol=atol, max_step=60.0)
    if not sol.success:
        raise RuntimeError(sol.message)

    out = {"t": sol.t}
    for idx, key in enumerate(STATE_KEYS):
        out[key] = sol.y[idx]
    return out, local_params

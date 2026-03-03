from __future__ import annotations

import numpy as np
from scipy.interpolate import interp1d
from scipy.integrate import solve_ivp

def _H_switch(I, Ic, DeltaI):
    # Smooth step function (sigmoid) to transition from 0 to 1 around Ic with width DeltaI.
    return 0.5 * (1.0 + np.tanh((I - Ic) / DeltaI))

def windmi_rhs(t, p, x, Vsw):
    """
    State vector: X(t) = (I, V, I1, VI, p, Kk, I2, Wrc)
    Eqs. (9)-(16) in Spencer & Horton (2006).
    """

    I, V, I1, VI, pres, Kk, I2, Wrc = x
    ## WINDMI constants and parameters. For definitions of these parameters, see file 'src/params.py'
    L = p["L"] ;L1 = p["L1"]; L2 = p["L2"] ; L_y = p["L_y"];
    C = p["C"]; C1 = p["C1"];
    R_prc = p["R_prc"]; R_A2 = p["R_A2"];

    M = p["M"]; DeltaI = p["DeltaI"]; SigmaI = p["SigmaI"];
    u0 = p["u0"]; Aeff = p["Aeff"]; Btr = p["Btr"];

    Omega_cps = p["Omega_cps"]; Alpha = p["Alpha"];
    tauE = p["tauE"]; tauk = p["tauk"]; taurc = p["taurc"]; beta_sw = p["beta_sw"];

    # The real players
    L = p["L"]; C = p["C"]; Sigma = p["Sigma"]; Ic_trig = p["Ic_trig"];

    # --- derived terms ---
    H = _H_switch(I, Ic_trig, DeltaI)

    # --- failsafe for non-physical negative values ---
    pres = max(pres, 0.0);
    Kk   = max(Kk,   0.0);
    Wrc  = max(Wrc,  0.0);

    Ips = Alpha * np.sqrt(max(pres, 0.0))  # Ips = a p^{1/2}

    # Unloading / injection coupling term used in Eq. (11) and Eq. (16)
    # (paper term appears as p V Aeff / (Xcps Btr Ly) in Eq. 11 and p V Aeff / (Btr Ly) in Eq. 16)
    inj_ps = (pres * V * Aeff) / (Omega_cps * Btr * L_y)
    inj_rc = (pres * V * Aeff) / (Btr * L_y)

    # --- Solve the coupled inductive pair (Eqs. 9 & 13) for dI/dt and dI1/dt ---
    # Eq (9):  L dI/dt  = bsw Vsw - V + M dI1/dt
    # Eq (13): LI dI1/dt = V - VI + M dI/dt
    # Write as:
    # [ L   -M ] [dI ] = [ bsw Vsw - V ]
    # [ -M  LI ] [dI1]   [ V - VI       ]
    A = np.array([[L, -M],
                [-M, L1]], dtype=float)
    b = np.array([beta_sw*Vsw - V,
                V - VI], dtype=float)

    detA = A[0,0]*A[1,1] - A[0,1]*A[1,0]   # = L*L1 - M^2

    # failsafe thresholds (tune if needed)
    eps_det = 1e-12
    max_cond = 1e12

    if abs(detA) < eps_det or np.linalg.cond(A) > max_cond:
        # fallback: least-squares / pseudo-inverse (won’t crash)
        dI, dI1 = np.linalg.lstsq(A, b, rcond=None)[0]
    else:
        dI, dI1 = np.linalg.solve(A, b)

    # Eq (10): C dV/dt = I - I1 - Ips - R V
    dV = (I - I1 - Ips - Sigma*V) / C

    # Eq (11): (3/2) dp/dt = R V^2 / Xcps - u0 p Kk^{1/2} H - p V Aeff/(Xcps Btr Ly) - (3p)/(2 tauE)
    # => dp/dt = (2/3)*[ ... ]
    dP = (2.0/3.0) * ( ((Sigma * V * V) / Omega_cps)
                       - (u0 * pres * np.sqrt(max(Kk, 0.0)) * H)
                       - inj_ps
                       - ((3.0 * pres)/(2.0 * tauE)) )

    # Eq (12): dKk/dt = Ips V - Kk/tauk
    dKk = Ips * V - (Kk / tauk)

    # Eq (14): CI dVI/dt = I1 - I2 - RI VI
    dVI = (I1 - I2 - (SigmaI * VI)) / C1

    # Eq (15): L2 dI2/dt = VI - (Rprc + RA2) I2
    dI2 = (VI - ((R_prc + R_A2) * I2)) / L2

    # Eq (16): dWrc/dt = Rprc I2^2 + p V Aeff/(Btr Ly) - Wrc/taurc
    dWrc = (R_prc * (I2**2)) + inj_rc - (max(Wrc, 0.0) / taurc)

    return np.array([dI, dV, dI1, dVI, dP, dKk, dI2, dWrc], dtype=float)

def solve_windmi_rk45(t_seconds,
                      p,
                      Vsw,
                      x0=None,
                      rtol=1e-6,
                      atol=1e-9,
                      Ic_trig=None,
                      L = None, C = None, Sigma = None):

    t_seconds = np.asarray(t_seconds, dtype=float);
    Vsw = np.asarray(Vsw, dtype=float);
    # default initial condition if not provided
    if x0 is None:
        x0 = np.zeros(8, dtype=float)
    else:
        x0 = np.asarray(x0, dtype=float)
        if x0.shape != (8,):
            raise ValueError("x0 must be shape (8,) = [I, V, I1, VI, p, Kk, I2, Wrc]")
    Vsw_of_t = interp1d(
        t_seconds, Vsw,
        kind="linear",
        bounds_error=False,
        fill_value=(Vsw[0], Vsw[-1])
    )
    p.update({
    k: v for k, v in {
        "Ic_trig": Ic_trig,
        "L": L,
        "C": C,
        "Sigma": Sigma
    }.items() if v is not None
})
    def rhs(t, x):
        return windmi_rhs(t, p, x, Vsw_of_t(t))
    sol = solve_ivp(rhs,
                    (t_seconds[0], t_seconds[-1]),
                    y0=x0,
                    t_eval=t_seconds,
                    rtol=rtol,
                    atol=atol,
                    max_step=60.0)
    if not sol.success:
        k = -1 if sol.t.size > 0 else None
        if k is not None:
            print("FAIL t =", sol.t[k])
            print("STATE @ fail:", sol.y[:, k])
        print("MESSAGE:", sol.message)
        raise RuntimeError(sol.message)
    return {
        "t": sol.t,
        "I":   sol.y[0],
        "V":   sol.y[1],
        "I1":  sol.y[2],
        "VI":  sol.y[3],
        "pres":   sol.y[4],
        "Kk":  sol.y[5],
        "I2":  sol.y[6],
        "Wrc": sol.y[7]}, p

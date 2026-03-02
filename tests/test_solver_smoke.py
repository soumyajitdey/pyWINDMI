import numpy as np
from windmi.params import default_params
from windmi.model import solve_windmi_rk45

def test_solver_smoke():
    # 10 minutes at 1-min resolution
    t = np.arange(0, 601, 60.0)
    Vsw = np.ones_like(t) * 4000.0
    p = default_params()
    out, _ = solve_windmi_rk45(t, p, Vsw)
    assert "I" in out and out["I"].shape == t.shape

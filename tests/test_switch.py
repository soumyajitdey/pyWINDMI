import numpy as np
from windmi.model import _H_switch

def test_H_switch_limits():
    Ic = 10.0
    DeltaI = 1.0
    assert _H_switch(Ic-100*DeltaI, Ic, DeltaI) < 1e-6
    assert _H_switch(Ic+100*DeltaI, Ic, DeltaI) > 1-1e-6

import datetime as dt
import numpy as np
import pandas as pd

from windmi.io import load_ace_csv, load_supermag_csv
from windmi.preprocess import compute_windmi_delay, apply_windmi_time_shift
from windmi.coupling import add_coupling_inputs
from windmi.params import default_params
from windmi.model import solve_windmi_rk45

def main():
    start = dt.datetime(2000,1,9)
    stop  = dt.datetime(2000,1,13)

    data = load_ace_csv(start.year, data_dir="data", start=start, stop=stop)
    _supermag = load_supermag_csv(start.year, data_dir="data")  # optional; loaded for parity with notebook

    t_delay_windmi = compute_windmi_delay(data)
    data = apply_windmi_time_shift(data, t_delay_windmi)
    data = data.loc[start:stop]

    data = add_coupling_inputs(data)

    t_seconds = np.array((data.index - start)/dt.timedelta(seconds=1))
    p = default_params()

    out, _ = solve_windmi_rk45(t_seconds, p, data["vBs"])

    out_df = pd.DataFrame(
        {"I": out["I"], "V": out["V"], "I1": out["I1"], "VI": out["VI"],
         "pres": out["pres"], "Kk": out["Kk"], "I2": out["I2"], "Wrc": out["Wrc"]},
        index=data.index
    )
    print(out_df.head())

if __name__ == "__main__":
    main()

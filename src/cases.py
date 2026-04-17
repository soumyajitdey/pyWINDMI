from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import numpy as np
import pandas as pd
from numpy import pi, sin, tanh, log, arccos, sqrt
from tqdm import tqdm

from data import prepare_inputs
from model import DEFAULT_PARAMS, STATE_KEYS, solve_windmi_rk45
from plotting import save_comparison_plot
from triggers import rolling_percentile_trigger

def _as_seconds(index: pd.DatetimeIndex, start: dt.datetime) -> np.ndarray:
    return np.array((index - start) / dt.timedelta(seconds=1), dtype=float)

def calc_l_c_sigma(data: pd.DataFrame, l_x: float = 80.0, l_y: float = 50.0, l_z: float = 1.0, r: float = 40.0, b_x0: float = 10.0e-9, b_z0: float = 0.1e-9):
    mu0 = 4 * pi * 1.0e-7
    r_e = 6380.0e3
    l_x_m = l_x * r_e
    l_y_m = l_y * r_e
    l_z_m = l_z * r_e
    e_charge = 1.6e-19
    k_b = 1.38e-23
    m_p = 1.67e-27

    dp = 1.67e-6 * data["Np"] * data["Vx"] ** 2
    r_0 = (10.22 + 1.29 * tanh(0.184 * (data["Bz"] + 8.14))) * (dp ** (-1 / 6.6))
    alpha_s = (0.58 - (0.007 * data["Bz"])) * (1 + (0.024 * log(dp)))
    r_lobe = r * sin(arccos(2 * ((r_0 / r) ** (1 / alpha_s)) - 1))
    a_lobe = pi * ((r_lobe * r_e) ** 2) / 2
    l_val = mu0 * a_lobe / l_x_m

    n_ps = 0.292 * (data["Np"] ** 0.49)
    n_ps = n_ps * 1.0e6
    rho_ps = n_ps * m_p
    c_val = pi * (l_x_m * l_z_m / l_y_m) * (rho_ps / (b_x0 * b_z0))

    v_sw = sqrt(data["Vx"] ** 2 + data["Vy"] ** 2 + data["Vz"] ** 2)
    t_cps = 2.17 + (0.0223 * v_sw)
    t_cps = t_cps * 1.0e3 * e_charge / k_b
    rho_i = sqrt(m_p * k_b * t_cps) / (e_charge * b_x0)
    sigma = 0.1 * (l_x_m * l_z_m / l_y_m) * (e_charge * n_ps / b_x0) * sqrt(rho_i / l_z_m)
    return l_val, c_val, sigma

# def _frame_from_output(
#     out_dict: dict,
#     index: pd.DatetimeIndex,
#     ic_values=None,
#     l_values=None,
#     c_values=None,
#     sigma_values=None,
# ) -> pd.DataFrame:

#     frame = pd.DataFrame(
#         {key: np.asarray(out_dict[key]) for key in STATE_KEYS},
#         index=index
#     )

#     # ---- I_c ----
#     if ic_values is not None:
#         if np.isscalar(ic_values):
#             frame["I_c"] = float(ic_values)
#         else:
#             frame["I_c"] = np.asarray(ic_values)

#     # ---- L ----
#     if l_values is not None:
#         if np.isscalar(l_values):
#             frame["L"] = float(l_values)
#         else:
#             frame["L"] = np.asarray(l_values)

#     # ---- C ----
#     if c_values is not None:
#         if np.isscalar(c_values):
#             frame["C"] = float(c_values)
#         else:
#             frame["C"] = np.asarray(c_values)

#     # ---- Sigma ----
#     if sigma_values is not None:
#         if np.isscalar(sigma_values):
#             frame["Sigma"] = float(sigma_values)
#         else:
#             frame["Sigma"] = np.asarray(sigma_values)

#     return frame

def _save_common_outputs(case_name: str, title: str, output_dir: str | Path, processed: pd.DataFrame, no_trigger: pd.DataFrame, with_trigger: pd.DataFrame, supermag: pd.DataFrame, substorms: dict[str, pd.DataFrame], meta: dict, variable_parameters: pd.DataFrame | None = None) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    processed.to_csv(output_dir / 'processed_input.csv')
    no_trigger.to_csv(output_dir / 'no_trigger.csv')
    with_trigger.to_csv(output_dir / 'with_trigger.csv')
    if variable_parameters is not None:
        variable_parameters.to_csv(output_dir / 'variable_parameters.csv')

    save_comparison_plot(no_trigger=no_trigger, with_trigger=with_trigger, supermag=supermag, substorms=substorms, output_path=output_dir / 'comparison.png', title=title)

    summary = {
        'case': case_name,
        **meta,
        'n_processed_rows': int(len(processed)),
        'n_no_trigger_rows': int(len(no_trigger)),
        'n_with_trigger_rows': int(len(with_trigger)),
        'start': processed.index.min().isoformat() if not processed.empty else None,
        'stop': processed.index.max().isoformat() if not processed.empty else None,
        'mode_LCS': title.split(',')[0].split('=')[1].strip(),
        'mode_Ic': title.split(',')[1].split('=')[1].strip(),
        'output folder': str(output_dir),
    }
    with open(output_dir / 'summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    return output_dir

def windmi(
    start: dt.datetime,
    stop: dt.datetime,
    output_dir: str | Path,
    *,
    mode_LCS: str = "constant",   # "constant" | "variable"
    mode_Ic: str = "daily",      # "daily" | "rolling"
    data_root=None,
    ace_url_template: str | None = None,
    prompt_for_download: bool = True,
) -> Path:
    processed, supermag, substorms, meta = prepare_inputs(
        start,
        stop,
        data_root=data_root,
        ace_url_template=ace_url_template,
        prompt_for_download=prompt_for_download,
    )
    N = len(processed)
    if N < 2:
        raise ValueError("Need at least 2 data points to run the model.")
    t_seconds = _as_seconds(processed.index, start)
    vsw_all = processed["input_voltage"].values

    # ---- Calculate L, C, Sigma ----
    if mode_LCS == "constant":
        l_arr = c_arr = sigma_arr = None
    elif mode_LCS == "variable":
        l_arr, c_arr, sigma_arr = calc_l_c_sigma(processed)
    else:
        raise ValueError(f"Invalid mode_LCS: {mode_LCS}")

    # No trigger case 
    params = DEFAULT_PARAMS.copy()
    x0 = np.zeros(8)
    states_no_trigger = np.full((N, len(STATE_KEYS)), np.nan)
    for i in tqdm(range(N - 1), desc="Processing no-trigger case"):
        idx = processed.index[i:i+2]
        t_i = _as_seconds(idx, start)
        vsw_i = vsw_all[i:i+2]

        kwargs = {}
        if mode_LCS == "variable":
            kwargs = dict(
                l_value=float(l_arr.iloc[i]),
                c_value=float(c_arr.iloc[i]),
                sigma_value=float(sigma_arr.iloc[i]),
            )

        out_i, params = solve_windmi_rk45(
            t_i, params, vsw_i, x0=x0, ic_trig=None, **kwargs)

        if i == 0:
            for j, key in enumerate(STATE_KEYS):
                states_no_trigger[0:2, j] = out_i[key]
        else:
            for j, key in enumerate(STATE_KEYS):
                states_no_trigger[i+1, j] = out_i[key][-1]

        x0 = np.array([out_i[key][-1] for key in STATE_KEYS])

    no_trigger = pd.DataFrame(states_no_trigger, index=processed.index, columns=STATE_KEYS)

    # Calculate I_c trigger values
    if mode_Ic == "rolling":
        ic_series = rolling_percentile_trigger(
            no_trigger["I"], window_minutes=180, quantile=0.7
        ).values
    elif mode_Ic == "daily":
        ic_series = np.zeros(N)
        days = pd.to_datetime(processed.index.date)

        for d in np.unique(days):
            mask = days == d
            ic_val = np.percentile(no_trigger.loc[mask, "I"], 70.0)
            ic_series[mask] = ic_val
    else:
        raise ValueError(f"Invalid mode_Ic: {mode_Ic}")
    
    # With trigger case
    params = DEFAULT_PARAMS.copy()
    x0 = np.zeros(8)
    states_with_trigger = np.full((N, len(STATE_KEYS)), np.nan)
    for i in tqdm(range(N - 1), desc="Processing with-trigger case"):
        idx = processed.index[i:i+2]
        t_i = _as_seconds(idx, start)
        vsw_i = vsw_all[i:i+2]
        ic_i = float(ic_series[i])

        kwargs = {}
        if mode_LCS == "variable":
            kwargs = dict(
                l_value=float(l_arr.iloc[i]),
                c_value=float(c_arr.iloc[i]),
                sigma_value=float(sigma_arr.iloc[i]),
            )

        out_i, params = solve_windmi_rk45(
            t_i, params, vsw_i, x0=x0, ic_trig=ic_i, **kwargs
        )

        if i == 0:
            for j, key in enumerate(STATE_KEYS):
                states_with_trigger[0:2, j] = out_i[key]
        else:
            for j, key in enumerate(STATE_KEYS):
                states_with_trigger[i+1, j] = out_i[key][-1]
        x0 = np.array([out_i[key][-1] for key in STATE_KEYS])

    with_trigger = pd.DataFrame(states_with_trigger,
                                 index=processed.index,
                                   columns=STATE_KEYS)
    with_trigger["I_c"] = ic_series

    variable_parameters = None
    if mode_LCS == "variable":
        variable_parameters = pd.DataFrame(
            {"L": l_arr, "C": c_arr, "Sigma": sigma_arr},
            index=processed.index,
        )

    title = f"LCS={mode_LCS}, Ic={mode_Ic}"
    return _save_common_outputs(
        "combined_case",
        title,
        output_dir,
        processed,
        no_trigger,
        with_trigger,
        supermag,
        substorms,
        meta,
        variable_parameters=variable_parameters,
    )

        
        
    

    

    


    
    
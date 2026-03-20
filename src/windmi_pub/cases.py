from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import numpy as np
import pandas as pd
from numpy import pi, sin
from tqdm import tqdm

from .data import prepare_inputs
from .model import DEFAULT_PARAMS, STATE_KEYS, solve_windmi_rk45
from .plotting import save_comparison_plot
from .triggers import rolling_percentile_trigger


def _as_seconds(index: pd.DatetimeIndex, start: dt.datetime) -> np.ndarray:
    return np.array((index - start) / dt.timedelta(seconds=1), dtype=float)


def _frame_from_output(out_dict: dict, index: pd.DatetimeIndex, ic_values=None) -> pd.DataFrame:
    frame = pd.DataFrame({key: np.asarray(out_dict[key]) for key in STATE_KEYS}, index=index)
    if ic_values is not None:
        if np.isscalar(ic_values):
            frame["I_c"] = float(ic_values)
        else:
            frame["I_c"] = np.asarray(ic_values)
    return frame


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
    r_0 = (10.22 + 1.29 * np.tanh(0.184 * (data["Bz"] + 8.14))) * (dp ** (-1 / 6.6))
    alpha_s = (0.58 - (0.007 * data["Bz"])) * (1 + (0.024 * np.log(dp)))
    r_lobe = r * sin(np.arccos(2 * ((r_0 / r) ** (1 / alpha_s)) - 1))
    a_lobe = pi * ((r_lobe * r_e) ** 2) / 2
    l_val = mu0 * a_lobe / l_x_m

    n_ps = 0.292 * (data["Np"] ** 0.49)
    n_ps = n_ps * 1.0e6
    rho_ps = n_ps * m_p
    c_val = np.pi * (l_x_m * l_z_m / l_y_m) * (rho_ps / (b_x0 * b_z0))

    v_sw = np.sqrt(data["Vx"] ** 2 + data["Vy"] ** 2 + data["Vz"] ** 2)
    t_cps = 2.17 + (0.0223 * v_sw)
    t_cps = t_cps * 1.0e3 * e_charge / k_b
    rho_i = np.sqrt(m_p * k_b * t_cps) / (e_charge * b_x0)
    sigma = 0.1 * (l_x_m * l_z_m / l_y_m) * (e_charge * n_ps / b_x0) * np.sqrt(rho_i / l_z_m)
    return l_val, c_val, sigma


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
    }
    with open(output_dir / 'summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    return output_dir


def run_case_1(
    start: dt.datetime,
    stop: dt.datetime,
    output_dir: str | Path,
    data_root=None,
    *,
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
    params = DEFAULT_PARAMS.copy()
    t_seconds = _as_seconds(processed.index, start)
    out, _ = solve_windmi_rk45(t_seconds, params, processed['input_voltage'].values)
    no_trigger = _frame_from_output(out, processed.index)

    x0 = np.zeros(8, dtype=float)
    pieces = []
    for day in pd.Index(processed.index.normalize().unique()):
        day_start = pd.Timestamp(day)
        day_stop = day_start + pd.Timedelta(days=1)
        mask = (processed.index >= day_start) & (processed.index < day_stop)
        if not mask.any():
            continue
        day_index = processed.index[mask]
        day_seconds = _as_seconds(day_index, start)
        day_vsw = processed.loc[day_index, 'input_voltage'].values
        ic_day = float(np.percentile(no_trigger.loc[day_index, 'I'], 70.0))
        out_day, _ = solve_windmi_rk45(day_seconds, params, day_vsw, x0=x0, ic_trig=ic_day)
        day_frame = _frame_from_output(out_day, day_index, ic_values=ic_day)
        pieces.append(day_frame)
        x0 = np.array([out_day[key][-1] for key in STATE_KEYS], dtype=float)

    with_trigger = pd.concat(pieces).sort_index() if pieces else pd.DataFrame(columns=STATE_KEYS + ['I_c'])
    return _save_common_outputs('case_1', 'Case 1: Constant L, C, Sigma + daily I_c', output_dir, processed, no_trigger, with_trigger, supermag, substorms, meta)


def run_case_2(
    start: dt.datetime,
    stop: dt.datetime,
    output_dir: str | Path,
    data_root=None,
    *,
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
    params = DEFAULT_PARAMS.copy()
    t_seconds = _as_seconds(processed.index, start)
    out, _ = solve_windmi_rk45(t_seconds, params, processed['input_voltage'].values)
    no_trigger = _frame_from_output(out, processed.index)
    rolling_ic = rolling_percentile_trigger(no_trigger['I'], window_minutes=180, quantile=0.7)

    x0 = np.zeros(8, dtype=float)
    pieces = []
    for i in tqdm(range(len(processed.index) - 1), desc='Case 2'):
        idx = processed.index[i:i+2]
        t_i = _as_seconds(idx, start)
        vsw_i = processed.loc[idx, 'input_voltage'].values
        ic_i = float(rolling_ic.iloc[i])
        out_i, _ = solve_windmi_rk45(t_i, params, vsw_i, x0=x0, ic_trig=ic_i)
        if i == 0:
            frame = _frame_from_output(out_i, idx, ic_values=np.full(len(idx), ic_i))
        else:
            sliced = {key: np.asarray(out_i[key])[1:] for key in STATE_KEYS}
            frame = _frame_from_output(sliced, idx[1:2], ic_values=np.array([ic_i]))
        pieces.append(frame)
        x0 = np.array([out_i[key][-1] for key in STATE_KEYS], dtype=float)

    with_trigger = pd.concat(pieces).sort_index() if pieces else pd.DataFrame(columns=STATE_KEYS + ['I_c'])
    return _save_common_outputs('case_2', 'Case 2: Constant L, C, Sigma + rolling I_c', output_dir, processed, no_trigger, with_trigger, supermag, substorms, meta)


def run_case_3(
    start: dt.datetime,
    stop: dt.datetime,
    output_dir: str | Path,
    data_root=None,
    *,
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
    l_arr, c_arr, sigma_arr = calc_l_c_sigma(processed)
    variable_parameters = pd.DataFrame({'L': l_arr, 'C': c_arr, 'Sigma': sigma_arr}, index=processed.index)

    params_no = DEFAULT_PARAMS.copy()
    x0 = np.zeros(8, dtype=float)
    no_parts = []
    for i in tqdm(range(len(processed.index) - 1), desc='Case 3 no-trigger'):
        idx = processed.index[i:i+2]
        t_i = _as_seconds(idx, start)
        vsw_i = processed.loc[idx, 'input_voltage'].values
        out_i, params_no = solve_windmi_rk45(t_i, params_no, vsw_i, x0=x0, ic_trig=None, l_value=float(l_arr.iloc[i]), c_value=float(c_arr.iloc[i]), sigma_value=float(sigma_arr.iloc[i]))
        if i == 0:
            frame = _frame_from_output(out_i, idx)
        else:
            sliced = {key: np.asarray(out_i[key])[1:] for key in STATE_KEYS}
            frame = _frame_from_output(sliced, idx[1:2])
        no_parts.append(frame)
        x0 = np.array([out_i[key][-1] for key in STATE_KEYS], dtype=float)
    no_trigger = pd.concat(no_parts).sort_index() if no_parts else pd.DataFrame(columns=STATE_KEYS)

    rolling_ic = rolling_percentile_trigger(no_trigger['I'], window_minutes=180, quantile=0.7)

    params_yes = DEFAULT_PARAMS.copy()
    x0 = np.zeros(8, dtype=float)
    yes_parts = []
    for i in tqdm(range(len(processed.index) - 1), desc='Case 3 with-trigger'):
        idx = processed.index[i:i+2]
        t_i = _as_seconds(idx, start)
        vsw_i = processed.loc[idx, 'input_voltage'].values
        ic_i = float(rolling_ic.iloc[i])
        out_i, params_yes = solve_windmi_rk45(t_i, params_yes, vsw_i, x0=x0, ic_trig=ic_i, l_value=float(l_arr.iloc[i]), c_value=float(c_arr.iloc[i]), sigma_value=float(sigma_arr.iloc[i]))
        if i == 0:
            frame = _frame_from_output(out_i, idx, ic_values=np.full(len(idx), ic_i))
        else:
            sliced = {key: np.asarray(out_i[key])[1:] for key in STATE_KEYS}
            frame = _frame_from_output(sliced, idx[1:2], ic_values=np.array([ic_i]))
        yes_parts.append(frame)
        x0 = np.array([out_i[key][-1] for key in STATE_KEYS], dtype=float)
    with_trigger = pd.concat(yes_parts).sort_index() if yes_parts else pd.DataFrame(columns=STATE_KEYS + ['I_c'])

    return _save_common_outputs('case_3', 'Case 3: Variable L, C, Sigma + rolling I_c', output_dir, processed, no_trigger, with_trigger, supermag, substorms, meta, variable_parameters=variable_parameters)

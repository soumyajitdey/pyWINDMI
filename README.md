# pyWINDMI

Python implementation of the WINDMI (Wind-driven Magnetosphere–Ionosphere) model, a low-dimensional, physics-based model that simulates the transfer and storage of energy in the magnetosphere–ionosphere system. The model solves a coupled set of non-linear differential equations to produce time series of key state variables such as cross-tail current, region-1 and region-2 currents, ionospheric potential, plasma sheet pressure, and ring current energy.

## Installation

Use **Python 3.10 or newer**.

```bash
git clone https://github.com/soumyajitdey/pyWINDMI.git
cd pyWINDMI
pip install -e . # optional: only needed if you want to install pyWINDMI as a Python package
```

Check that everything is working:

```bash
python -m bootstrap
```

## Running the model

Run commands from the repository root (`pyWINDMI/` folder).

```bash
python examples/run_windmi.py \
    --start 2000-07-15T00:00:00 \
    --stop  2000-07-19T00:00:00 \
    --mode-LCS variable \
    --mode-Ic rolling
```

The four flags above are all required. See [Configuration](#configuration) for a full description of each.

---

## Configuration

### `--start` and `--stop`

The time window for the run, in ISO 8601 format (UTC). The model fetches and processes all ACE solar-wind data that falls within this range.

### `--mode-LCS`

Controls how the three core model parameters — inductance `L`, capacitance `C`, and conductance `σ` of magnetosphere — are determined.

- `constant` — use fixed default values throughout the run, provided in `src/model.py`.
- `variable` — derives the parameters at each timestep (using `calc_l_c_sigma` function in `src/cases.py`).

### `--mode-Ic`

Controls how the unloading trigger geotail current `I_c` is computed (uses `src/triggers.py`).

- `daily` — daily current threshold set to the 70th percentile of the no-trigger current `I` for that day.
- `rolling` — recomputed continuously from a rolling 3-hour window using the same percentile.

### Additional options

| Flag | Default | Description |
|---|---|---|
| `--output-dir PATH` | Auto-generated from run settings | Write results to a specific folder. |
| `--data-root PATH` | `./data` (or `WINDMI_DATA_ROOT`) | Look for input data here instead of the default search path. |
| `--ace-url-template URL` | `https://github.com/soumyajitdey/ACE_data` | Custom download template for missing ACE files. |
| `--no-prompt` | Prompts enabled | Skip all interactive download confirmations. |

---

## Input data

The model reads ACE solar-wind files in CSV format. If a required file is missing locally, pyWINDMI will offer to download it from the companion repository at `https://github.com/soumyajitdey/ACE_data`.

Data is searched in the following order:

1. The path given via `--data-root`
2. The `WINDMI_DATA_ROOT` environment variable
3. A `./data` directory relative to the working path

**ACE files** (required) follow the naming pattern `ACE_<year>.csv` and must contain the columns `Time`, `Bx`, `By`, `Bz`, `Vx`, `Vy`, `Vz`, and `Np`.

**Comparison files** (optional) are used only when generating the output figure. These include `SuperMag_<year>.csv` (requires `Date_UTC` and `SML` columns) and any of the substorm catalogs (`Substorms_Forsyth_*`, `Substorms_Frey_*`, `Substorms_Liou_*`, `Substorms_Newell_*`, `Substorms_Ohtani_*`), each requiring a `Date_UTC` column.

---

## Output

Results are written to the output directory, which is named automatically if `--output-dir` is not set:

```
outputs/windmi_<mode-LCS>_LCS_<mode-Ic>_Ic_<start>_to_<stop>/
```

The directory contains the following files.

**`processed_input.csv`** — the solar-wind data as the solver actually sees it: time-shifted to account for propagation delay, resampled to a 1-minute grid, and extended with the computed `vBs` coupling function and `input_voltage` column.

**`no_trigger.csv`** — state variables from the first model pass, run without the unloading trigger. Columns: `I` (cross-tail current), `V` (magnetospheric potential), `I1` (Region-1 FAC), `VI` (ionospheric potential), `pres` (plasma-sheet pressure), `Kk` (plasma sheet kinetic energy), `I2` (Region-2 FAC), `Wrc` (ring-current energy).

**`with_trigger.csv`** — state variables from the second model pass, with the unloading trigger active. Same columns as above, plus `I_c`, the trigger threshold at each timestep.

**`variable_parameters.csv`** *(written only when `--mode-LCS variable` is used)* — the time-dependent values of `L`, `C`, and `σ` computed from the input data.

**`comparison.png`** — a two-panel figure. The top panel overlays `I` from both passes alongside `I_c`. The bottom panel shows the unloading trigger function `Θ`, with optional substorm onset markers from available catalogs and SuperMAG `SML` index on the secondary axis.

**`summary.json`** — metadata for the run: requested and actual time ranges, row counts for each output table, data availability flags, and the mode settings used.

---

## How a run works

pyWINDMI runs the model twice. The first pass integrates the equations without the substorm unloading trigger, producing a baseline current series from which `I_c` is derived. The second pass uses that threshold to activate the trigger mechanism at the appropriate times. This two-pass design keeps the trigger current physically grounded in each run's own solar-wind conditions rather than relying on a fixed external value.

Between those two passes, the code handles all data logistics: loading ACE files, downloading anything missing, computing the propagation delay from ACE to the subsolar point, and resampling the time-shifted data to the uniform 1-minute grid that the ODE solver expects.

---

## Project structure

```
pyWINDMI/
├── examples/
│   └── run_windmi.py      # entry point
├── src/
│   ├── bootstrap.py       # environment check
│   ├── cases.py           # run configuration
│   ├── data.py            # data loading and preprocessing
│   ├── model.py           # ODE definitions and integration
│   ├── plotting.py        # comparison figure
│   └── triggers.py        # I_c computation
├── CITATION.cff
├── LICENSE
├── changelog.md
└── pyproject.toml
```
---

## Citation

If you use pyWINDMI in published work, please cite it using the metadata in `CITATION.cff`.

---

## References
1. Horton, W., and I. Doxas. “A Low‐dimensional Dynamical Model for the Solar Wind Driven Geotail‐ionosphere System.” Journal of Geophysical Research: Space Physics 103, no. A3 (1998): 4561–72. https://doi.org/10.1029/97JA02417.
2. Spencer, E., W. Horton, and I. Doxas. “The Dynamics of Storms and Substorms with the WINDMI Model.” Advances in Space Research 38, no. 8 (2006): 1657–68. https://doi.org/10.1016/j.asr.2006.02.013.
3. Adhya, P., Spencer, E., & KayodeAdeoye, M. (2025). Substorm identification with the WINDMI magnetosphere ‐ Ionosphere nonlinear physics model. Space Weather, 23, e2024SW003960. https://doi.org/10.1029/ 2024SW003960

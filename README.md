# pyWINDMI

Python implementation of the WINDMI (Wind-driven Magnetosphere–Ionosphere) model, a low-dimensional, physics-based model that simulates the transfer and storage of energy in the magnetosphere–ionosphere system. The model solves a coupled set of non-linear differential equations to produce time series of key state variables such as cross-tail current, region-1 and region-2 currents, ionospheric potential, plasma sheet pressure, and ring current energy.

## Basic Usage

The model is executed using a single script, where the user specifies the time range and run configuration.

### Required arguments

- `--start` : Start date and time (UTC)  
- `--stop`  : End date and time (UTC)  
- `--mode-LCS` : Treatment of \(L\), \(C\), and \(\Sigma\)  
  - `constant`  
  - `variable`  
- `--mode-Ic` : Method for computing trigger current \(I_c\)  
  - `daily`  
  - `rolling`  

### Example

```bash
python run_windmi.py \
    --start 2000-01-01T00:00:00 \
    --stop 2000-01-02T00:00:00 \
    --mode-LCS variable \
    --mode-Ic rolling
```

## Installation

Use **Python 3.10 or newer**.

```bash
git clone https://github.com/soumyajitdey/pyWINDMI.git
cd pyWINDMI
```

### Install dependencies

```bash
pip install --upgrade pip
pip install "numpy>=1.23" "pandas>=1.5" "scipy>=1.10" "matplotlib>=3.7" "tqdm>=4.65"
pip install -e .
```

### Verify

```bash
python -m bootstrap
```

## Quick start

Run commands from the repository root.

### Example: constant \(L,C,\Sigma\) with daily \(I_c\)

```bash
python examples/run_windmi.py \
    --start 2000-07-15T00:00:00 \
    --stop 2000-07-19T00:00:00 \
    --mode-LCS constant \
    --mode-Ic daily
```

### Example: constant \(L,C,\Sigma\) with rolling \(I_c\)

```bash
python examples/run_windmi.py \
    --start 2000-07-15T00:00:00 \
    --stop 2000-07-19T00:00:00 \
    --mode-LCS constant \
    --mode-Ic rolling
```

### Example: variable \(L,C,\Sigma\) with rolling \(I_c\)

```bash
python examples/run_windmi.py \
    --start 2000-07-15T00:00:00 \
    --stop 2000-07-19T00:00:00 \
    --mode-LCS variable \
    --mode-Ic rolling
```

### Example with a custom data directory

```bash
python examples/run_windmi.py \
    --start 2000-12-30T00:00:00 \
    --stop 2001-01-05T00:00:00 \
    --mode-LCS variable \
    --mode-Ic daily \
    --data-root /path/to/data
```

### Example without interactive prompts

```bash
python examples/run_windmi.py \
    --start 2000-12-30T00:00:00 \
    --stop 2001-01-05T00:00:00 \
    --mode-LCS constant \
    --mode-Ic rolling \
    --no-prompt
```

## Command-line options

```text
--start              Start datetime in ISO format
--stop               Stop datetime in ISO format
--mode-LCS           constant | variable
--mode-Ic            daily | rolling
--output-dir         Output folder. If omitted, a dated folder is created
--data-root          Optional path to the input-data directory
--ace-url-template   Optional download template for missing ACE files
--no-prompt          Disable interactive download prompts
```

## Mode definitions

### `--mode-LCS`

- `constant`: use the default constant WINDMI parameters `L`, `C`, and `Sigma`.
- `variable`: compute time-dependent `L`, `C`, and `Sigma` from the solar-wind input data at each step.

### `--mode-Ic`

- `daily`: compute one trigger current `I_c` per day from the 70th percentile of the no-trigger current `I` for that day.
- `rolling`: compute `I_c` from a rolling 3-hour window using the 70th percentile of the no-trigger current `I`.

## What the code does

For a typical run, the package:

1. loads the requested ACE files,
2. downloads missing ACE, SuperMAG, and substorm files if allowed,
3. computes the ACE-to-subsolar propagation delay,
4. time-shifts the solar-wind data and interpolates it to a 1-minute grid,
5. computes the WINDMI input voltage,
6. runs the WINDMI model once without the unloading trigger,
7. computes the trigger current series `I_c`,
8. runs the WINDMI model again with the trigger turned on,
9. writes output tables, summary metadata, and a comparison figure.

## Repository layout

```text
pyWINDMI/
├── examples/
│   └── run_windmi.py
├── src/
│   ├── __init__.py
│   ├── bootstrap.py
│   ├── cases.py
│   ├── data.py
│   ├── model.py
│   ├── plotting.py
│   └── triggers.py
├── CITATION.cff
├── LICENSE
├── changelog.md
├── pyproject.toml
├── setup.py
└── README.md
```

## Input Data

If the required input files are not available locally, they are automatically downloaded from the companion repository:

```text
https://github.com/soumyajitdey/ACE_data
```

The code searches for input data in the following order:

1. The directory specified via the `--data-root` argument  
2. The directory set in the `WINDMI_DATA_ROOT` environment variable  
3. A local `./data` directory in the current working path  

The first location that contains the required files is used.

### Required ACE files

Files are expected in the form:

```text
ACE_2000.csv
ACE_2001.csv
...
```

Each ACE file must contain at least these columns:

```text
Time, Bx, By, Bz, Vx, Vy, Vz, Np
```

Column meanings:

- `Time`: timestamp of the ACE measurement.
- `Bx`, `By`, `Bz`: interplanetary magnetic-field components.
- `Vx`, `Vy`, `Vz`: solar-wind velocity components.
- `Np`: proton number density.

### Optional comparison files

These are not required for the model integration itself, but they are used in the comparison plot.

```text
SuperMag_<year>.csv
Substorms_Forsyth_1970_to_2022.csv
Substorms_Frey_1970_to_2022.csv
Substorms_Liou_1970_to_2022.csv
Substorms_Newell_1970_to_2022.csv
Substorms_Ohtani_1970_to_2022.csv
```

Minimum required columns:

- `SuperMag_<year>.csv`: `Date_UTC`, `SML`
- substorm catalog files: `Date_UTC`

## Output

If `--output-dir` is not given, the example script creates a folder like:

```text
outputs/windmi_<mode-LCS>_LCS_<mode-Ic>_Ic_<start-date>_to_<stop-date>
```

Example:

```text
outputs/windmi_variable_LCS_rolling_Ic_2000-07-15_to_2000-07-19
```

The output directory contains the following files.

### 1. `processed_input.csv`

Preprocessed solar-wind input after time shifting and 1-minute interpolation, plus the coupling function used to drive WINDMI. This table is the actual model input.

Expected columns include:

- `Bx`, `By`, `Bz`: IMF components after the WINDMI time shift.
- `Vx`, `Vy`, `Vz`: solar-wind velocity components after the time shift.
- `Np`: proton density after the time shift.
- `vBs`: the computed `vBs` coupling function.
- `input_voltage`: the coupling function actually used by the run. In the current code this is `vBs`.

Notes:

- the time index is the shifted/interpolated 1-minute time grid,
- this file is what the solver actually sees, not the raw ACE table.

### 2. `no_trigger.csv`

WINDMI state variables from the run without the unloading trigger.

Columns:

- `I`: cross-tail current.
- `V`: magnetospheric potential.
- `I1`: region-1/current-sheet branch current used in the model equations.
- `VI`: ionospheric potential.
- `pres`: plasma-sheet pressure.
- `Kk`: plasma-sheet kinetic energy variable.
- `I2`: ring-current / region-2 branch current variable.
- `Wrc`: ring-current energy.

### 3. `with_trigger.csv`

WINDMI state variables from the run with the unloading trigger active.

Columns:

- `I`, `V`, `I1`, `VI`, `pres`, `Kk`, `I2`, `Wrc`: same meanings as in `no_trigger.csv`.
- `I_c`: trigger current threshold used at each time step.

### 4. `variable_parameters.csv`  *(only for `--mode-LCS variable`)*

Time-dependent values of the three model parameters computed from the input data.

Columns:

- `L`: effective inductance used by the model.
- `C`: effective capacitance used by the model.
- `Sigma`: effective conductance parameter used by the model.

This file is written only when `--mode-LCS variable` is used.

### 5. `comparison.png`

A two-panel comparison figure.

- Top panel: `I` from the no-trigger and with-trigger runs, plus `I_c` when available.
- Bottom panel: unloading switch function `Theta`, with optional Newell and Ohtani substorm onset markers, and optional SuperMAG `SML` on the right axis.

### 6. `summary.json`

Run metadata and bookkeeping information.

Current fields include:

- `case`
- `constant_time_delay_seconds`
- `n_input_rows`
- `n_processed_rows`
- `n_no_trigger_rows`
- `n_with_trigger_rows`
- `start_requested`
- `stop_requested`
- `start`
- `stop`
- `years_requested`
- `supermag_available`
- `substorm_catalogs_available`
- `mode_LCS`
- `mode_Ic`
- `output folder`

## Notes

- The package now uses one main example script instead of three separate case scripts.
- The different legacy cases are now reproduced by selecting `--mode-LCS` and `--mode-Ic`.
- Optional comparison files are automatically downloaded when allowed; otherwise the run can still proceed if those files are already present locally.
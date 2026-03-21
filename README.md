# WINDMI_substorms

`WINDMI_substorms` is a small Python package for running three published WINDMI experiment setups from solar-wind input data. The code reads ACE yearly CSV files, applies the built-in ACE-to-magnetopause time-shift, computes the WINDMI driving voltage, solves the 8-variable WINDMI system with `solve_ivp`, and writes model outputs and a comparison figure to disk.

The repository is organized around three example cases:

- **Case 1**: constant `L`, `C`, and `Sigma`, with a **daily** trigger current `I_c`
- **Case 2**: constant `L`, `C`, and `Sigma`, with a **rolling** trigger current `I_c`
- **Case 3**: time-varying `L`, `C`, and `Sigma`, with a **rolling** trigger current `I_c`

## What the package does

At a high level, each run does the following:

1. loads ACE input files for the requested years,
2. downloads missing ACE files automatically if allowed,
3. computes the WINDMI propagation delay from ACE to the subsolar point,
4. resamples the shifted solar-wind data to a 1-minute grid,
5. computes the input coupling voltage (`vBs` by default),
6. runs the WINDMI model,
7. saves output tables and a comparison plot.

Optional SuperMAG and substorm catalog files are used only for the comparison plot. The model run itself does not depend on them.

## Repository layout

```text
WINDMI_substorms/
├── examples/
│   ├── case_1_constant_params_daily_ic.py
│   ├── case_2_constant_params_rolling_ic.py
│   └── case_3_variable_params_rolling_ic.py
├── src/
│   └── windmi_pub/
│       ├── __init__.py
│       ├── bootstrap.py
│       ├── cases.py
│       ├── data.py
│       ├── model.py
│       ├── plotting.py
│       └── triggers.py
├── pyproject.toml
├── setup.py
└── README.md
```

## Input data

By default, the required ACE solar wind data and SuperMAG geomagnetic indices are imported directly from the following repository:

https://github.com/soumyajitdey/ACE_data.git

No manual download is required unless you want to use custom or local datasets.

### Required ACE files

The examples expect yearly ACE CSV files named like:

```text
data/
├── ACE_2000.csv
├── ACE_2001.csv
└── ...
```

Each ACE file must contain at least these columns:

```text
Time, Bx, By, Bz, Vx, Vy, Vz, Np
```

The code looks for input data in this order:

1. the path passed with `--data-root`
2. `WINDMI_DATA_ROOT`
3. `./data` relative to the current working directory

If a required ACE year is missing, the examples can download it automatically from the default template:

```text
https://raw.githubusercontent.com/soumyajitdey/ACE_data/main/ACE_{year}.csv
```

You can override that source with either:

- `--ace-url-template`
- `WINDMI_ACE_URL_TEMPLATE`

### Optional comparison files

These files are optional:

```text
SuperMag_<year>.csv
Substorms_Forsyth_1970_to_2022.csv
Substorms_Frey_1970_to_2022.csv
Substorms_Liou_1970_to_2022.csv
Substorms_Newell_1970_to_2022.csv
Substorms_Ohtani_1970_to_2022.csv
```

If they are present, they are added to the output comparison plot. If they are absent, the model still runs.

## Installation

This package declares the build metadata in `pyproject.toml`, but the runtime dependencies are checked by `windmi_pub.bootstrap` when an example script starts.

### Python version

Use **Python 3.10 or newer**.

### Create an environment

```bash
git clone https://github.com/soumyajitdey/WINDMI_substorms.git
cd WINDMI_substorms
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### Install the package

Editable install:

```bash
pip install -e .
```

Regular install:

```bash
pip install .
```

### Install required runtime packages

The example scripts check for these minimum versions:

- `numpy>=1.23`
- `pandas>=1.5`
- `scipy>=1.10`
- `matplotlib>=3.7`
- `tqdm>=4.65`

Install them with:

```bash
pip install "numpy>=1.23" "pandas>=1.5" "scipy>=1.10" "matplotlib>=3.7" "tqdm>=4.65"
```

You can test the environment with:

```bash
python -m windmi_pub.bootstrap
```

## Running the three example cases

All three examples require only a start time and a stop time in ISO format.

### Case 1: constant parameters with daily `I_c`

```bash
python examples/case_1_constant_params_daily_ic.py --start 2000-12-30T00:00:00 --stop 2001-01-05T00:00:00
```

This run uses the default WINDMI parameters and computes one trigger threshold per day from the 70th percentile of the no-trigger `I` time series.

### Case 2: constant parameters with rolling `I_c`

```bash
python examples/case_2_constant_params_rolling_ic.py --start 2000-12-30T00:00:00 --stop 2001-01-05T00:00:00
```

This run uses the default WINDMI parameters and updates `I_c` with a 3-hour rolling 70th percentile.

### Case 3: variable parameters with rolling `I_c`

```bash
python examples/case_3_variable_params_rolling_ic.py --start 2000-12-30T00:00:00 --stop 2001-01-05T00:00:00
```

This run recalculates `L`, `C`, and `Sigma` from the solar-wind input at each time step, then applies the rolling trigger threshold.

## Useful command-line options

All three example scripts support the same optional arguments:

```text
--output-dir         output folder for results
--data-root          custom directory for ACE / SuperMAG / substorm files
--ace-url-template   custom download template for missing ACE files
--no-prompt          disable interactive download prompts
```

Example with non-interactive download behavior:

```bash
python examples/case_3_variable_params_rolling_ic.py --start 2000-12-30T00:00:00 --stop 2001-01-05T00:00:00 --no-prompt
```

Example with a custom data directory:

```bash
python examples/case_1_constant_params_daily_ic.py --start 2000-01-09T00:00:00 --stop 2000-01-11T23:59:00 --data-root /path/to/data
```

## Output files

Each example writes results into its output directory. Typical outputs are:

```text
processed_input.csv
no_trigger.csv
with_trigger.csv
comparison.png
summary.json
```

Case 3 also writes:

```text
variable_parameters.csv
```

## Notes

- The solver uses the RK45 integrator through `scipy.integrate.solve_ivp`.
- The default input coupling function is `vBs`.
- The comparison figure plots modeled `I`, trigger state `theta`, optional `I_c`, optional SuperMAG `SML`, and available Newell/Ohtani substorm times.

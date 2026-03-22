# pyWINDMI

## Installation

Use **Python 3.10 or newer**.

Clone the repository:

```bash
git clone https://github.com/soumyajitdey/pyWINDMI.git
cd pyWINDMI
```

Install the required packages:

```bash
pip install --upgrade pip
pip install "numpy>=1.23" "pandas>=1.5" "scipy>=1.10" "matplotlib>=3.7" "tqdm>=4.65"
```

Optional editable install:

```bash
pip install -e .
```

Check that the environment is ready:

```bash
python -m windmi_pub.bootstrap
```

## Example runs

Run all commands from the **repository root**.

### Case 1: constant parameters with daily `I_c`

```bash
python examples/case_1_constant_params_daily_ic.py --start 2000-12-30T00:00:00 --stop 2001-01-05T00:00:00
```

### Case 2: constant parameters with rolling `I_c`

```bash
python examples/case_2_constant_params_rolling_ic.py --start 2000-12-30T00:00:00 --stop 2001-01-05T00:00:00
```

### Case 3: variable parameters with rolling `I_c`

```bash
python examples/case_3_variable_params_rolling_ic.py --start 2000-12-30T00:00:00 --stop 2001-01-05T00:00:00
```

### Example with a custom data directory

```bash
python examples/case_1_constant_params_daily_ic.py \
    --start 2000-12-30T00:00:00 \
    --stop 2001-01-05T00:00:00 \
    --data-root /path/to/data
```

### Example without interactive prompts

```bash
python examples/case_2_constant_params_rolling_ic.py \
    --start 2000-12-30T00:00:00 \
    --stop 2001-01-05T00:00:00 \
    --no-prompt
```

## Overview

`pyWINDMI` is a Python package for running three published WINDMI experiment setups from solar-wind input data.

The package reads ACE yearly CSV files, applies the built-in ACE-to-magnetopause time shift, computes the WINDMI driving voltage, solves the 8-variable WINDMI system, and writes model outputs and comparison plots to disk.

## Included example cases

The repository provides three example runs:

- **Case 1**: constant `L`, `C`, and `Sigma`, with a daily trigger current `I_c`
- **Case 2**: constant `L`, `C`, and `Sigma`, with a rolling trigger current `I_c`
- **Case 3**: time-varying `L`, `C`, and `Sigma`, with a rolling trigger current `I_c`

## Repository layout

```text
pyWINDMI/
├── data/
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

## What the code does

For a typical run, the package:

1. loads ACE input files for the requested years,
2. downloads missing ACE files if allowed,
3. computes the ACE-to-subsolar propagation delay,
4. resamples the shifted solar-wind data to a 1-minute grid,
5. computes the input coupling voltage,
6. runs the WINDMI model,
7. saves output tables and figures.

Optional SuperMAG and substorm catalog files are used only for comparison plots. The WINDMI run itself does not require them.

## Input data

By default, ACE and SuperMAG data files are imported from this GitHub repository:

```text
https://github.com/soumyajitdey/ACE_data.git
```

So in most cases, you do not need to manually download the ACE files first.

### Required ACE files

The examples expect yearly ACE CSV files with names like:

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

The code searches for input data in this order:

1. the path passed with `--data-root`
2. the environment variable `WINDMI_DATA_ROOT`
3. `./data` relative to the current working directory

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

If present, they are added to the comparison plots. If absent, the model still runs.

## Common command-line options

All three examples accept the same main options:

```text
--start            Start datetime in ISO format
--stop             Stop datetime in ISO format
--output-dir       Output folder
--data-root        Optional path to input data
--ace-url-template Optional download template for missing ACE files
--no-prompt        Disable download prompts for missing ACE files
```

## Output

Each example writes results to its own output directory by default:

- `outputs/case_1_constant_daily_ic`
- `outputs/case_2_constant_rolling_ic`
- `outputs/case_3_variable_rolling_ic`

The output directory contains model results and comparison figures.

## Notes

- The internal Python source folder is currently `src/windmi_pub/`.
- The example scripts already add `src/` to `sys.path`, so running them from the repo root is enough.
- You do not need to rename `windmi_pub` to use the examples.

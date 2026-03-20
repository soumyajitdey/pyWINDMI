# windmi-pub

`windmi-pub` is a lightweight Python package built from the `windmi_pub.ipynb` notebook. It exposes the shared preprocessing and solver logic as reusable code, and keeps the three notebook cases as runnable example scripts.

## Model summary

The package does the following:
- loads yearly ACE solar-wind inputs,
- applies the notebook time-shift logic,
- computes the driving voltage used by WINDMI,
- runs WINDMI for the three notebook cases,
- writes CSV outputs and a comparison plot into an output folder.

## Case mapping from the notebook

- **Case 1**: constant `L`, `C`, `Sigma` with daily `I_c`
- **Case 2**: constant `L`, `C`, `Sigma` with rolling `I_c`
- **Case 3**: variable `L`, `C`, `Sigma` with rolling `I_c`

## Repository layout

```text
windmi_pub_package/
├── examples/
│   ├── case_1_constant_daily_ic.py
│   ├── case_2_constant_rolling_ic.py
│   └── case_3_variable_rolling_ic.py
├── src/windmi_pub/
│   ├── bootstrap.py
│   ├── cases.py
│   ├── data.py
│   ├── model.py
│   ├── plotting.py
│   └── triggers.py
├── pyproject.toml
├── setup.py
└── README.md
```

## Input data

By default the package looks for input files in:

1. `WINDMI_DATA_ROOT`, if that environment variable is set, or
2. `./data` relative to the current working directory.

### ACE files

The package expects yearly CSV files named like:

```text
data/
├── ACE_2000.csv
├── ACE_2001.csv
└── ...
```

Each ACE file must contain at least:

```text
Time, Bx, By, Bz, Vx, Vy, Vz, Np
```

If a requested ACE year is missing, the example script will:
- check which yearly ACE files are needed,
- use the files already present,
- prompt to download any missing years,
- download missing years automatically from the public GitHub repository `soumyajitdey/ACE_data`,
- cache those files locally under your data directory for future runs.

The built-in default download template is:

```text
https://raw.githubusercontent.com/soumyajitdey/ACE_data/main/ACE_{year}.csv
```

You can still override that default with either:
- `--ace-url-template`, or
- `WINDMI_ACE_URL_TEMPLATE`

### SuperMAG and substorm files

These are optional for running WINDMI.
If present, they are used for the comparison plot. If absent, the model still runs.

Optional files:

```text
data/
├── SuperMag_2000.csv
├── SuperMag_2001.csv
├── ...
├── Substorms_Forsyth_1970_to_2022.csv
├── Substorms_Frey_1970_to_2022.csv
├── Substorms_Liou_1970_to_2022.csv
├── Substorms_Newell_1970_to_2022.csv
└── Substorms_Ohtani_1970_to_2022.csv
```

## Installation

This repository does **not** auto-install third-party runtime packages.
Install the package normally, then make sure the required runtime packages are already available in your Python environment.
If a required package is missing or too old, the example scripts stop with a clear error message.

### Editable install

```bash
git clone <your-github-repo-url>
cd windmi_pub_package
pip install -e .
```

### Regular install

```bash
pip install .
```

### Manual dependency check

```bash
python -m windmi_pub.bootstrap
```

## Runtime packages checked at startup

- `numpy>=1.23`
- `pandas>=1.5`
- `scipy>=1.10`
- `matplotlib>=3.7`
- `tqdm>=4.65`

## Running the example cases

The examples require only `--start` and `--stop`. They support ranges across multiple years, for example `2000-12-30` to `2001-01-05`.

### Case 1

```bash
python examples/case_1_constant_daily_ic.py \
    --start 2000-12-30T00:00:00 \
    --stop 2001-01-05T00:00:00
```

### Case 2

```bash
python examples/case_2_constant_rolling_ic.py \
    --start 2000-12-30T00:00:00 \
    --stop 2001-01-05T00:00:00
```

### Case 3

```bash
python examples/case_3_variable_rolling_ic.py \
    --start 2000-12-30T00:00:00 \
    --stop 2001-01-05T00:00:00
```

### With automatic ACE download for missing years

```bash
python examples/case_3_variable_rolling_ic.py \
    --start 2000-12-30T00:00:00 \
    --stop 2001-01-05T00:00:00
```

### Non-interactive mode

```bash
python examples/case_3_variable_rolling_ic.py \
    --start 2000-12-30T00:00:00 \
    --stop 2001-01-05T00:00:00 \
    --no-prompt
```

### Override the default ACE download source

```bash
python examples/case_3_variable_rolling_ic.py \
    --start 2000-12-30T00:00:00 \
    --stop 2001-01-05T00:00:00 \
    --ace-url-template "https://your-server/path/ACE_{year}.csv"
```

### Optional output override

```bash
python examples/case_3_variable_rolling_ic.py \
    --start 2000-12-30T00:00:00 \
    --stop 2001-01-05T00:00:00 \
    --output-dir ./outputs/custom_case3_run
```

## Output files

Each example writes a folder containing files such as:
- `processed_input.csv`
- `no_trigger.csv`
- `with_trigger.csv`
- `summary.json`
- `comparison.png`

Case 3 also writes:
- `variable_parameters.csv`

## Notes

- The WINDMI core functions were left unchanged.
- The package now supports cross-year runs by loading only the years needed for the requested interval.
- Missing SuperMAG and substorm files no longer block the model run.

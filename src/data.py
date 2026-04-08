from __future__ import annotations

import datetime as dt
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

SUBSTORM_KEYS = ("Forsyth", "Frey", "Liou", "Newell", "Ohtani")
ACE_REQUIRED_COLUMNS = ("Time", "Bx", "By", "Bz", "Vx", "Vy", "Vz", "Np")
SUPERMAG_REQUIRED_COLUMNS = ("Date_UTC", "SML")
SUBSTORM_REQUIRED_COLUMNS = ("Date_UTC",)
DEFAULT_ACE_URL_TEMPLATE = "https://raw.githubusercontent.com/soumyajitdey/ACE_data/main/ACE_{year}.csv"
DEFAULT_SUPERMAG_URL_TEMPLATE = "https://raw.githubusercontent.com/soumyajitdey/ACE_data/main/SuperMag_{year}.csv"
DEFAULT_SUBSTORM_URL_TEMPLATE = "https://raw.githubusercontent.com/soumyajitdey/ACE_data/main/Substorms_{key}_1970_to_2022.csv"

def resolve_data_root(data_root: str | os.PathLike[str] | None = None) -> Path:
    if data_root is not None:
        root = Path(data_root).expanduser().resolve()
    elif os.environ.get("WINDMI_DATA_ROOT"):
        root = Path(os.environ["WINDMI_DATA_ROOT"]).expanduser().resolve()
    else:
        root = (Path.cwd() / "data").resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _ensure_columns(frame: pd.DataFrame, required: Iterable[str], file_path: Path) -> None:
    missing = [col for col in required if col not in frame.columns]
    if missing:
        raise ValueError(f"Missing columns {missing} in {file_path}")


def _requested_years(start: dt.datetime, stop: dt.datetime) -> list[int]:
    if stop < start:
        raise ValueError("stop must be later than start")
    return list(range(start.year, stop.year + 1))


def _missing_ace_files(root: Path, years: Iterable[int]) -> list[Path]:
    return [root / f"ACE_{year}.csv" for year in years if not (root / f"ACE_{year}.csv").exists()]


def _is_interactive() -> bool:
    try:
        return sys.stdin.isatty()
    except Exception:
        return False


def _prompt_yes_no(message: str, default: bool = True) -> bool:
    if not _is_interactive():
        return default
    suffix = "[Y/n]" if default else "[y/N]"
    reply = input(f"{message} {suffix} ").strip().lower()
    if not reply:
        return default
    return reply in {"y", "yes"}


def _prompt_text(message: str) -> str:
    if not _is_interactive():
        return ""
    return input(message).strip()


def download_ace_year(
    year: int,
    root: Path,
    url_template: str,
    timeout: int = 120,
) -> Path:
    if "{year}" not in url_template:
        raise ValueError("ACE URL template must contain '{year}'")

    root.mkdir(parents=True, exist_ok=True)
    url = url_template.format(year=year)
    destination = root / f"ACE_{year}.csv"
    tmp_destination = destination.with_suffix(".csv.part")

    try:
        with urllib.request.urlopen(url, timeout=timeout) as response, open(tmp_destination, "wb") as out:
            out.write(response.read())
        frame = pd.read_csv(tmp_destination)
        _ensure_columns(frame, ACE_REQUIRED_COLUMNS, tmp_destination)
        tmp_destination.replace(destination)
    except urllib.error.URLError as exc:
        if tmp_destination.exists():
            tmp_destination.unlink()
        raise RuntimeError(f"Failed to download ACE data for {year} from {url}: {exc}") from exc
    except Exception:
        if tmp_destination.exists():
            tmp_destination.unlink()
        raise
    return destination


def ensure_ace_data(
    root: Path,
    start: dt.datetime,
    stop: dt.datetime,
    *,
    download_missing: bool = True,
    prompt: bool = True,
    ace_url_template: str | None = None,
) -> None:
    years = _requested_years(start, stop)
    missing_files = _missing_ace_files(root, years)
    if not missing_files:
        return

    missing_years = [path.stem.split("_")[-1] for path in missing_files]
    template = ace_url_template or os.environ.get("WINDMI_ACE_URL_TEMPLATE") or DEFAULT_ACE_URL_TEMPLATE

    if not download_missing:
        missing_list = ", ".join(path.name for path in missing_files)
        raise FileNotFoundError(
            "Missing ACE input files: "
            f"{missing_list}. Automatic download is disabled, so add them under {root}."
        )

    if prompt and _is_interactive():
        print(f"Missing ACE files for years: {', '.join(missing_years)}")
        if not _prompt_yes_no("Download the missing ACE files now?", default=True):
            missing_list = ", ".join(path.name for path in missing_files)
            raise FileNotFoundError(
                "Missing ACE input files: "
                f"{missing_list}. Add them under {root} or allow the script to download them."
            )

    for year in years:
        destination = root / f"ACE_{year}.csv"
        if destination.exists():
            continue
        if prompt and _is_interactive():
            print(f"Downloading {destination.name} from {template.format(year=year)} ...")
        download_ace_year(year, root=root, url_template=template)


def _load_yearly_csvs(
    root: Path,
    prefix: str,
    start: dt.datetime,
    stop: dt.datetime,
    time_column: str,
    required_columns: Iterable[str],
) -> pd.DataFrame:
    frames = []
    for year in _requested_years(start, stop):
        file_path = root / f"{prefix}_{year}.csv"
        if not file_path.exists():
            raise FileNotFoundError(f"Required input file not found: {file_path}")
        frame = pd.read_csv(file_path)
        _ensure_columns(frame, required_columns, file_path)
        frame.index = pd.to_datetime(frame[time_column])
        frame = frame.drop(columns=[time_column])
        frames.append(frame)
    data = pd.concat(frames).sort_index()
    return data.loc[(data.index >= start - dt.timedelta(hours=2)) & (data.index <= stop + dt.timedelta(hours=2))]


def load_ace(root: Path, start: dt.datetime, stop: dt.datetime) -> pd.DataFrame:
    '''Loads ACE data for the specified time range. 
    Expects files named ACE_{year}.csv with columns: Time, Bx, By, Bz, Vx, Vy, Vz, Np.'''
    return _load_yearly_csvs(root, "ACE", start, stop, "Time", ACE_REQUIRED_COLUMNS)

def _download_csv(
    *,
    url: str,
    destination: Path,
    required_columns: Iterable[str],
    timeout: int = 120,
) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp_destination = destination.with_suffix(destination.suffix + ".part")
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response, open(tmp_destination, "wb") as out:
            out.write(response.read())
        frame = pd.read_csv(tmp_destination)
        _ensure_columns(frame, required_columns, tmp_destination)
        tmp_destination.replace(destination)
    except urllib.error.URLError as exc:
        if tmp_destination.exists():
            tmp_destination.unlink()
        raise RuntimeError(f"Failed to download file from {url}: {exc}") from exc
    except Exception:
        if tmp_destination.exists():
            tmp_destination.unlink()
        raise
    return destination


def download_supermag_year(
    year: int,
    root: Path,
    url_template: str,
    timeout: int = 120,
) -> Path:
    if "{year}" not in url_template:
        raise ValueError("SuperMAG URL template must contain '{year}'")
    url = url_template.format(year=year)
    destination = root / f"SuperMag_{year}.csv"
    return _download_csv(
        url=url,
        destination=destination,
        required_columns=SUPERMAG_REQUIRED_COLUMNS,
        timeout=timeout,
    )


def download_substorm_catalog(
    key: str,
    root: Path,
    url_template: str,
    timeout: int = 120,
) -> Path:
    if "{key}" not in url_template:
        raise ValueError("Substorm URL template must contain '{key}'")
    url = url_template.format(key=key)
    destination = root / f"Substorms_{key}_1970_to_2022.csv"
    return _download_csv(
        url=url,
        destination=destination,
        required_columns=SUBSTORM_REQUIRED_COLUMNS,
        timeout=timeout,
    )

def _missing_supermag_files(root: Path, years: Iterable[int]) -> list[Path]:
    return [root / f"SuperMag_{year}.csv" for year in years if not (root / f"SuperMag_{year}.csv").exists()]


def _missing_substorm_files(root: Path) -> list[Path]:
    return [
        root / f"Substorms_{key}_1970_to_2022.csv"
        for key in SUBSTORM_KEYS
        if not (root / f"Substorms_{key}_1970_to_2022.csv").exists()
    ]


def ensure_supermag_data(
    root: Path,
    start: dt.datetime,
    stop: dt.datetime,
    *,
    download_missing: bool = True,
    prompt: bool = True,
    supermag_url_template: str | None = None,
) -> None:
    years = _requested_years(start, stop)
    missing_files = _missing_supermag_files(root, years)
    if not missing_files:
        return

    template = (
        supermag_url_template
        or os.environ.get("WINDMI_SUPERMAG_URL_TEMPLATE")
        or DEFAULT_SUPERMAG_URL_TEMPLATE
    )

    if not download_missing:
        missing_list = ", ".join(path.name for path in missing_files)
        raise FileNotFoundError(
            f"Missing SuperMAG input files: {missing_list}. "
            f"Automatic download is disabled, so add them under {root}."
        )

    if prompt and _is_interactive():
        missing_years = [path.stem.split("_")[-1] for path in missing_files]
        print(f"Missing SuperMAG files for years: {', '.join(missing_years)}")
        if not _prompt_yes_no("Download the missing SuperMAG files now?", default=True):
            missing_list = ", ".join(path.name for path in missing_files)
            raise FileNotFoundError(
                f"Missing SuperMAG input files: {missing_list}. "
                f"Add them under {root} or allow the script to download them."
            )

    for year in years:
        destination = root / f"SuperMag_{year}.csv"
        if destination.exists():
            continue
        if prompt and _is_interactive():
            print(f"Downloading {destination.name} from {template.format(year=year)} ...")
        download_supermag_year(year, root=root, url_template=template)


def ensure_substorm_data(
    root: Path,
    *,
    download_missing: bool = True,
    prompt: bool = True,
    substorm_url_template: str | None = None,
) -> None:
    missing_files = _missing_substorm_files(root)
    if not missing_files:
        return

    template = (
        substorm_url_template
        or os.environ.get("WINDMI_SUBSTORM_URL_TEMPLATE")
        or DEFAULT_SUBSTORM_URL_TEMPLATE
    )

    if not download_missing:
        missing_list = ", ".join(path.name for path in missing_files)
        raise FileNotFoundError(
            f"Missing substorm catalog files: {missing_list}. "
            f"Automatic download is disabled, so add them under {root}."
        )

    if prompt and _is_interactive():
        missing_names = [path.name for path in missing_files]
        print("Missing substorm catalogs:")
        for name in missing_names:
            print(f"  - {name}")
        if not _prompt_yes_no("Download the missing substorm catalogs now?", default=True):
            missing_list = ", ".join(path.name for path in missing_files)
            raise FileNotFoundError(
                f"Missing substorm catalog files: {missing_list}. "
                f"Add them under {root} or allow the script to download them."
            )

    for key in SUBSTORM_KEYS:
        destination = root / f"Substorms_{key}_1970_to_2022.csv"
        if destination.exists():
            continue
        if prompt and _is_interactive():
            print(f"Downloading {destination.name} from {template.format(key=key)} ...")
        download_substorm_catalog(key, root=root, url_template=template)

def load_supermag(root: Path, start: dt.datetime, stop: dt.datetime) -> pd.DataFrame:
    '''Loads SuperMAG SML index for the specified time range.
    Expects files named SuperMag_{year}.csv with columns: Date_UTC, SML.'''
    try:
        return _load_yearly_csvs(root, "SuperMag", start, stop, "Date_UTC", SUPERMAG_REQUIRED_COLUMNS).loc[start:stop]
    except FileNotFoundError:
        return pd.DataFrame()


def load_substorm_lists(root: Path, start: dt.datetime, stop: dt.datetime) -> dict[str, pd.DataFrame]:
    '''loads existing substorm lists:
    - Forsyth et al. (2015)
    - Frey et al. (2004)
    - Liou et al. (2001)
    - Newell and Gjerloev (2011)
    - Ohtani et al. (2019)
    '''
    out: dict[str, pd.DataFrame] = {}
    for key in SUBSTORM_KEYS:
        file_path = root / f"Substorms_{key}_1970_to_2022.csv"
        if not file_path.exists():
            continue
        frame = pd.read_csv(file_path)
        _ensure_columns(frame, SUBSTORM_REQUIRED_COLUMNS, file_path)
        frame.index = pd.to_datetime(frame["Date_UTC"])
        out[key] = frame.loc[start:stop]
    return out


def compute_time_delay(data: pd.DataFrame) -> tuple[float, pd.Series]:
    '''Compute the time delay from ACE to the subsolar point using Shue et al. (1998) formula.'''
    dp = 1.67e-6 * data["Np"] * data["Vx"] ** 2
    r_subsolar = (10.22 + 1.29 * np.tanh(0.184 * (data["Bz"] + 8.14))) * (dp ** (-1 / 6.6)) # distance of subsolar point in Earth radii
    t_delay = -((250.0 - np.nanmean(r_subsolar)) * 6380.0) / np.nanmean(data["Vx"]) # constant time delay in seconds
    t_delay_windmi = -((250.0 - r_subsolar) * 6380.0) / data["Vx"].rolling(window=20, min_periods=1, center=True).mean() # time delay series with rolling mean to smooth out short-term fluctuations
    return float(t_delay), t_delay_windmi


def apply_windmi_time_shift(data: pd.DataFrame, t_delay_windmi: pd.Series) -> pd.DataFrame:
    '''Apply the time shift to the ACE data to align it with the subsolar point.'''
    data_shifted = data.copy()
    data_shifted.index = data_shifted.index + pd.to_timedelta(t_delay_windmi, unit="s")
    data_shifted = data_shifted.sort_index()
    data_shifted = data_shifted[~data_shifted.index.isna()]
    data_shifted = data_shifted[~data_shifted.index.duplicated(keep="first")]

    t_start = data_shifted.index.min().floor("min")
    t_end = data_shifted.index.max().ceil("min")
    x0 = np.array((data_shifted.index - t_start) / dt.timedelta(seconds=1))
    x1_time = pd.date_range(t_start, t_end, freq="1min")
    x1 = np.array((x1_time - t_start) / dt.timedelta(seconds=1))

    out = pd.DataFrame(index=x1_time)
    for col in data_shifted.columns:
        y0 = data_shifted[col].values
        y1 = interp1d(x0, y0, kind="linear", bounds_error=False, fill_value=np.nan)(x1)
        out[col] = y1

    out = out.dropna()
    out.index.name = "time"
    return out


def compute_input_voltage(data: pd.DataFrame, coupling: str = "vBs", f107: float = 172.42) -> pd.DataFrame:
    '''Compute the input voltage (coupling function) from the ACE data.
    Supported coupling functions:
    - vBs: 4000 + 1e-6 * ly * |Vx * max(0, -Bz)|
    - SH: Siscoe-Hill formula
    - Newell: Newell coupling function
    Default is vBs.
    f10.7 only needed for SH forula to compute the saturation potential, but is ignored for other formulas.
    '''
    # bx = data["Bx"]
    # by = data["By"]
    bz = data["Bz"]
    vx = data["Vx"]
    # vy = data["Vy"]
    # vz = data["Vz"]
    # np_sw = data["Np"]

    # VBs formula
    r_e = 6380.0e3
    ly = 10.0 * r_e
    bz_input = 0.5 * (np.abs(bz) - bz)
    vbs = 4000.0 + (1.0e-6 * ly * np.abs(vx * bz_input))

    # # Siscoe-Hill formula
    # m_p = 1.67e-27
    # b_abs = np.sqrt(bx ** 2 + by ** 2 + bz ** 2).replace(0, np.nan)
    # theta = np.arccos(np.clip(bz / b_abs, -1.0, 1.0))
    # v_sw = np.sqrt(vx ** 2 + vy ** 2 + vz ** 2)
    # esw = (v_sw * 1e3) * (np.sqrt(by ** 2 + bz ** 2) * 1e-9) * np.sin(theta / 2.0)
    # psw = m_p * (np_sw * 1.0e6) * ((v_sw * 1.0e3) ** 2)
    # phi_m = 30.0 + (57.6 * (esw * 1.0e3) * ((1.0e9 * psw) ** (-1.0 / 6.0)))
    # c0 = 0.77
    # sigma_p = c0 * np.sqrt(f107)
    # phi_s = 1600.0 * ((psw * 1.0e9) ** (1 / 3)) / sigma_p # saturation potential
    # phi_h = (phi_m * phi_s) / (phi_m + phi_s) # Hill potential 

    # # Newell formula
    # dphi_mp = (np.abs(vx) ** (4 / 3)) * (b_abs ** (2 / 3)) * (np.sin(theta / 2.0) ** (8 / 3))
    # scale = np.nanmean(vbs) / np.nanmean(dphi_mp)
    # newell_scaled = 4000.0 + scale * dphi_mp

    out = data.copy()
    out["vBs"] = vbs
    # out["SH"] = 1e3 * phi_m
    # out["Newell"] = newell_scaled
    if coupling not in out.columns:
        raise ValueError(f"Unknown coupling function '{coupling}'. Valid options: vBs, SH, Newell)")
    out["input_voltage"] = out[coupling]
    return out


def prepare_inputs(
    start: dt.datetime,
    stop: dt.datetime,
    data_root: str | os.PathLike[str] | None = None,
    coupling: str = "vBs",
    *,
    download_missing_ace: bool = True,
    download_missing_supermag: bool = True,
    download_missing_substorms: bool = True,
    prompt_for_download: bool = True,
    ace_url_template: str | None = None,
    supermag_url_template: str | None = None,
    substorm_url_template: str | None = None,
):
    root = resolve_data_root(data_root)

    ensure_ace_data(
        root,
        start,
        stop,
        download_missing=download_missing_ace,
        prompt=prompt_for_download,
        ace_url_template=ace_url_template,
    )

    ensure_supermag_data(
        root,
        start,
        stop,
        download_missing=download_missing_supermag,
        prompt=prompt_for_download,
        supermag_url_template=supermag_url_template,
    )

    ensure_substorm_data(
        root,
        download_missing=download_missing_substorms,
        prompt=prompt_for_download,
        substorm_url_template=substorm_url_template,
    )

    ace = load_ace(root, start, stop)
    supermag = load_supermag(root, start, stop)
    substorms = load_substorm_lists(root, start, stop)

    constant_delay, delay_series = compute_time_delay(ace)
    shifted = apply_windmi_time_shift(ace, delay_series)
    processed = compute_input_voltage(shifted.loc[start:stop], coupling=coupling)

    meta = {
        "constant_time_delay_seconds": float(constant_delay),
        "n_input_rows": int(len(processed)),
        "start_requested": start.isoformat(),
        "stop_requested": stop.isoformat(),
        "years_requested": _requested_years(start, stop),
        "supermag_available": not supermag.empty,
        "substorm_catalogs_available": sorted(substorms.keys()),
    }
    return processed, supermag, substorms, meta

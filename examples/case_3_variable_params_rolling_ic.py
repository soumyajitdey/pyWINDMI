#!/usr/bin/env python
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / 'src'
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from bootstrap import ensure_dependencies

ensure_dependencies(quiet=False)
from cases import run_case_3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run WINDMI case 3: variable L, C, Sigma with rolling I_c.")
    parser.add_argument("--start", required=True, help="Start datetime, for example 2000-12-30T00:00:00")
    parser.add_argument("--stop", required=True, help="Stop datetime, for example 2001-01-05T00:00:00")
    parser.add_argument(
    "--output-dir",
    default=None,
    help="Output folder. If not provided, a dated folder is created.",
    )
    parser.add_argument(
        "--data-root",
        default=None,
        help="Optional input data directory. If omitted, the script uses WINDMI_DATA_ROOT or ./data",
    )
    parser.add_argument(
        "--ace-url-template",
        default=None,
        help="Optional download template for missing ACE files. By default the script downloads from soumyajitdey/ACE_data on GitHub.",
    )
    parser.add_argument(
        "--no-prompt",
        action="store_true",
        help="Disable interactive prompts when ACE files are missing.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    start = dt.datetime.fromisoformat(args.start)
    stop = dt.datetime.fromisoformat(args.stop)
    if args.output_dir is None:
        start_str = start.strftime("%Y-%m-%d")
        stop_str = stop.strftime("%Y-%m-%d")
        output_dir = Path("outputs") / f"case_3_variable_rolling_ic_{start_str}_to_{stop_str}"
    else:
        output_dir = Path(args.output_dir)
    out_dir = run_case_3(
        start=start,
        stop=stop,
        output_dir=output_dir,
        data_root=args.data_root,
        ace_url_template=args.ace_url_template,
        prompt_for_download=not args.no_prompt,
    )
    print(f"Finished. Outputs written to: {out_dir}")


if __name__ == "__main__":
    main()

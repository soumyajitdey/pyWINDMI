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

from windmi_pub.bootstrap import ensure_dependencies

ensure_dependencies(quiet=False)
from windmi_pub.cases import run_case_2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run WINDMI case 2: constant L, C, Sigma with rolling I_c.")
    parser.add_argument("--start", required=True, help="Start datetime, for example 2000-12-30T00:00:00")
    parser.add_argument("--stop", required=True, help="Stop datetime, for example 2001-01-05T00:00:00")
    parser.add_argument(
        "--output-dir",
        default=str(Path("outputs") / "case_2_constant_rolling_ic"),
        help="Output folder. Default: outputs/case_2_constant_rolling_ic",
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
    out_dir = run_case_2(
        start=start,
        stop=stop,
        output_dir=args.output_dir,
        data_root=args.data_root,
        ace_url_template=args.ace_url_template,
        prompt_for_download=not args.no_prompt,
    )
    print(f"Finished. Outputs written to: {out_dir}")


if __name__ == "__main__":
    main()

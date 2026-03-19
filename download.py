#!/usr/bin/env python3
"""
Download CMS CPSC monthly enrollment files.

CMS publishes ZIP files at a predictable URL pattern:
  https://www.cms.gov/files/zip/monthly-enrollment-cpsc-{month}-{year}.zip

Each ZIP contains a single CSV (~180MB uncompressed).
"""

import calendar
import zipfile
from datetime import date, datetime
from pathlib import Path
from urllib.request import urlretrieve
from urllib.error import HTTPError


BASE_URL = "https://www.cms.gov/files/zip/monthly-enrollment-cpsc-{month}-{year}.zip"
DATA_DIR = Path("data/raw")


def cpsc_url(year: int, month: int) -> str:
    month_name = calendar.month_name[month].lower()
    return BASE_URL.format(month=month_name, year=year)


def download_cpsc(year: int, month: int, dest_dir: Path = DATA_DIR) -> Path:
    """Download and extract a CPSC enrollment file. Returns path to the CSV."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    label = f"{year}-{month:02d}"
    csv_path = dest_dir / f"{label}.csv"

    if csv_path.exists():
        print(f"Already have {csv_path}")
        return csv_path

    url = cpsc_url(year, month)
    zip_path = dest_dir / f"{label}.zip"

    print(f"Downloading {url} ...")
    try:
        urlretrieve(url, zip_path)
    except HTTPError as e:
        raise RuntimeError(f"Failed to download {url}: {e}") from e

    print(f"Extracting {zip_path} ...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if not csv_names:
            raise RuntimeError(f"No CSV found in {zip_path}")
        # Extract the first CSV and rename to our standard naming
        zf.extract(csv_names[0], dest_dir)
        extracted = dest_dir / csv_names[0]
        extracted.rename(csv_path)

    zip_path.unlink()
    print(f"Saved {csv_path} ({csv_path.stat().st_size / 1e6:.1f} MB)")
    return csv_path


def download_month_pair(year: int, month: int) -> tuple[Path, Path]:
    """Download current month and the month before it."""
    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1

    prev_csv = download_cpsc(prev_year, prev_month)
    curr_csv = download_cpsc(year, month)
    return prev_csv, curr_csv


def latest_available() -> tuple[int, int]:
    """Guess the latest available month (CMS publishes ~6 weeks after month end)."""
    today = date.today()
    # Back up 2 months to be safe
    m = today.month - 2
    y = today.year
    if m <= 0:
        m += 12
        y -= 1
    return y, m


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Download CMS CPSC enrollment data")
    parser.add_argument("--year", type=int, help="Year (default: latest available)")
    parser.add_argument("--month", type=int, help="Month (default: latest available)")
    parser.add_argument("--pair", action="store_true", help="Download this month AND the previous month")
    args = parser.parse_args()

    if args.year and args.month:
        y, m = args.year, args.month
    else:
        y, m = latest_available()
        print(f"Guessing latest available: {calendar.month_name[m]} {y}")

    if args.pair:
        prev, curr = download_month_pair(y, m)
        print(f"\nReady to run:\n  python run.py {prev} {curr}")
    else:
        path = download_cpsc(y, m)
        print(f"\nDownloaded: {path}")

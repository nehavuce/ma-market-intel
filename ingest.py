"""
Ingest and normalize CMS Medicare Advantage CPSC enrollment files.

CMS publishes monthly enrollment by Contract-Plan-State-County (CPSC).
Source: https://www.cms.gov/data-research/statistics-trends-and-reports/
        medicare-advantagepart-d-contract-and-enrollment-data/monthly-enrollment-cpsc

Files are ~180MB CSVs. This module reads them into a standardized format
and caches as parquet for faster reloads.
"""

import pandas as pd
from pathlib import Path


# CMS column names vary slightly across years — normalize here
COLUMN_MAP = {
    "Contract Number": "contract_id",
    "Plan ID": "plan_id",
    "State": "state",
    "County": "county",
    "FIPS State County Code": "fips",
    "Enrollment": "enrollment",
    "Organization Name": "org_name",
    "Organization Marketing Name": "carrier",
    "Plan Type": "plan_type",
    "Parent Organization": "parent_org",
}


def load_cpsc_file(csv_path: str | Path) -> pd.DataFrame:
    """Load a CMS CPSC enrollment CSV and return a normalized DataFrame."""
    csv_path = Path(csv_path)
    parquet_path = csv_path.with_suffix(".parquet")

    # Use cached parquet if it exists and is newer than the CSV
    if parquet_path.exists() and parquet_path.stat().st_mtime > csv_path.stat().st_mtime:
        return pd.read_parquet(parquet_path)

    df = pd.read_csv(csv_path, dtype=str, low_memory=False)

    # Normalize column names
    rename = {}
    for orig, norm in COLUMN_MAP.items():
        matches = [c for c in df.columns if orig.lower() in c.lower()]
        if matches:
            rename[matches[0]] = norm
    df = df.rename(columns=rename)

    # Coerce enrollment to numeric
    if "enrollment" in df.columns:
        df["enrollment"] = pd.to_numeric(df["enrollment"], errors="coerce").fillna(0).astype(int)

    # Cache as parquet
    df.to_parquet(parquet_path, index=False)
    print(f"Cached {parquet_path.name} ({len(df):,} rows)")

    return df


def aggregate_by_county_carrier(df: pd.DataFrame) -> pd.DataFrame:
    """Roll up plan-level data to county + carrier level."""
    group_cols = [c for c in ["fips", "state", "county", "carrier", "parent_org", "contract_id"] if c in df.columns]
    return (
        df.groupby(group_cols, as_index=False)
        .agg(enrollment=("enrollment", "sum"))
    )

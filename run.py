#!/usr/bin/env python3
"""
MA Market Intel — Monthly pipeline runner.

Usage:
    # Basic: compare two months of CMS CPSC data
    python run.py data/raw/2026-01.csv data/raw/2026-02.csv

    # With proprietary data supplement
    python run.py data/raw/2026-01.csv data/raw/2026-02.csv --proprietary data/internal/feb_metrics.csv

    # Custom thresholds
    python run.py data/raw/2026-01.csv data/raw/2026-02.csv --config config/thresholds.json
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

from ingest import load_cpsc_file, aggregate_by_county_carrier
from deltas import compute_deltas, flag_outliers, top_movers
from analyst import generate_monthly_report, update_trend_analysis, generate_management_report


def main():
    parser = argparse.ArgumentParser(description="MA Market Intel pipeline")
    parser.add_argument("previous", help="Path to previous month's CPSC CSV")
    parser.add_argument("current", help="Path to current month's CPSC CSV")
    parser.add_argument("--config", default="config/thresholds.json", help="Thresholds config")
    parser.add_argument("--proprietary", help="Path to proprietary data CSV (optional)")
    parser.add_argument("--audience", default="VP of Growth", help="Target audience for management report")
    parser.add_argument("--month", help="Month label (e.g., 'February 2026'). Auto-detected if not set.")
    parser.add_argument("--skip-claude", action="store_true", help="Only run data pipeline, skip Claude analysis")
    args = parser.parse_args()

    month_label = args.month or Path(args.current).stem

    # --- Step 1: Ingest ---
    print(f"Loading previous month: {args.previous}")
    prev_df = load_cpsc_file(args.previous)
    print(f"Loading current month: {args.current}")
    curr_df = load_cpsc_file(args.current)

    # --- Step 2: Aggregate ---
    print("Aggregating to county + carrier level...")
    prev_agg = aggregate_by_county_carrier(prev_df)
    curr_agg = aggregate_by_county_carrier(curr_df)
    print(f"  Previous: {len(prev_agg):,} county-carrier combos")
    print(f"  Current:  {len(curr_agg):,} county-carrier combos")

    # --- Step 3: Compute deltas ---
    print("Computing deltas...")
    deltas = compute_deltas(curr_agg, prev_agg)
    deltas = flag_outliers(deltas, args.config)
    movers = top_movers(deltas)
    print(f"  {movers['total_flagged']:,} flagged out of {movers['total_rows']:,} rows")

    # Save processed deltas
    output_dir = Path("output/reports")
    output_dir.mkdir(parents=True, exist_ok=True)
    deltas_path = output_dir / f"deltas_{month_label}.parquet"
    deltas.to_parquet(deltas_path, index=False)
    print(f"  Saved deltas to {deltas_path}")

    # Save movers JSON (useful for debugging or feeding to other tools)
    movers_path = output_dir / f"movers_{month_label}.json"
    movers_path.write_text(json.dumps(movers, indent=2, default=str))

    if args.skip_claude:
        print("Skipping Claude analysis (--skip-claude). Data outputs saved.")
        return

    # --- Step 4: Claude analysis ---
    print("\nGenerating monthly report with Claude...")
    report = generate_monthly_report(movers, month_label)
    report_path = output_dir / f"report_{month_label}.md"
    report_path.write_text(report)
    print(f"  Saved report to {report_path}")

    print("Updating running trend analysis...")
    update_trend_analysis(movers, month_label)
    print("  Updated output/trends/running_trend.md")

    # --- Step 5 (optional): Management report with proprietary data ---
    if args.proprietary:
        print(f"\nLoading proprietary data: {args.proprietary}")
        # Read proprietary CSV and convert to text summary for Claude
        import pandas as pd
        prop_df = pd.read_csv(args.proprietary)
        proprietary_context = prop_df.to_markdown(index=False)

        print("Generating management report...")
        mgmt_report = generate_management_report(movers, month_label, proprietary_context, args.audience)
        mgmt_path = output_dir / f"mgmt_report_{month_label}.md"
        mgmt_path.write_text(mgmt_report)
        print(f"  Saved management report to {mgmt_path}")

    print("\nDone.")


if __name__ == "__main__":
    main()

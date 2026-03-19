#!/usr/bin/env python3
"""
Fully automated monthly pipeline.

This is the cron-ready entry point. It:
1. Determines which month to process
2. Downloads the data from CMS (current + previous month)
3. Runs the delta/outlier pipeline
4. Generates Claude-powered reports
5. Updates the running trend analysis
6. Optionally sends a notification

Usage:
    # Auto-detect latest available month
    python monthly.py

    # Specific month
    python monthly.py --year 2025 --month 12

    # Include proprietary data
    python monthly.py --proprietary data/internal/latest.csv

    # Dry run (download + data only, no Claude)
    python monthly.py --dry-run
"""

import argparse
import calendar
import json
import sys
from datetime import datetime
from pathlib import Path

from download import download_month_pair, latest_available
from ingest import load_cpsc_file, aggregate_by_county_carrier
from deltas import compute_deltas, flag_outliers, top_movers


def run_pipeline(
    year: int,
    month: int,
    config_path: str = "config/thresholds.json",
    proprietary_path: str | None = None,
    audience: str = "VP of Growth",
    dry_run: bool = False,
) -> dict:
    """Run the full monthly pipeline. Returns a summary dict."""
    month_label = f"{calendar.month_name[month]} {year}"
    print(f"\n{'='*60}")
    print(f"  MA Market Intel — {month_label}")
    print(f"{'='*60}\n")

    # --- Download ---
    print("[1/5] Downloading data from CMS...")
    prev_csv, curr_csv = download_month_pair(year, month)

    # --- Ingest ---
    print("\n[2/5] Loading and normalizing...")
    prev_df = load_cpsc_file(prev_csv)
    curr_df = load_cpsc_file(curr_csv)

    prev_agg = aggregate_by_county_carrier(prev_df)
    curr_agg = aggregate_by_county_carrier(curr_df)
    print(f"  Previous: {len(prev_agg):,} county-carrier combos")
    print(f"  Current:  {len(curr_agg):,} county-carrier combos")

    # --- Deltas ---
    print("\n[3/5] Computing deltas and flagging outliers...")
    deltas = compute_deltas(curr_agg, prev_agg)
    deltas = flag_outliers(deltas, config_path)
    movers = top_movers(deltas)
    print(f"  {movers['total_flagged']:,} flagged / {movers['total_rows']:,} total")

    # Save data outputs
    output_dir = Path("output/reports")
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_label = f"{year}-{month:02d}"

    deltas.to_parquet(output_dir / f"deltas_{safe_label}.parquet", index=False)
    (output_dir / f"movers_{safe_label}.json").write_text(json.dumps(movers, indent=2, default=str))

    if dry_run:
        print("\n[DRY RUN] Skipping Claude analysis. Data outputs saved.")
        return {"month": month_label, "flagged": movers["total_flagged"], "dry_run": True}

    # --- Claude Analysis ---
    from analyst import generate_monthly_report, update_trend_analysis, generate_management_report

    print("\n[4/5] Generating reports with Claude...")
    report = generate_monthly_report(movers, month_label)
    report_path = output_dir / f"report_{safe_label}.md"
    report_path.write_text(report)
    print(f"  Monthly report: {report_path}")

    print("  Updating trend analysis...")
    update_trend_analysis(movers, month_label)
    trend_path = Path("output/trends/running_trend.md")
    print(f"  Trend document: {trend_path}")

    # --- Management Report (if proprietary data provided) ---
    mgmt_path = None
    if proprietary_path:
        print(f"\n[5/5] Generating management report...")
        import pandas as pd
        prop_df = pd.read_csv(proprietary_path)
        proprietary_context = prop_df.to_markdown(index=False)
        mgmt_report = generate_management_report(movers, month_label, proprietary_context, audience)
        mgmt_path = output_dir / f"mgmt_report_{safe_label}.md"
        mgmt_path.write_text(mgmt_report)
        print(f"  Management report: {mgmt_path}")
    else:
        print("\n[5/5] No proprietary data — skipping management report.")

    summary = {
        "month": month_label,
        "flagged": movers["total_flagged"],
        "total_rows": movers["total_rows"],
        "report": str(report_path),
        "trend": str(trend_path),
        "mgmt_report": str(mgmt_path) if mgmt_path else None,
    }

    print(f"\n{'='*60}")
    print(f"  Done. {movers['total_flagged']} outliers flagged.")
    print(f"{'='*60}\n")
    return summary


def main():
    parser = argparse.ArgumentParser(description="Automated monthly MA Market Intel pipeline")
    parser.add_argument("--year", type=int)
    parser.add_argument("--month", type=int)
    parser.add_argument("--config", default="config/thresholds.json")
    parser.add_argument("--proprietary", help="Path to proprietary data CSV")
    parser.add_argument("--audience", default="VP of Growth")
    parser.add_argument("--dry-run", action="store_true", help="Data pipeline only, no Claude")
    args = parser.parse_args()

    if args.year and args.month:
        y, m = args.year, args.month
    else:
        y, m = latest_available()
        print(f"Auto-detected latest available month: {calendar.month_name[m]} {y}")

    summary = run_pipeline(
        year=y,
        month=m,
        config_path=args.config,
        proprietary_path=args.proprietary,
        audience=args.audience,
        dry_run=args.dry_run,
    )

    # Write summary for external tools to pick up
    summary_path = Path("output/last_run.json")
    summary_path.write_text(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

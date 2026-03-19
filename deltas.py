"""
Compute month-over-month deltas and flag outliers.

This is the analytical core: it merges two months of aggregated data,
computes absolute and percentage changes, calculates market share shifts,
and flags statistical outliers.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path


def load_thresholds(config_path: str = "config/thresholds.json") -> dict:
    with open(config_path) as f:
        return json.load(f)


def compute_deltas(
    current: pd.DataFrame,
    previous: pd.DataFrame,
) -> pd.DataFrame:
    """Merge two months and compute enrollment changes."""
    join_cols = [c for c in ["fips", "carrier", "contract_id"] if c in current.columns and c in previous.columns]
    context_cols = [c for c in ["state", "county", "parent_org"] if c in current.columns]

    merged = current.merge(
        previous[join_cols + ["enrollment"]],
        on=join_cols,
        how="outer",
        suffixes=("_curr", "_prev"),
    )

    # Carry forward context columns
    for col in context_cols:
        if col in current.columns and col not in merged.columns:
            merged = merged.merge(current[join_cols + [col]].drop_duplicates(), on=join_cols, how="left")

    merged["enrollment_curr"] = merged["enrollment_curr"].fillna(0).astype(int)
    merged["enrollment_prev"] = merged["enrollment_prev"].fillna(0).astype(int)

    merged["change"] = merged["enrollment_curr"] - merged["enrollment_prev"]
    merged["change_pct"] = np.where(
        merged["enrollment_prev"] > 0,
        (merged["change"] / merged["enrollment_prev"]) * 100,
        np.where(merged["enrollment_curr"] > 0, 100.0, 0.0),
    )

    # Market share within each county
    county_totals_curr = merged.groupby("fips")["enrollment_curr"].transform("sum")
    county_totals_prev = merged.groupby("fips")["enrollment_prev"].transform("sum")
    merged["mkt_share_curr"] = np.where(county_totals_curr > 0, merged["enrollment_curr"] / county_totals_curr * 100, 0)
    merged["mkt_share_prev"] = np.where(county_totals_prev > 0, merged["enrollment_prev"] / county_totals_prev * 100, 0)
    merged["mkt_share_change"] = merged["mkt_share_curr"] - merged["mkt_share_prev"]

    return merged.sort_values("change", key=abs, ascending=False)


def flag_outliers(deltas: pd.DataFrame, config_path: str = "config/thresholds.json") -> pd.DataFrame:
    """Flag rows that exceed configured thresholds or are statistical outliers."""
    cfg = load_thresholds(config_path)

    # Only look at rows with meaningful enrollment
    mask_relevant = (deltas["enrollment_curr"] >= cfg["min_enrollment_for_relevance"]) | (
        deltas["enrollment_prev"] >= cfg["min_enrollment_for_relevance"]
    )

    flags = []

    # Threshold-based flags
    flags.append(mask_relevant & (deltas["change_pct"].abs() >= cfg["enrollment_change_pct_threshold"]))
    flags.append(mask_relevant & (deltas["mkt_share_change"].abs() >= cfg["market_share_change_pct_threshold"]))

    # Statistical outlier: change is >2 std devs from mean (among relevant rows)
    relevant = deltas.loc[mask_relevant, "change"]
    mean, std = relevant.mean(), relevant.std()
    if std > 0:
        flags.append(mask_relevant & ((deltas["change"] - mean).abs() > 2 * std))

    # Carrier filter (if specified)
    if cfg["carriers_of_interest"]:
        carrier_mask = deltas["carrier"].str.lower().isin([c.lower() for c in cfg["carriers_of_interest"]])
        flags.append(mask_relevant & carrier_mask & (deltas["change"] != 0))

    deltas["flagged"] = False
    for f in flags:
        deltas["flagged"] = deltas["flagged"] | f

    return deltas


def top_movers(deltas: pd.DataFrame, n: int = 25) -> dict:
    """Extract the top movers for Claude to analyze."""
    flagged = deltas[deltas["flagged"]].copy()

    display_cols = [c for c in ["state", "county", "fips", "carrier", "contract_id",
                                 "enrollment_prev", "enrollment_curr", "change", "change_pct",
                                 "mkt_share_prev", "mkt_share_curr", "mkt_share_change"]
                    if c in flagged.columns]

    # Top gainers and losers
    gainers = flagged.nlargest(n, "change")[display_cols]
    losers = flagged.nsmallest(n, "change")[display_cols]

    # Biggest market share shifts
    share_shifts = flagged.reindex(flagged["mkt_share_change"].abs().sort_values(ascending=False).index).head(n)[display_cols]

    # County-level summary
    county_summary = (
        deltas.groupby(["fips", "state", "county"] if "county" in deltas.columns else ["fips"])
        .agg(
            total_curr=("enrollment_curr", "sum"),
            total_prev=("enrollment_prev", "sum"),
            num_carriers=("carrier", "nunique"),
            num_flagged=("flagged", "sum"),
        )
        .assign(county_change=lambda x: x["total_curr"] - x["total_prev"])
        .sort_values("county_change", key=abs, ascending=False)
        .head(n)
    )

    return {
        "top_gainers": gainers.to_dict("records"),
        "top_losers": losers.to_dict("records"),
        "biggest_share_shifts": share_shifts.to_dict("records"),
        "county_summary": county_summary.reset_index().to_dict("records"),
        "total_flagged": int(flagged.shape[0]),
        "total_rows": int(deltas.shape[0]),
    }

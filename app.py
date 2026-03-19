#!/usr/bin/env python3
"""
MA Market Intel — Streamlit Dashboard

Run with:
    streamlit run app.py
"""

import json
import os
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ingest import load_cpsc_file, aggregate_by_county_carrier
from deltas import compute_deltas, flag_outliers, top_movers, load_thresholds

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="MA Market Intel",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Auth — optional password gate for shared deployments
# ---------------------------------------------------------------------------
def check_password() -> bool:
    """Return True if no password is configured or if the user entered it."""
    app_password = st.secrets.get("APP_PASSWORD", "") if hasattr(st, "secrets") else ""
    if not app_password:
        return True
    if st.session_state.get("authenticated"):
        return True
    pwd = st.text_input("Enter the app password:", type="password")
    if pwd == app_password:
        st.session_state["authenticated"] = True
        st.rerun()
    elif pwd:
        st.error("Incorrect password.")
    return False


if not check_password():
    st.stop()

# ---------------------------------------------------------------------------
# Inject API key from Streamlit secrets (for Cloud deployment)
# ---------------------------------------------------------------------------
if hasattr(st, "secrets") and st.secrets.get("ANTHROPIC_API_KEY", ""):
    os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]

# ---------------------------------------------------------------------------
# Sidebar — data loading & config
# ---------------------------------------------------------------------------
st.sidebar.title("MA Market Intel")
st.sidebar.markdown("Medicare Advantage enrollment analysis")

st.sidebar.divider()
st.sidebar.subheader("Data Source")

data_source = st.sidebar.radio(
    "Load data from:",
    ["Upload CSV files", "Use test data", "Select existing files"],
)

prev_df = None
curr_df = None
month_label = ""

if data_source == "Upload CSV files":
    prev_file = st.sidebar.file_uploader("Previous month CSV", type=["csv"])
    curr_file = st.sidebar.file_uploader("Current month CSV", type=["csv"])
    month_label = st.sidebar.text_input("Month label", "February 2026")
    if prev_file and curr_file:
        # Save uploads to temp location for the ingest pipeline
        tmp_prev = Path("data/raw/_upload_prev.csv")
        tmp_curr = Path("data/raw/_upload_curr.csv")
        tmp_prev.parent.mkdir(parents=True, exist_ok=True)
        tmp_prev.write_bytes(prev_file.read())
        tmp_curr.write_bytes(curr_file.read())
        prev_df = load_cpsc_file(tmp_prev)
        curr_df = load_cpsc_file(tmp_curr)

elif data_source == "Use test data":
    test_prev = Path("data/raw/test-2025-11.csv")
    test_curr = Path("data/raw/test-2025-12.csv")
    if test_prev.exists() and test_curr.exists():
        prev_df = load_cpsc_file(test_prev)
        curr_df = load_cpsc_file(test_curr)
        month_label = "December 2025"
    else:
        st.sidebar.warning("Test data not found. Run: `python generate_test_data.py`")

elif data_source == "Select existing files":
    raw_dir = Path("data/raw")
    csvs = sorted(raw_dir.glob("*.csv")) if raw_dir.exists() else []
    if csvs:
        prev_choice = st.sidebar.selectbox("Previous month", csvs, format_func=lambda p: p.name)
        curr_choice = st.sidebar.selectbox("Current month", csvs, index=min(1, len(csvs) - 1), format_func=lambda p: p.name)
        month_label = st.sidebar.text_input("Month label", curr_choice.stem if curr_choice else "")
        if prev_choice and curr_choice:
            prev_df = load_cpsc_file(prev_choice)
            curr_df = load_cpsc_file(curr_choice)
    else:
        st.sidebar.warning("No CSV files in data/raw/")

# Threshold controls
st.sidebar.divider()
st.sidebar.subheader("Outlier Thresholds")
cfg = load_thresholds()
enroll_thresh = st.sidebar.slider("Enrollment change %", 1.0, 25.0, cfg["enrollment_change_pct_threshold"], 0.5)
share_thresh = st.sidebar.slider("Market share change %", 0.5, 10.0, cfg["market_share_change_pct_threshold"], 0.25)
min_enroll = st.sidebar.number_input("Min enrollment for relevance", 0, 10000, cfg["min_enrollment_for_relevance"], 100)
top_n = st.sidebar.slider("Top N movers to show", 5, 50, cfg["top_n_movers"])

# Write thresholds back so the pipeline uses them
runtime_cfg = {
    "enrollment_change_pct_threshold": enroll_thresh,
    "market_share_change_pct_threshold": share_thresh,
    "min_enrollment_for_relevance": min_enroll,
    "top_n_movers": top_n,
    "carriers_of_interest": cfg.get("carriers_of_interest", []),
}
runtime_cfg_path = Path("config/_runtime_thresholds.json")
runtime_cfg_path.parent.mkdir(parents=True, exist_ok=True)
runtime_cfg_path.write_text(json.dumps(runtime_cfg))

# ---------------------------------------------------------------------------
# Main content — only render when data is loaded
# ---------------------------------------------------------------------------
if prev_df is None or curr_df is None:
    st.title("MA Market Intel")
    st.info("Select a data source in the sidebar to get started.")
    st.stop()

# --- Run pipeline ---
prev_agg = aggregate_by_county_carrier(prev_df)
curr_agg = aggregate_by_county_carrier(curr_df)
deltas = compute_deltas(curr_agg, prev_agg)
deltas = flag_outliers(deltas, str(runtime_cfg_path))
movers = top_movers(deltas, n=top_n)
flagged_df = deltas[deltas["flagged"]].copy()

# ---------------------------------------------------------------------------
# Header metrics
# ---------------------------------------------------------------------------
st.title(f"MA Market Intel — {month_label}")

col1, col2, col3, col4 = st.columns(4)
total_curr = int(deltas["enrollment_curr"].sum())
total_prev = int(deltas["enrollment_prev"].sum())
total_change = total_curr - total_prev
total_change_pct = (total_change / total_prev * 100) if total_prev > 0 else 0

col1.metric("Total Enrollment", f"{total_curr:,}", f"{total_change:+,} ({total_change_pct:+.1f}%)")
col2.metric("County-Carrier Combos", f"{len(deltas):,}")
col3.metric("Outliers Flagged", f"{len(flagged_df):,}", f"{len(flagged_df)/len(deltas)*100:.1f}% of total")
col4.metric("Counties with Flags", f"{flagged_df['fips'].nunique() if 'fips' in flagged_df.columns else 0}")

# ---------------------------------------------------------------------------
# Tab layout
# ---------------------------------------------------------------------------
tab_overview, tab_gainers, tab_counties, tab_carrier, tab_claude, tab_data = st.tabs(
    ["Overview", "Gainers & Losers", "County Hotspots", "Carrier Deep Dive", "Claude Analysis", "Raw Data"]
)

# --- OVERVIEW TAB ---
with tab_overview:
    st.subheader("Enrollment Change Distribution")

    col_left, col_right = st.columns(2)

    with col_left:
        # Histogram of changes
        relevant = deltas[(deltas["enrollment_curr"] >= min_enroll) | (deltas["enrollment_prev"] >= min_enroll)].copy()
        fig_hist = px.histogram(
            relevant, x="change_pct", nbins=50,
            title="Distribution of Enrollment Changes (%)",
            labels={"change_pct": "Change %", "count": "Count"},
            color_discrete_sequence=["#4A90D9"],
        )
        fig_hist.add_vline(x=0, line_dash="dash", line_color="gray")
        fig_hist.update_layout(height=400)
        st.plotly_chart(fig_hist, use_container_width=True)

    with col_right:
        # Top movers bar chart
        top_df = flagged_df.nlargest(10, "change", keep="first")[["carrier", "county", "change"]].copy()
        bottom_df = flagged_df.nsmallest(10, "change", keep="first")[["carrier", "county", "change"]].copy()
        bar_df = pd.concat([top_df, bottom_df]).drop_duplicates()
        bar_df["label"] = bar_df["carrier"].str[:20] + " / " + bar_df["county"].fillna("")
        bar_df = bar_df.sort_values("change")
        colors = ["#E74C3C" if x < 0 else "#2ECC71" for x in bar_df["change"]]

        fig_bar = go.Figure(go.Bar(
            x=bar_df["change"], y=bar_df["label"], orientation="h",
            marker_color=colors,
        ))
        fig_bar.update_layout(title="Top Gainers & Losers (Enrollment Change)", height=400, yaxis=dict(tickfont=dict(size=10)))
        st.plotly_chart(fig_bar, use_container_width=True)

    # Market share shift scatter
    st.subheader("Market Share Shifts")
    scatter_df = relevant.copy()
    scatter_df["abs_change"] = scatter_df["change"].abs()
    fig_scatter = px.scatter(
        scatter_df, x="mkt_share_change", y="change_pct",
        size="enrollment_curr", color="flagged",
        hover_data=["carrier", "county", "state", "enrollment_curr", "enrollment_prev"],
        title="Market Share Change vs Enrollment Change",
        labels={"mkt_share_change": "Market Share Change (pp)", "change_pct": "Enrollment Change %"},
        color_discrete_map={True: "#E74C3C", False: "#BDC3C7"},
    )
    fig_scatter.update_layout(height=500)
    st.plotly_chart(fig_scatter, use_container_width=True)


# --- GAINERS & LOSERS TAB ---
with tab_gainers:
    col_g, col_l = st.columns(2)

    with col_g:
        st.subheader("Top Gainers")
        gainers_df = pd.DataFrame(movers["top_gainers"])
        if not gainers_df.empty:
            display_cols = [c for c in ["carrier", "county", "state", "change", "change_pct", "mkt_share_change"] if c in gainers_df.columns]
            fmt = {"change": "{:+,d}", "change_pct": "{:+.1f}%", "mkt_share_change": "{:+.2f}pp"}
            st.dataframe(
                gainers_df[display_cols].style.format({k: v for k, v in fmt.items() if k in display_cols}),
                use_container_width=True, hide_index=True,
            )

    with col_l:
        st.subheader("Top Losers")
        losers_df = pd.DataFrame(movers["top_losers"])
        if not losers_df.empty:
            display_cols = [c for c in ["carrier", "county", "state", "change", "change_pct", "mkt_share_change"] if c in losers_df.columns]
            st.dataframe(
                losers_df[display_cols].style.format({k: v for k, v in fmt.items() if k in display_cols}),
                use_container_width=True, hide_index=True,
            )

    st.subheader("Biggest Market Share Shifts")
    shifts_df = pd.DataFrame(movers["biggest_share_shifts"])
    if not shifts_df.empty:
        display_cols = [c for c in ["carrier", "county", "state", "mkt_share_prev", "mkt_share_curr", "mkt_share_change", "enrollment_curr"] if c in shifts_df.columns]
        share_fmt = {"mkt_share_prev": "{:.1f}%", "mkt_share_curr": "{:.1f}%", "mkt_share_change": "{:+.2f}pp", "enrollment_curr": "{:,}"}
        st.dataframe(
            shifts_df[display_cols].style.format({k: v for k, v in share_fmt.items() if k in display_cols}),
            use_container_width=True, hide_index=True,
        )


# --- COUNTY HOTSPOTS TAB ---
with tab_counties:
    st.subheader("County-Level Summary")
    county_df = pd.DataFrame(movers["county_summary"])
    if not county_df.empty:
        display_cols = [c for c in ["county", "state", "fips", "total_curr", "total_prev", "county_change", "num_carriers", "num_flagged"] if c in county_df.columns]
        county_fmt = {"total_curr": "{:,}", "total_prev": "{:,}", "county_change": "{:+,}"}
        st.dataframe(
            county_df[display_cols].style.format({k: v for k, v in county_fmt.items() if k in display_cols}),
            use_container_width=True, hide_index=True,
        )

    # Drill into a county
    st.divider()
    st.subheader("County Deep Dive")
    counties_available = sorted(deltas["county"].dropna().unique()) if "county" in deltas.columns else []
    if counties_available:
        selected_county = st.selectbox("Select county", counties_available)
        county_data = deltas[deltas["county"] == selected_county].sort_values("change", key=abs, ascending=False)

        col_chart, col_table = st.columns([1, 1])
        with col_chart:
            fig_county = px.bar(
                county_data, x="carrier", y="change", color="flagged",
                title=f"Enrollment Changes in {selected_county}",
                color_discrete_map={True: "#E74C3C", False: "#4A90D9"},
            )
            fig_county.update_layout(height=400)
            st.plotly_chart(fig_county, use_container_width=True)

        with col_table:
            display_cols = [c for c in ["carrier", "enrollment_prev", "enrollment_curr", "change", "change_pct", "mkt_share_curr", "flagged"] if c in county_data.columns]
            st.dataframe(county_data[display_cols], use_container_width=True, hide_index=True)


# --- CARRIER DEEP DIVE TAB ---
with tab_carrier:
    st.subheader("Carrier Performance Across Counties")
    carriers = sorted(deltas["carrier"].dropna().unique()) if "carrier" in deltas.columns else []
    if carriers:
        selected_carrier = st.selectbox("Select carrier", carriers)
        carrier_data = deltas[deltas["carrier"] == selected_carrier].sort_values("change", key=abs, ascending=False)

        # Summary metrics for this carrier
        c1, c2, c3 = st.columns(3)
        carrier_total_curr = int(carrier_data["enrollment_curr"].sum())
        carrier_total_prev = int(carrier_data["enrollment_prev"].sum())
        carrier_change = carrier_total_curr - carrier_total_prev
        c1.metric("Total Enrollment", f"{carrier_total_curr:,}", f"{carrier_change:+,}")
        c2.metric("Counties Active", f"{len(carrier_data)}")
        c3.metric("Counties Flagged", f"{int(carrier_data['flagged'].sum())}")

        col_chart, col_table = st.columns([1, 1])
        with col_chart:
            fig_carrier = px.bar(
                carrier_data, x="county", y="change", color="flagged",
                title=f"{selected_carrier} — Enrollment Changes by County",
                color_discrete_map={True: "#E74C3C", False: "#4A90D9"},
            )
            fig_carrier.update_layout(height=400, xaxis_tickangle=-45)
            st.plotly_chart(fig_carrier, use_container_width=True)

        with col_table:
            display_cols = [c for c in ["county", "state", "enrollment_prev", "enrollment_curr", "change", "change_pct", "mkt_share_change"] if c in carrier_data.columns]
            st.dataframe(carrier_data[display_cols], use_container_width=True, hide_index=True)


# --- CLAUDE ANALYSIS TAB ---
with tab_claude:
    st.subheader("AI-Powered Analysis")

    import os
    has_key = bool(os.environ.get("ANTHROPIC_API_KEY"))

    if not has_key:
        api_key = st.text_input("Enter your Anthropic API key:", type="password")
        if api_key:
            os.environ["ANTHROPIC_API_KEY"] = api_key
            has_key = True

    if has_key:
        # Proprietary data upload
        prop_file = st.file_uploader("Upload proprietary data (optional CSV)", type=["csv"], key="prop_upload")
        proprietary_context = ""
        if prop_file:
            prop_df = pd.read_csv(prop_file)
            proprietary_context = prop_df.to_markdown(index=False)
            st.success(f"Loaded {len(prop_df)} rows of proprietary data")

        col_report, col_trend, col_mgmt = st.columns(3)

        with col_report:
            if st.button("Generate Monthly Report", use_container_width=True):
                with st.spinner("Claude is analyzing outliers..."):
                    from analyst import generate_monthly_report
                    report = generate_monthly_report(movers, month_label, proprietary_context)
                    st.session_state["report"] = report
                    # Save to file
                    report_path = Path("output/reports") / f"report_{month_label}.md"
                    report_path.parent.mkdir(parents=True, exist_ok=True)
                    report_path.write_text(report)

        with col_trend:
            if st.button("Update Trend Analysis", use_container_width=True):
                with st.spinner("Claude is updating trends..."):
                    from analyst import update_trend_analysis
                    trend = update_trend_analysis(movers, month_label)
                    st.session_state["trend"] = trend

        with col_mgmt:
            if proprietary_context:
                audience = st.text_input("Target audience", "VP of Growth")
                if st.button("Generate Management Report", use_container_width=True):
                    with st.spinner("Claude is generating management report..."):
                        from analyst import generate_management_report
                        mgmt = generate_management_report(movers, month_label, proprietary_context, audience)
                        st.session_state["mgmt_report"] = mgmt
                        mgmt_path = Path("output/reports") / f"mgmt_report_{month_label}.md"
                        mgmt_path.parent.mkdir(parents=True, exist_ok=True)
                        mgmt_path.write_text(mgmt)
            else:
                st.caption("Upload proprietary data above to enable management reports")

        st.divider()

        # Display reports
        if "report" in st.session_state:
            st.subheader("Monthly Report")
            st.markdown(st.session_state["report"])
            st.download_button("Download Report", st.session_state["report"], f"report_{month_label}.md", mime="text/markdown")

        if "trend" in st.session_state:
            st.subheader("Running Trend Analysis")
            st.markdown(st.session_state["trend"])

        if "mgmt_report" in st.session_state:
            st.subheader("Management Report")
            st.markdown(st.session_state["mgmt_report"])
            st.download_button("Download Management Report", st.session_state["mgmt_report"], f"mgmt_report_{month_label}.md", mime="text/markdown")

        # Show existing reports
        existing_reports = sorted(Path("output/reports").glob("report_*.md")) if Path("output/reports").exists() else []
        if existing_reports:
            st.divider()
            st.subheader("Previous Reports")
            for rp in existing_reports:
                with st.expander(rp.stem):
                    st.markdown(rp.read_text())

        trend_path = Path("output/trends/running_trend.md")
        if trend_path.exists() and "trend" not in st.session_state:
            st.divider()
            st.subheader("Current Trend Document")
            st.markdown(trend_path.read_text())

    else:
        st.warning("Enter your Anthropic API key above to enable Claude-powered analysis.")
        st.caption("The data pipeline and visualizations work without an API key.")


# --- RAW DATA TAB ---
with tab_data:
    st.subheader("Full Delta Dataset")

    # Filters
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        show_flagged_only = st.checkbox("Flagged only", value=False)
    with col_f2:
        state_filter = st.multiselect("Filter by state", sorted(deltas["state"].dropna().unique()) if "state" in deltas.columns else [])
    with col_f3:
        carrier_filter = st.multiselect("Filter by carrier", sorted(deltas["carrier"].dropna().unique()) if "carrier" in deltas.columns else [])

    filtered = deltas.copy()
    if show_flagged_only:
        filtered = filtered[filtered["flagged"]]
    if state_filter:
        filtered = filtered[filtered["state"].isin(state_filter)]
    if carrier_filter:
        filtered = filtered[filtered["carrier"].isin(carrier_filter)]

    st.dataframe(filtered, use_container_width=True, hide_index=True)

    # Export
    csv_export = filtered.to_csv(index=False)
    st.download_button("Download as CSV", csv_export, f"deltas_{month_label}.csv", mime="text/csv")

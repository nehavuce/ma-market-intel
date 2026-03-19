"""
Claude-powered analysis layer.

Takes the structured outlier data from deltas.py and produces:
1. A monthly narrative report (what happened, what matters)
2. Updates to the running trend document
"""

import json
from datetime import datetime
from pathlib import Path

import os
import anthropic

MODEL = "claude-sonnet-4-6"  # fast + cheap for structured analysis; swap to opus for deeper reasoning


def _get_client() -> anthropic.Anthropic:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise EnvironmentError(
            "ANTHROPIC_API_KEY not set. Export it before running:\n"
            "  export ANTHROPIC_API_KEY=sk-ant-..."
        )
    return anthropic.Anthropic()


def generate_monthly_report(movers: dict, month_label: str, proprietary_context: str = "") -> str:
    """Generate a narrative analysis of this month's outliers."""
    system = """You are a Medicare Advantage market analyst. You analyze enrollment data
and produce concise, actionable intelligence for health plan executives.

Your reports should:
- Lead with the 3-5 most important findings
- Quantify everything (enrollment numbers, % changes, market share shifts)
- Distinguish between noise (seasonal churn) and signal (competitive moves)
- Flag counties or carriers that warrant closer attention
- Be direct — executives skim, so front-load insights"""

    user_msg = f"""Analyze the Medicare Advantage enrollment changes for {month_label}.

## Outlier Data
{json.dumps(movers, indent=2, default=str)}

{f"## Additional Business Context{chr(10)}{proprietary_context}" if proprietary_context else ""}

Produce a monthly market intelligence report with these sections:
1. **Executive Summary** (3-5 bullet points)
2. **Top Competitive Moves** (who gained/lost where, and what it likely means)
3. **County Hotspots** (counties with unusual activity)
4. **Market Share Shifts** (carriers gaining/losing share at scale)
5. **Watch List** (things to monitor next month)"""

    response = _get_client().messages.create(
        model=MODEL,
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user_msg}],
    )
    return response.content[0].text


def update_trend_analysis(
    movers: dict,
    month_label: str,
    trend_path: str = "output/trends/running_trend.md",
) -> str:
    """Read existing trend doc, ask Claude to update it with new month's data."""
    trend_path = Path(trend_path)
    existing_trend = trend_path.read_text() if trend_path.exists() else "No prior trend data."

    system = """You are a Medicare Advantage market analyst maintaining a running trend document.
This document tracks multi-month patterns in MA enrollment. Your job is to UPDATE it
with the latest month's data — not rewrite it from scratch.

Guidelines:
- Preserve historical observations; add to them
- Call out when a trend accelerates, reverses, or confirms
- Keep the document structured and scannable
- Remove stale watch items that resolved
- Total length should stay under 3000 words"""

    user_msg = f"""Here is the current running trend document:

---
{existing_trend}
---

New data for {month_label}:
{json.dumps(movers, indent=2, default=str)}

Update the trend document to incorporate this month's findings.
Return the COMPLETE updated document (not just the changes)."""

    response = _get_client().messages.create(
        model=MODEL,
        max_tokens=6000,
        system=system,
        messages=[{"role": "user", "content": user_msg}],
    )

    updated = response.content[0].text
    trend_path.parent.mkdir(parents=True, exist_ok=True)
    trend_path.write_text(updated)
    return updated


def generate_management_report(
    movers: dict,
    month_label: str,
    proprietary_data: str,
    audience: str = "VP of Growth",
) -> str:
    """Level 2: Combine public CMS data with proprietary data for a management report."""
    system = f"""You are producing an internal management report for {audience} at a health plan.
You have access to both public CMS enrollment data and internal business data.

Your report should:
- Connect market-level trends to internal performance
- Identify competitive threats and opportunities by specific county
- Recommend concrete actions (where to invest, where to defend)
- Include data tables where helpful
- Be presentation-ready (could be dropped into a slide deck)"""

    user_msg = f"""## Public Market Data ({month_label})
{json.dumps(movers, indent=2, default=str)}

## Internal Business Data
{proprietary_data}

Produce a management report with:
1. **Market Position Summary** — where we stand vs. competitors
2. **Opportunities** — counties/segments where we should grow
3. **Threats** — where competitors are gaining on us
4. **Recommended Actions** — specific, prioritized next steps
5. **Appendix** — supporting data tables"""

    response = _get_client().messages.create(
        model=MODEL,
        max_tokens=6000,
        system=system,
        messages=[{"role": "user", "content": user_msg}],
    )
    return response.content[0].text

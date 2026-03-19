#!/usr/bin/env python3
"""
Generate a sample proprietary data file to demonstrate
the management report capability.

This simulates the kind of internal data a health plan would have:
- Their own enrollment by county
- Retention/churn rates
- Sales pipeline data
- Member satisfaction scores
"""

import csv
from pathlib import Path

HEADERS = [
    "county", "state", "fips",
    "our_enrollment", "our_enrollment_prev_month",
    "retention_rate_pct", "new_sales", "disenrollments",
    "star_rating", "member_satisfaction_score",
    "broker_leads", "digital_leads",
    "avg_premium", "competitor_avg_premium",
    "notes"
]

ROWS = [
    ["Miami-Dade", "FL", "12086", 8500, 8200, 96.5, 450, 150, 4.0, 4.2, 320, 180, 45.00, 52.00, "Strong broker channel"],
    ["Broward", "FL", "12011", 5200, 5100, 95.8, 220, 120, 4.0, 4.1, 180, 90, 48.00, 51.00, ""],
    ["Palm Beach", "FL", "12099", 4800, 4600, 94.2, 310, 110, 3.5, 3.9, 200, 140, 47.00, 50.00, "Satisfaction dip — investigating"],
    ["Los Angeles", "CA", "06037", 3200, 3400, 91.0, 180, 380, 3.5, 3.7, 150, 220, 62.00, 58.00, "Lost ground to Devoted Health entry"],
    ["Maricopa", "AZ", "04013", 6100, 5800, 97.1, 420, 120, 4.5, 4.5, 280, 160, 38.00, 42.00, "Benefiting from Humana pullback"],
    ["Cook", "IL", "17031", 4400, 4200, 93.5, 350, 150, 3.5, 3.8, 190, 170, 55.00, 53.00, "BCBS decline is an opportunity"],
    ["Harris", "TX", "48201", 7200, 7000, 95.0, 380, 180, 4.0, 4.0, 240, 200, 42.00, 45.00, ""],
    ["Clark", "NV", "32003", 2800, 2700, 94.8, 180, 80, 4.0, 4.1, 120, 90, 40.00, 43.00, ""],
    ["King", "WA", "53033", 1900, 1850, 96.0, 120, 70, 4.5, 4.3, 80, 110, 58.00, 60.00, ""],
    ["New York", "NY", "36061", 2100, 2050, 93.0, 150, 100, 3.5, 3.6, 90, 130, 72.00, 68.00, "Premium disadvantage"],
]


def main():
    path = Path("data/internal/sample_proprietary.csv")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(HEADERS)
        writer.writerows(ROWS)
    print(f"Wrote {path} ({len(ROWS)} rows)")
    print(f"\nUse with:\n  python run.py ... --proprietary {path}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Generate realistic synthetic CPSC data for testing the pipeline.

Creates two months of data with known outliers so we can verify
detection and reporting work correctly.
"""

import csv
import random
from pathlib import Path

random.seed(42)

CARRIERS = [
    ("H0001", "UnitedHealthcare", "UnitedHealth Group"),
    ("H0002", "Humana", "Humana Inc"),
    ("H0003", "CVS/Aetna", "CVS Health"),
    ("H0004", "Cigna Healthcare", "The Cigna Group"),
    ("H0005", "Kaiser Permanente", "Kaiser Foundation"),
    ("H0006", "Centene/WellCare", "Centene Corporation"),
    ("H0007", "Molina Healthcare", "Molina Healthcare Inc"),
    ("H0008", "Blue Cross Blue Shield", "BCBS Association"),
    ("H0009", "Devoted Health", "Devoted Health Inc"),
    ("H0010", "Alignment Healthcare", "Alignment Healthcare Inc"),
]

# Real FIPS codes + county names for a realistic spread
COUNTIES = [
    ("06037", "CA", "Los Angeles"),
    ("06073", "CA", "San Diego"),
    ("12086", "FL", "Miami-Dade"),
    ("12011", "FL", "Broward"),
    ("12099", "FL", "Palm Beach"),
    ("48201", "TX", "Harris"),
    ("48113", "TX", "Dallas"),
    ("04013", "AZ", "Maricopa"),
    ("32003", "NV", "Clark"),
    ("36061", "NY", "New York"),
    ("36047", "NY", "Kings"),
    ("17031", "IL", "Cook"),
    ("26163", "MI", "Wayne"),
    ("39035", "OH", "Cuyahoga"),
    ("42101", "PA", "Philadelphia"),
    ("13121", "GA", "Fulton"),
    ("37119", "NC", "Mecklenburg"),
    ("47157", "TN", "Shelby"),
    ("29189", "MO", "St. Louis"),
    ("53033", "WA", "King"),
]

PLAN_TYPES = ["HMO", "PPO", "PFFS", "HMO-POS", "Local PPO"]

HEADERS = [
    "Contract Number", "Plan ID", "Organization Name",
    "Organization Marketing Name", "Plan Type", "Parent Organization",
    "State", "County", "FIPS State County Code", "Enrollment"
]


def base_enrollment(carrier_idx: int, county_idx: int) -> int:
    """Generate a plausible base enrollment. Bigger carriers get more."""
    carrier_weight = max(1, 11 - carrier_idx)  # H0001 is biggest
    county_weight = random.randint(50, 500)
    return carrier_weight * county_weight


def generate_month(output_path: Path, base_data: dict, apply_changes: dict = None):
    """Write a CPSC CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []

    for (contract_id, carrier, parent), county_data in base_data.items():
        for (fips, state, county), plans in county_data.items():
            for plan_id, plan_type, enrollment in plans:
                # Apply changes if specified
                if apply_changes:
                    key = (contract_id, fips, plan_id)
                    if key in apply_changes:
                        enrollment = apply_changes[key]

                rows.append([
                    contract_id, plan_id, carrier, carrier,
                    plan_type, parent, state, county, fips, enrollment
                ])

    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(HEADERS)
        writer.writerows(rows)

    print(f"Wrote {output_path} ({len(rows):,} rows)")


def main():
    # Build base enrollment data
    base_data = {}
    for ci, (contract_id, carrier, parent) in enumerate(CARRIERS):
        carrier_counties = {}
        for cj, (fips, state, county) in enumerate(COUNTIES):
            # Each carrier has 1-3 plans per county
            n_plans = random.randint(1, 3)
            plans = []
            for p in range(n_plans):
                plan_id = f"{100 + p:03d}"
                plan_type = random.choice(PLAN_TYPES)
                enrollment = base_enrollment(ci, cj)
                plans.append((plan_id, plan_type, enrollment))
            carrier_counties[(fips, state, county)] = plans
        base_data[(contract_id, carrier, parent)] = carrier_counties

    # Month 1: baseline
    prev_path = Path("data/raw/test-2025-11.csv")
    generate_month(prev_path, base_data)

    # Month 2: apply some interesting changes
    changes = {}

    # OUTLIER 1: UnitedHealthcare surges in Miami-Dade (+40%)
    for plan_id, plan_type, enr in base_data[CARRIERS[0]]["12086", "FL", "Miami-Dade"]:
        changes[(CARRIERS[0][0], "12086", plan_id)] = int(enr * 1.40)

    # OUTLIER 2: Humana loses big in Maricopa AZ (-25%)
    for plan_id, plan_type, enr in base_data[CARRIERS[1]]["04013", "AZ", "Maricopa"]:
        changes[(CARRIERS[1][0], "04013", plan_id)] = int(enr * 0.75)

    # OUTLIER 3: Devoted Health enters Los Angeles (new market — was near zero, now 2000+)
    for plan_id, plan_type, enr in base_data[CARRIERS[8]]["06037", "CA", "Los Angeles"]:
        changes[(CARRIERS[8][0], "06037", plan_id)] = 2200

    # OUTLIER 4: Centene/WellCare steadily grows across FL counties
    for fips, state, county in [("12086", "FL", "Miami-Dade"), ("12011", "FL", "Broward"), ("12099", "FL", "Palm Beach")]:
        for plan_id, plan_type, enr in base_data[CARRIERS[5]][(fips, state, county)]:
            changes[(CARRIERS[5][0], fips, plan_id)] = int(enr * 1.15)

    # OUTLIER 5: BCBS collapses in Cook County IL
    for plan_id, plan_type, enr in base_data[CARRIERS[7]]["17031", "IL", "Cook"]:
        changes[(CARRIERS[7][0], "17031", plan_id)] = int(enr * 0.55)

    # Normal noise for everything else (±1-3%)
    for (contract_id, carrier, parent), county_data in base_data.items():
        for (fips, state, county), plans in county_data.items():
            for plan_id, plan_type, enrollment in plans:
                key = (contract_id, fips, plan_id)
                if key not in changes:
                    noise = random.uniform(-0.03, 0.03)
                    changes[key] = max(0, int(enrollment * (1 + noise)))

    curr_path = Path("data/raw/test-2025-12.csv")
    generate_month(curr_path, base_data, changes)

    print(f"\nTest data ready. Run the pipeline with:")
    print(f"  python run.py {prev_path} {curr_path} --month 'December 2025'")
    print(f"\nKnown outliers to verify:")
    print(f"  1. UnitedHealthcare +40% in Miami-Dade FL")
    print(f"  2. Humana -25% in Maricopa AZ")
    print(f"  3. Devoted Health enters Los Angeles CA (new market)")
    print(f"  4. Centene/WellCare +15% across FL counties")
    print(f"  5. BCBS -45% in Cook County IL")


if __name__ == "__main__":
    main()

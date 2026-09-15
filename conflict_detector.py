import pandas as pd
from pathlib import Path


# ============================================================
# BHOOMI-X — CONFLICT DETECTION ENGINE
# Milestone 2.1: Area Conflict Detection
# ============================================================


# ------------------------------------------------------------
# 1. Configuration
# ------------------------------------------------------------

LOW_THRESHOLD = 2.0
MODERATE_THRESHOLD = 5.0
HIGH_THRESHOLD = 10.0


# ------------------------------------------------------------
# 2. Classify area conflict
# ------------------------------------------------------------

def classify_area_conflict(difference_percent):
    """
    Classify the seriousness of an area discrepancy.
    """

    if difference_percent <= LOW_THRESHOLD:
        return "LOW"

    elif difference_percent <= MODERATE_THRESHOLD:
        return "MODERATE"

    elif difference_percent <= HIGH_THRESHOLD:
        return "HIGH"

    else:
        return "CRITICAL"


# ------------------------------------------------------------
# 3. Calculate area conflict
# ------------------------------------------------------------

def calculate_area_conflict(cadastral_area, municipal_area):
    """
    Compare cadastral and municipal recorded areas.
    """

    if pd.isna(cadastral_area) or pd.isna(municipal_area):
        return {
            "area_difference_sqm": None,
            "area_difference_percent": None,
            "severity": "MISSING_DATA"
        }

    if cadastral_area <= 0:
        return {
            "area_difference_sqm": None,
            "area_difference_percent": None,
            "severity": "INVALID_DATA"
        }

    difference = abs(cadastral_area - municipal_area)

    difference_percent = (
        difference / cadastral_area
    ) * 100

    severity = classify_area_conflict(difference_percent)

    return {
        "area_difference_sqm": round(difference, 2),
        "area_difference_percent": round(difference_percent, 2),
        "severity": severity
    }


# ------------------------------------------------------------
# 4. Load harmonization results
# ------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

MATCH_FILE = (
    BASE_DIR
    / "data"
    / "harmonization"
    / "municipal_matches.csv"
)


print("\n" + "=" * 70)
print("       BHOOMI-X AREA CONFLICT DETECTION")
print("=" * 70)


if not MATCH_FILE.exists():

    print("\nERROR: Municipal match file not found.")
    print(f"Expected file: {MATCH_FILE}")

    raise SystemExit


matches = pd.read_csv(MATCH_FILE)


print(f"\nLoaded {len(matches)} matched parcel records.")


# ------------------------------------------------------------
# 5. Detect area conflicts
# ------------------------------------------------------------

results = []

for _, row in matches.iterrows():

    reference_area = row.get("reference_area_sqm")
    municipal_area = row.get("municipal_area_sqm")

    conflict = calculate_area_conflict(
        reference_area,
        municipal_area
    )

    results.append({
       "parcel_id": row.get("parcel_id"),
        "reference_area_sqm": reference_area,
        "municipal_area_sqm": municipal_area,
        **conflict
    })

conflict_df = pd.DataFrame(results)


# ------------------------------------------------------------
# 6. Save results
# ------------------------------------------------------------

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "conflicts"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


OUTPUT_FILE = (
    OUTPUT_DIR
    / "area_conflicts.csv"
)


conflict_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ------------------------------------------------------------
# 7. Summary
# ------------------------------------------------------------

print("\nAREA CONFLICT SUMMARY")
print("-" * 70)

print(
    conflict_df["severity"]
    .value_counts()
    .to_string()
)


print("\nSample results:")
print(
    conflict_df
    .head(15)
    .to_string(index=False)
)


print("\n" + "=" * 70)
print("       AREA CONFLICT DETECTION COMPLETE")
print("=" * 70)
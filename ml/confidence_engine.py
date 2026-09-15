import pandas as pd
from pathlib import Path


# ============================================================
# BHOOMI-X CONFIDENCE & EVIDENCE ENGINE
# ============================================================

print("\nBHOOMI-X CONFIDENCE & EVIDENCE ENGINE")
print("=" * 60)


# ============================================================
# 1. Paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "conflicts"
    / "resolution_recommendations.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "conflicts"
    / "confidence_results.csv"
)


# ============================================================
# 2. Load resolution results
# ============================================================

print("\nLoading resolution recommendations...")

data = pd.read_csv(INPUT_FILE)

print("Records loaded :", len(data))


# ============================================================
# 3. Calculate confidence
# ============================================================

def calculate_confidence(row):

    action = str(
        row.get("recommended_action", "")
    ).upper()

    conflict_count = row.get(
        "conflict_count",
        0
    )

    try:
        conflict_count = int(conflict_count)
    except (ValueError, TypeError):
        conflict_count = 0


    # --------------------------------------------------------
    # No conflict
    # --------------------------------------------------------

    if action == "NO ACTION":

        confidence = 98
        level = "HIGH CONFIDENCE"

        evidence = (
            "No significant conflict was detected "
            "between the available records."
        )


    # --------------------------------------------------------
    # Owner review
    # --------------------------------------------------------

    elif action == "REVIEW OWNER":

        confidence = 80
        level = "MEDIUM CONFIDENCE"

        evidence = (
            "Owner information differs or requires "
            "verification between datasets."
        )


    # --------------------------------------------------------
    # Area review
    # --------------------------------------------------------

    elif action == "REVIEW AREA":

        confidence = 82
        level = "MEDIUM CONFIDENCE"

        evidence = (
            "A difference was detected in the recorded "
            "parcel area."
        )


    # --------------------------------------------------------
    # Geometry review
    # --------------------------------------------------------

    elif action == "REVIEW GEOMETRY":

        confidence = 78
        level = "NEEDS REVIEW"

        evidence = (
            "A difference was detected between parcel "
            "boundaries or geometry."
        )


    # --------------------------------------------------------
    # Multiple conflicts
    # --------------------------------------------------------

    elif action == "MULTIPLE CONFLICTS":

        confidence = 65
        level = "LOW CONFIDENCE"

        evidence = (
            f"{conflict_count} different conflicts were "
            "detected for this parcel."
        )


    # --------------------------------------------------------
    # Unknown
    # --------------------------------------------------------

    else:

        confidence = 50
        level = "LOW CONFIDENCE"

        evidence = (
            "The available information is insufficient "
            "for an automatic recommendation."
        )


    return pd.Series(
        {
            "confidence_score": confidence,
            "confidence_level": level,
            "evidence": evidence
        }
    )


# ============================================================
# 4. Generate confidence results
# ============================================================

print("\nCalculating confidence scores...")

confidence_results = data.apply(
    calculate_confidence,
    axis=1
)


# ============================================================
# 5. Build final output
# ============================================================

final_report = pd.concat(
    [
        data.reset_index(drop=True),
        confidence_results.reset_index(drop=True)
    ],
    axis=1
)


# ============================================================
# 6. Save results
# ============================================================

final_report.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# 7. Display summary
# ============================================================

print("\nCONFIDENCE SUMMARY")
print("=" * 60)

print(
    final_report[
        "confidence_level"
    ]
    .value_counts()
    .to_string()
)


print("\nSample results:")

print(
    final_report[
        [
            "parcel_id",
            "recommended_action",
            "confidence_score",
            "confidence_level",
            "evidence"
        ]
    ]
    .head(15)
    .to_string(index=False)
)


# ============================================================
# 8. Finish
# ============================================================

print("\nOutput file:")
print(OUTPUT_FILE)

print("\n" + "=" * 60)
print("CONFIDENCE & EVIDENCE ENGINE COMPLETE")
print("=" * 60)
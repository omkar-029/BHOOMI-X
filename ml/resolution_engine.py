import pandas as pd
from pathlib import Path


# ============================================================
# BHOOMI-X SMART RESOLUTION ENGINE
# ============================================================

print("\nBHOOMI-X SMART RESOLUTION ENGINE")
print("=" * 60)


# ============================================================
# 1. Paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "conflicts"
    / "unified_conflict_report.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "conflicts"
    / "resolution_recommendations.csv"
)


# ============================================================
# 2. Load unified report
# ============================================================

print("\nLoading unified conflict report...")

report = pd.read_csv(INPUT_FILE)

print("Records loaded :", len(report))


# ============================================================
# 3. Smart resolution function
# ============================================================

def resolve_conflict(row):

    recommendations = []
    explanations = []
    conflict_count = 0

    # --------------------------------------------------------
    # OWNER CHECK
    # --------------------------------------------------------

    owner_relationship = str(
        row.get("relationship", "")
    ).upper()

    if "CONFLICT" in owner_relationship:

        conflict_count += 1

        recommendations.append(
            "REVIEW OWNER"
        )

        cadastral_owner = row.get(
            "cadastral_owner",
            "Unknown"
        )

        municipal_owner = row.get(
            "municipal_owner",
            "Unknown"
        )

        explanations.append(
            f"Owner records differ. "
            f"Cadastral: {cadastral_owner}; "
            f"Municipal: {municipal_owner}."
        )

    elif "REVIEW" in owner_relationship:

        conflict_count += 1

        recommendations.append(
            "REVIEW OWNER"
        )

        explanations.append(
            "Owner names are similar but require verification."
        )


    # --------------------------------------------------------
    # AREA CHECK
    # --------------------------------------------------------

    area_severity = str(
        row.get("severity", "")
    ).upper()

    area_difference = row.get(
        "area_difference_sqm_owner",
        row.get("area_difference_sqm", 0)
    )

    try:
        area_difference = float(area_difference)
    except (ValueError, TypeError):
        area_difference = 0.0

    if area_severity in ["MODERATE", "HIGH"]:

        conflict_count += 1

        recommendations.append(
            "REVIEW AREA"
        )

        explanations.append(
            f"Recorded parcel areas differ by "
            f"{area_difference:.2f} square metres."
        )


    # --------------------------------------------------------
    # GEOMETRY CHECK
    # --------------------------------------------------------

    geometry_conflict = str(
        row.get(
            "conflict_type_geometry",
            row.get("conflict_type", "")
        )
    ).upper()

    if geometry_conflict in [
        "MODERATE GEOMETRY CONFLICT",
        "MAJOR GEOMETRY CONFLICT"
    ]:

        conflict_count += 1

        recommendations.append(
            "REVIEW GEOMETRY"
        )

        reason = row.get(
            "reason_geometry",
            row.get(
                "reason",
                "Boundary difference detected."
            )
        )

        explanations.append(
            f"Geometry issue: {reason}"
        )

    elif geometry_conflict == "MINOR BOUNDARY DIFFERENCE":

        conflict_count += 1

        recommendations.append(
            "REVIEW GEOMETRY"
        )

        explanations.append(
            "A minor boundary difference was detected."
        )


    # ========================================================
    # 4. Final recommendation
    # ========================================================

    if conflict_count == 0:

        action = "NO ACTION"

        explanation = (
            "No significant conflict detected "
            "between the available records."
        )

    elif conflict_count == 1:

        action = recommendations[0]

        explanation = " ".join(
            explanations
        )

    else:

        action = "MULTIPLE CONFLICTS"

        explanation = " ".join(
            explanations
        )


    return pd.Series(
        {
            "conflict_count": conflict_count,
            "recommended_action": action,
            "explanation": explanation
        }
    )


# ============================================================
# 5. Generate recommendations
# ============================================================

print("\nGenerating smart recommendations...")

resolution = report.apply(
    resolve_conflict,
    axis=1
)


# ============================================================
# 6. Combine with parcel information
# ============================================================

output_columns = [
    "parcel_id",
    "municipal_plot_id"
]

output_columns = [
    column
    for column in output_columns
    if column in report.columns
]


resolution_report = pd.concat(
    [
        report[output_columns].reset_index(drop=True),
        resolution.reset_index(drop=True)
    ],
    axis=1
)


# ============================================================
# 7. Save recommendations
# ============================================================

resolution_report.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# 8. Display summary
# ============================================================

print("\nRESOLUTION SUMMARY")
print("=" * 60)

print(
    resolution_report[
        "recommended_action"
    ]
    .value_counts()
    .to_string()
)


print("\nSample recommendations:")

print(
    resolution_report
    .head(15)
    .to_string(index=False)
)


# ============================================================
# 9. Finish
# ============================================================

print("\nOutput file:")
print(OUTPUT_FILE)

print("\n" + "=" * 60)
print("SMART RESOLUTION ENGINE COMPLETE")
print("=" * 60)
import pandas as pd
from pathlib import Path


# ============================================================
# BHOOMI-X OFFICER REVIEW SYSTEM
# ============================================================

print("\nBHOOMI-X OFFICER REVIEW SYSTEM")
print("=" * 60)


# ============================================================
# 1. Paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "conflicts"
    / "confidence_results.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "conflicts"
    / "officer_review_queue.csv"
)


# ============================================================
# 2. Load confidence results
# ============================================================

print("\nLoading confidence results...")

data = pd.read_csv(INPUT_FILE)

print("Records loaded :", len(data))


# ============================================================
# 3. Create officer review status
# ============================================================

def create_review_status(row):

    action = str(
        row.get("recommended_action", "")
    ).upper()

    confidence_level = str(
        row.get("confidence_level", "")
    ).upper()

    # No conflict -> automatically cleared
    if action == "NO ACTION":

        return pd.Series(
            {
                "review_status": "AUTO CLEARED",
                "officer_action": "NOT REQUIRED",
                "officer_comment": ""
            }
        )

    # Conflict -> human officer should review
    return pd.Series(
        {
            "review_status": "PENDING",
            "officer_action": "PENDING",
            "officer_comment": ""
        }
    )


# ============================================================
# 4. Create review information
# ============================================================

print("\nCreating officer review queue...")

review_data = data.apply(
    create_review_status,
    axis=1
)


# ============================================================
# 5. Build review queue
# ============================================================

review_queue = pd.concat(
    [
        data.reset_index(drop=True),
        review_data.reset_index(drop=True)
    ],
    axis=1
)


# ============================================================
# 6. Add priority
# ============================================================

def calculate_priority(row):

    action = str(
        row.get("recommended_action", "")
    ).upper()

    confidence = row.get(
        "confidence_score",
        0
    )

    try:
        confidence = float(confidence)
    except (ValueError, TypeError):
        confidence = 0

    if action == "NO ACTION":
        return "NONE"

    if action == "MULTIPLE CONFLICTS":
        return "HIGH"

    if action == "REVIEW GEOMETRY":
        return "HIGH"

    if action == "REVIEW OWNER":
        return "MEDIUM"

    if action == "REVIEW AREA":
        return "MEDIUM"

    if confidence < 60:
        return "HIGH"

    return "MEDIUM"


review_queue["priority"] = review_queue.apply(
    calculate_priority,
    axis=1
)


# ============================================================
# 7. Save review queue
# ============================================================

review_queue.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# 8. Summary
# ============================================================

print("\nOFFICER REVIEW SUMMARY")
print("=" * 60)

print(
    review_queue[
        "review_status"
    ]
    .value_counts()
    .to_string()
)


print("\nPriority summary:")

print(
    review_queue[
        "priority"
    ]
    .value_counts()
    .to_string()
)


# ============================================================
# 9. Pending cases
# ============================================================

pending = review_queue[
    review_queue["review_status"] == "PENDING"
]


print("\nPending officer reviews :", len(pending))


print("\nSample pending cases:")

columns_to_show = [
    "parcel_id",
    "municipal_plot_id",
    "recommended_action",
    "confidence_score",
    "confidence_level",
    "priority",
    "review_status"
]

columns_to_show = [
    column
    for column in columns_to_show
    if column in pending.columns
]

print(
    pending[
        columns_to_show
    ]
    .head(15)
    .to_string(index=False)
)


# ============================================================
# 10. Finish
# ============================================================

print("\nOutput file:")
print(OUTPUT_FILE)

print("\n" + "=" * 60)
print("OFFICER REVIEW SYSTEM COMPLETE")
print("=" * 60)
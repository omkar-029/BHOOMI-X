import pandas as pd
from pathlib import Path


# ============================================================
# BHOOMI-X OFFICER DECISION SYSTEM
# ============================================================

print("\nBHOOMI-X OFFICER DECISION SYSTEM")
print("=" * 60)


# ============================================================
# 1. Paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "conflicts"
    / "officer_review_queue.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "conflicts"
    / "officer_decisions.csv"
)


# ============================================================
# 2. Load review queue
# ============================================================

print("\nLoading officer review queue...")

data = pd.read_csv(INPUT_FILE)

print("Total records :", len(data))

pending = data[
    data["review_status"].astype(str).str.upper() == "PENDING"
].copy()

print("Pending cases :", len(pending))


# ============================================================
# 3. Remove old decision columns
# ============================================================

# The review queue already contains these columns.
# We remove them before creating the final officer decision.

for column in [
    "officer_action",
    "officer_comment"
]:

    if column in pending.columns:
        pending = pending.drop(
            columns=[column]
        )


# ============================================================
# 4. Create demo officer decisions
# ============================================================

def create_demo_decision(row):

    action = str(
        row.get("recommended_action", "")
    ).upper()

    if action == "REVIEW OWNER":

        return pd.Series(
            {
                "officer_action": "REVIEW",
                "officer_comment":
                    "Verify ownership documents."
            }
        )

    elif action == "REVIEW AREA":

        return pd.Series(
            {
                "officer_action": "REVIEW",
                "officer_comment":
                    "Verify recorded parcel area."
            }
        )

    elif action == "REVIEW GEOMETRY":

        return pd.Series(
            {
                "officer_action": "REVIEW",
                "officer_comment":
                    "Verify parcel boundary."
            }
        )

    else:

        return pd.Series(
            {
                "officer_action": "REVIEW",
                "officer_comment":
                    "Manual verification required."
            }
        )


# ============================================================
# 5. Generate decisions
# ============================================================

print("\nCreating demo officer decisions...")

if pending.empty:

    decision_data = pd.DataFrame(
        columns=[
            "officer_action",
            "officer_comment"
        ]
    )

else:

    decision_data = pending.apply(
        create_demo_decision,
        axis=1
    )


# ============================================================
# 6. Build final decision report
# ============================================================

if pending.empty:

    decision_report = pending.copy()

else:

    decision_report = pd.concat(
        [
            pending.reset_index(drop=True),
            decision_data.reset_index(drop=True)
        ],
        axis=1
    )


# ============================================================
# 7. Save decisions
# ============================================================

decision_report.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# 8. Display summary
# ============================================================

print("\nOFFICER DECISION SUMMARY")
print("=" * 60)

if decision_report.empty:

    print("No decisions generated.")

else:

    print(
        decision_report["officer_action"]
        .value_counts()
        .to_string()
    )


# ============================================================
# 9. Display sample decisions
# ============================================================

print("\nSample officer decisions:")

if not decision_report.empty:

    columns_to_show = [
        "parcel_id",
        "recommended_action",
        "confidence_score",
        "officer_action",
        "officer_comment"
    ]

    columns_to_show = [
        column
        for column in columns_to_show
        if column in decision_report.columns
    ]

    print(
        decision_report[
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
print("OFFICER DECISION SYSTEM COMPLETE")
print("=" * 60)
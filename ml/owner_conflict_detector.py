import pandas as pd
import geopandas as gpd
from pathlib import Path
from difflib import SequenceMatcher
import sys

# Allow Python to find owner_normalizer.py inside the ml folder
sys.path.append(str(Path(__file__).parent))

from owner_normalizer import normalize_owner_name


# --------------------------------------------------
# 1. Paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

MATCH_FILE = (
    PROJECT_ROOT
    / "data"
    / "harmonization"
    / "municipal_matches.csv"
)

CADASTRAL_FILE = (
    PROJECT_ROOT
    / "data"
    / "cadastral"
    / "cadastral.geojson"
)

MUNICIPAL_FILE = (
    PROJECT_ROOT
    / "data"
    / "municipal"
    / "municipal.geojson"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "conflicts"
)

OUTPUT_FILE = OUTPUT_DIR / "owner_conflicts.csv"


# --------------------------------------------------
# 2. Owner similarity
# --------------------------------------------------

def owner_similarity(name_a, name_b):

    a = normalize_owner_name(name_a)
    b = normalize_owner_name(name_b)

    if not a or not b:
        return 0.0

    score = SequenceMatcher(None, a, b).ratio()

    return round(score * 100, 2)


# --------------------------------------------------
# 3. Conflict classification
# --------------------------------------------------

def classify_owner_relationship(score):

    if score >= 90:
        return "LIKELY SAME OWNER"

    elif score >= 70:
        return "REVIEW REQUIRED"

    else:
        return "OWNER CONFLICT"


# --------------------------------------------------
# 4. Load data
# --------------------------------------------------

print("\nBHOOMI-X OWNER CONFLICT DETECTOR")
print("-" * 60)

matches = pd.read_csv(MATCH_FILE)

cadastral = gpd.read_file(CADASTRAL_FILE)

municipal = gpd.read_file(MUNICIPAL_FILE)


# --------------------------------------------------
# ------------------------------------------------------------
# 5. Build robust lookup tables
# ------------------------------------------------------------

def id_key(value):
    """
    Extract the numeric part of an ID.

    Examples:
    P0001  -> 1
    C0001  -> 1
    M-8000 -> 8000
    """
    digits = "".join(ch for ch in str(value) if ch.isdigit())

    if not digits:
        return None

    return int(digits)


cadastral_lookup = {}

for _, row in cadastral.iterrows():
    key = id_key(row["cadastral_id"])

    if key is not None:
        cadastral_lookup[key] = row


municipal_lookup = {}

for _, row in municipal.iterrows():
    key = id_key(row["plot_id"])

    if key is not None:
        municipal_lookup[key] = row


# ------------------------------------------------------------
# 6. Compare owners
# ------------------------------------------------------------

results = []

for _, match in matches.iterrows():

    parcel_id = match["parcel_id"]
    municipal_plot_id = match["municipal_plot_id"]

    parcel_key = id_key(parcel_id)

    if parcel_key is None:
        continue

    # Find cadastral record
    cadastral_row = cadastral_lookup.get(parcel_key)

    # Find municipal record
    municipal_key = id_key(municipal_plot_id)

    municipal_row = municipal_lookup.get(municipal_key)

    if cadastral_row is None or municipal_row is None:
        continue

    cadastral_owner = cadastral_row["owner_name"]
    municipal_owner = municipal_row["property_owner"]

    score = owner_similarity(
        cadastral_owner,
        municipal_owner
    )

    relationship = classify_owner_relationship(score)

    results.append({
        "parcel_id": parcel_id,
        "municipal_plot_id": municipal_plot_id,
        "cadastral_owner": cadastral_owner,
        "municipal_owner": municipal_owner,
        "owner_similarity": score,
        "relationship": relationship
    })


owner_conflict_df = pd.DataFrame(results)


# --------------------------------------------------
# 7. Create result table
# --------------------------------------------------

owner_conflict_df = pd.DataFrame(results)


# --------------------------------------------------
# 8. Save results
# --------------------------------------------------

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

owner_conflict_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# --------------------------------------------------
# 9. Summary
# --------------------------------------------------

print("\nOWNER CONFLICT SUMMARY")
print("-" * 60)

if owner_conflict_df.empty:

    print("No owner comparisons were generated.")

else:

    print(
        owner_conflict_df["relationship"]
        .value_counts()
        .to_string()
    )

    print("\nSample results:")
    print(
        owner_conflict_df
        .head(15)
        .to_string(index=False)
    )


print("\n" + "-" * 60)
print("OWNER CONFLICT DETECTION COMPLETE")
print("-" * 60)

print(f"\nOutput file:")
print(OUTPUT_FILE)
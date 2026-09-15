from pathlib import Path
from difflib import SequenceMatcher

import geopandas as gpd
import pandas as pd


# ============================================================
# BHOOMI-X
# Milestone 1.3 — Intelligent Spatial Harmonization Engine
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

GROUND_TRUTH_FILE = (
    DATA_DIR / "ground_truth" / "ground_truth_projected.geojson"
)

CADASTRAL_FILE = (
    DATA_DIR / "cadastral" / "cadastral.geojson"
)

MUNICIPAL_FILE = (
    DATA_DIR / "municipal" / "municipal.geojson"
)

OUTPUT_DIR = DATA_DIR / "harmonization"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

AREA_TOLERANCE_PERCENT = 5.0

# Weights used to calculate confidence.
# These are intentionally transparent and explainable.
WEIGHTS = {
    "spatial": 0.40,
    "area": 0.25,
    "owner": 0.20,
    "identifier": 0.15,
}


# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------

def normalize_text(value):
    """Normalize names/identifiers for comparison."""

    if pd.isna(value):
        return ""

    return (
        str(value)
        .lower()
        .strip()
        .replace(".", "")
        .replace(",", "")
    )


def text_similarity(value_a, value_b):
    """Return similarity between two text values from 0 to 100."""

    a = normalize_text(value_a)
    b = normalize_text(value_b)

    if not a or not b:
        return 0.0

    return round(
        SequenceMatcher(None, a, b).ratio() * 100,
        2,
    )


def area_similarity(area_a, area_b):
    """Compare two areas and return similarity from 0 to 100."""

    if area_a <= 0 or area_b <= 0:
        return 0.0

    difference = abs(area_a - area_b)
    maximum = max(area_a, area_b)

    difference_percent = (
        difference / maximum
    ) * 100

    similarity = max(
        0,
        100 - difference_percent,
    )

    return round(similarity, 2)


def spatial_similarity(geometry_a, geometry_b):
    """
    Calculate polygon IoU:
    Intersection Area / Union Area.

    Returns 0–100.
    """

    if geometry_a is None or geometry_b is None:
        return 0.0

    if geometry_a.is_empty or geometry_b.is_empty:
        return 0.0

    try:
        intersection = geometry_a.intersection(
            geometry_b
        )

        union = geometry_a.union(
            geometry_b
        )

        if union.area == 0:
            return 0.0

        score = (
            intersection.area
            / union.area
        ) * 100

        return round(score, 2)

    except Exception:
        return 0.0


def calculate_confidence(
    spatial_score,
    area_score,
    owner_score,
    identifier_score,
):
    """Calculate weighted overall confidence."""

    confidence = (
        spatial_score
        * WEIGHTS["spatial"]
        + area_score
        * WEIGHTS["area"]
        + owner_score
        * WEIGHTS["owner"]
        + identifier_score
        * WEIGHTS["identifier"]
    )

    return round(confidence, 2)


def get_status(confidence):
    """Convert confidence into an explainable decision."""

    if confidence >= 90:
        return "HIGH CONFIDENCE"

    if confidence >= 75:
        return "LIKELY MATCH"

    if confidence >= 50:
        return "REVIEW REQUIRED"

    return "LOW CONFIDENCE"


# ------------------------------------------------------------
# Load datasets
# ------------------------------------------------------------

print()
print("=" * 70)
print("          BHOOMI-X INTELLIGENT HARMONIZATION ENGINE")
print("=" * 70)

print("\nLoading datasets...")

ground_truth = gpd.read_file(
    GROUND_TRUTH_FILE
)

cadastral = gpd.read_file(
    CADASTRAL_FILE
)

municipal = gpd.read_file(
    MUNICIPAL_FILE
)


# ------------------------------------------------------------
# CRS harmonization
# ------------------------------------------------------------

# Ground truth is already in projected CRS.
# Cadastral and municipal data are stored in WGS84.
# Convert them to the same metric CRS before spatial analysis.

cadastral = cadastral.to_crs(
    ground_truth.crs
)

municipal = municipal.to_crs(
    ground_truth.crs
)


print(
    f"Ground truth parcels : {len(ground_truth)}"
)

print(
    f"Cadastral records    : {len(cadastral)}"
)

print(
    f"Municipal records    : {len(municipal)}"
)


# ------------------------------------------------------------
# STEP 1
# Cadastral harmonization
# ------------------------------------------------------------

print("\n")
print("-" * 70)
print("STEP 1 — CADASTRAL HARMONIZATION")
print("-" * 70)


cadastral_results = []


for _, parcel in ground_truth.iterrows():

    # Candidate records with the same survey number.
    candidates = cadastral[
        cadastral["survey_no"]
        == parcel["survey_no"]
    ]

    if candidates.empty:
        continue

    candidate = candidates.iloc[0]

    spatial_score = spatial_similarity(
        parcel.geometry,
        candidate.geometry,
    )

    area_score = area_similarity(
        parcel["area_sqm"],
        candidate["recorded_area"],
    )

    owner_score = text_similarity(
        parcel["owner_name"],
        candidate["owner_name"],
    )

    identifier_score = (
        100.0
        if normalize_text(parcel["survey_no"])
        == normalize_text(candidate["survey_no"])
        else 0.0
    )

    confidence = calculate_confidence(
        spatial_score,
        area_score,
        owner_score,
        identifier_score,
    )

    status = get_status(confidence)

    cadastral_results.append({

        "parcel_id":
            parcel["parcel_id"],

        "survey_no":
            parcel["survey_no"],

        "cadastral_id":
            candidate["cadastral_id"],

        "spatial_similarity":
            spatial_score,

        "area_similarity":
            area_score,

        "owner_similarity":
            owner_score,

        "identifier_similarity":
            identifier_score,

        "confidence":
            confidence,

        "status":
            status,

    })


cadastral_results_df = pd.DataFrame(
    cadastral_results
)


# ------------------------------------------------------------
# STEP 2
# Municipal spatial matching
# ------------------------------------------------------------

print("\n")
print("-" * 70)
print("STEP 2 — MUNICIPAL SPATIAL MATCHING")
print("-" * 70)


municipal_results = []


# Build centroid list once for efficiency.
municipal_centroids = (
    municipal.geometry.centroid
)


for _, parcel in ground_truth.iterrows():

    parcel_centroid = (
        parcel.geometry.centroid
    )

    # Calculate distance to every municipal parcel centroid.
    distances = municipal_centroids.distance(
        parcel_centroid
    )

    nearest_index = distances.idxmin()

    candidate = municipal.loc[
        nearest_index
    ]

    spatial_score = spatial_similarity(
        parcel.geometry,
        candidate.geometry,
    )

    area_score = area_similarity(
        parcel["area_sqm"],
        candidate["plot_area"],
    )

    owner_score = text_similarity(
        parcel["owner_name"],
        candidate["property_owner"],
    )

    # Municipal dataset doesn't contain the survey number.
    # Therefore identifier similarity is unavailable.
    identifier_score = 0.0

    confidence = calculate_confidence(
        spatial_score,
        area_score,
        owner_score,
        identifier_score,
    )

    status = get_status(confidence)

    municipal_results.append({

        "parcel_id":
            parcel["parcel_id"],

        "municipal_plot_id":
            candidate["plot_id"],
            "reference_area_sqm":
    parcel["area_sqm"],

"municipal_area_sqm":
    candidate["plot_area"],

        "spatial_similarity":
            spatial_score,

        "area_similarity":
            area_score,

        "owner_similarity":
            owner_score,

        "identifier_similarity":
            identifier_score,

        "confidence":
            confidence,

        "status":
            status,

    })


municipal_results_df = pd.DataFrame(
    municipal_results
)


# ------------------------------------------------------------
# STEP 3
# Save results
# ------------------------------------------------------------

cadastral_output = (
    OUTPUT_DIR
    / "cadastral_matches.csv"
)

municipal_output = (
    OUTPUT_DIR
    / "municipal_matches.csv"
)

cadastral_results_df.to_csv(
    cadastral_output,
    index=False,
)

municipal_results_df.to_csv(
    municipal_output,
    index=False,
)


# ------------------------------------------------------------
# STEP 4
# Summary
# ------------------------------------------------------------

print("\n")
print("=" * 70)
print("                 HARMONIZATION SUMMARY")
print("=" * 70)


print("\nCADASTRAL MATCHING")

print(
    "Records matched:",
    len(cadastral_results_df),
)

print(
    "High confidence:",
    (
        cadastral_results_df["status"]
        == "HIGH CONFIDENCE"
    ).sum(),
)

print(
    "Likely matches:",
    (
        cadastral_results_df["status"]
        == "LIKELY MATCH"
    ).sum(),
)

print(
    "Review required:",
    (
        cadastral_results_df["status"]
        == "REVIEW REQUIRED"
    ).sum(),
)


print("\nMUNICIPAL MATCHING")

print(
    "Records matched:",
    len(municipal_results_df),
)

print(
    "High confidence:",
    (
        municipal_results_df["status"]
        == "HIGH CONFIDENCE"
    ).sum(),
)

print(
    "Likely matches:",
    (
        municipal_results_df["status"]
        == "LIKELY MATCH"
    ).sum(),
)

print(
    "Review required:",
    (
        municipal_results_df["status"]
        == "REVIEW REQUIRED"
    ).sum(),
)


# ------------------------------------------------------------
# STEP 5
# Show suspicious records
# ------------------------------------------------------------

print("\n")
print("-" * 70)
print("SUSPICIOUS CADASTRAL MATCHES")
print("-" * 70)


suspicious_cadastral = (
    cadastral_results_df[
        cadastral_results_df["confidence"] < 95
    ]
    .sort_values(
        "confidence"
    )
)


if suspicious_cadastral.empty:

    print("\nNo suspicious cadastral matches found.")

else:

    print(
        suspicious_cadastral[
            [
                "parcel_id",
                "survey_no",
                "spatial_similarity",
                "area_similarity",
                "owner_similarity",
                "confidence",
                "status",
            ]
        ]
        .head(15)
        .to_string(index=False)
    )


print("\n")
print("-" * 70)
print("SUSPICIOUS MUNICIPAL MATCHES")
print("-" * 70)


suspicious_municipal = (
    municipal_results_df[
        municipal_results_df["confidence"] < 95
    ]
    .sort_values(
        "confidence"
    )
)


if suspicious_municipal.empty:

    print("\nNo suspicious municipal matches found.")

else:

    print(
        suspicious_municipal[
            [
                "parcel_id",
                "municipal_plot_id",
                "spatial_similarity",
                "area_similarity",
                "owner_similarity",
                "confidence",
                "status",
            ]
        ]
        .head(15)
        .to_string(index=False)
    )


# ------------------------------------------------------------
# Final
# ------------------------------------------------------------

print("\n")
print("=" * 70)
print("       BHOOMI-X HARMONIZATION ENGINE COMPLETE")
print("=" * 70)

print("\nOutput files:")

print(cadastral_output)
print(municipal_output)

print("\nMilestone 1.3 complete! 🚀")
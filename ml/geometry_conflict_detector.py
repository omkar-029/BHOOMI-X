import pandas as pd
import geopandas as gpd
from pathlib import Path
# --------------------------------------------------
# 1. Project आणि data paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

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

OUTPUT_FILE = OUTPUT_DIR / "geometry_conflicts.csv"
# --------------------------------------------------
# 2. नकाशांचा data load करणे
# --------------------------------------------------

print("\nBHOOMI-X GEOMETRY CONFLICT DETECTOR")
print("-" * 60)

cadastral = gpd.read_file(CADASTRAL_FILE)
municipal = gpd.read_file(MUNICIPAL_FILE)

print(f"Cadastral parcels loaded : {len(cadastral)}")
print(f"Municipal parcels loaded  : {len(municipal)}")
# --------------------------------------------------
# 3. Check Coordinate Reference Systems (CRS)
# --------------------------------------------------

print("\nCRS INFORMATION")
print("-" * 60)

print("Cadastral CRS :", cadastral.crs)
print("Municipal CRS :", municipal.crs)
# --------------------------------------------------
# 4. Convert to metric CRS for geometry calculations
# --------------------------------------------------

TARGET_CRS = "EPSG:32643"

cadastral_metric = cadastral.to_crs(TARGET_CRS)
municipal_metric = municipal.to_crs(TARGET_CRS)

print("\nCRS CONVERSION")
print("-" * 60)

print("Target CRS :", TARGET_CRS)
print("Cadastral converted :", cadastral_metric.crs)
print("Municipal converted :", municipal_metric.crs)
# --------------------------------------------------
# 5. Geometry similarity
# --------------------------------------------------

def geometry_similarity(geometry_a, geometry_b):
    """
    Calculate how much two parcel boundaries overlap.
    Returns a score from 0 to 100.
    """

    if geometry_a is None or geometry_b is None:
        return 0.0

    if geometry_a.is_empty or geometry_b.is_empty:
        return 0.0

    intersection_area = geometry_a.intersection(geometry_b).area
    union_area = geometry_a.union(geometry_b).area

    if union_area == 0:
        return 0.0

    score = (intersection_area / union_area) * 100

    return round(score, 2)
# --------------------------------------------------
# 6. Geometry conflict classification
# --------------------------------------------------

def classify_geometry_conflict(score):

    if score >= 95:
        return "NO CONFLICT"

    elif score >= 85:
        return "MINOR BOUNDARY DIFFERENCE"

    elif score >= 70:
        return "MODERATE GEOMETRY CONFLICT"

    else:
        return "MAJOR GEOMETRY CONFLICT"
    # --------------------------------------------------
# 7. Explain geometry conflict
# --------------------------------------------------

def explain_geometry_conflict(cadastral_geometry, municipal_geometry):

    centroid_distance = (
        cadastral_geometry.centroid.distance(
            municipal_geometry.centroid
        )
    )

    cadastral_area = cadastral_geometry.area
    municipal_area = municipal_geometry.area

    area_difference = abs(cadastral_area - municipal_area)

    if centroid_distance >= 2:
        reason = "Municipal boundary appears spatially shifted."
        recommendation = "Officer review required."

    elif area_difference >= 10:
        reason = "Parcel areas differ between the two datasets."
        recommendation = "Verify parcel boundary and recorded area."

    else:
        reason = "Boundaries match between cadastral and municipal records."
        recommendation = "No action required."

    return (
        round(centroid_distance, 2),
        round(area_difference, 2),
        reason,
        recommendation
    )
    # --------------------------------------------------
# --------------------------------------------------
# 7. Compare cadastral and municipal boundaries
# --------------------------------------------------

geometry_results = []

# Our synthetic datasets were generated in the same parcel order.
# So row 0 in cadastral corresponds to row 0 in municipal,
# row 1 corresponds to row 1, and so on.

total_parcels = min(
    len(cadastral_metric),
    len(municipal_metric)
)

for i in range(total_parcels):

    cadastral_row = cadastral_metric.iloc[i]
    municipal_row = municipal_metric.iloc[i]

    score = geometry_similarity(
        cadastral_row.geometry,
        municipal_row.geometry
    )

    conflict_type = classify_geometry_conflict(score)
    (
    centroid_distance,
    area_difference,
    reason,
    recommendation
) = explain_geometry_conflict(
    cadastral_row.geometry,
    municipal_row.geometry
)

    geometry_results.append({
    "cadastral_id": cadastral_row["cadastral_id"],
    "municipal_plot_id": municipal_row["plot_id"],
    "geometry_similarity": score,
    "centroid_distance_m": centroid_distance,
    "area_difference_sqm": area_difference,
    "conflict_type": conflict_type,
    "reason": reason,
    "recommendation": recommendation
})


geometry_results_df = pd.DataFrame(geometry_results)

print("\nGEOMETRY COMPARISON")
print("-" * 60)

print("Parcels compared :", len(geometry_results_df))

print("\nConflict summary:")
print(
    geometry_results_df["conflict_type"]
    .value_counts()
    .to_string()
)

print("\nSample results:")
print(
    geometry_results_df
    .head(10)
    .to_string(index=False)
)
# ============================================================
# 8. Save geometry conflict results
# ============================================================

OUTPUT_DIR = PROJECT_ROOT / "data" / "conflicts"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

GEOMETRY_OUTPUT_FILE = (
    OUTPUT_DIR / "geometry_conflicts.csv"
)

geometry_results_df.to_csv(
    GEOMETRY_OUTPUT_FILE,
    index=False
)

print("\nOutput file:")
print(GEOMETRY_OUTPUT_FILE)

print("\nGEOMETRY CONFLICT DETECTION COMPLETE")
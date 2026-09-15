import pandas as pd
import geopandas as gpd
from pathlib import Path


# ============================================================
# BHOOMI-X UNIFIED CONFLICT REPORT
# ============================================================

print("\nBHOOMI-X UNIFIED CONFLICT REPORT")
print("=" * 60)


# ============================================================
# 1. Paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

CONFLICT_DIR = PROJECT_ROOT / "data" / "conflicts"

AREA_FILE = CONFLICT_DIR / "area_conflicts.csv"
OWNER_FILE = CONFLICT_DIR / "owner_conflicts.csv"
GEOMETRY_FILE = CONFLICT_DIR / "geometry_conflicts.csv"

CADASTRAL_FILE = (
    PROJECT_ROOT
    / "data"
    / "cadastral"
    / "cadastral.geojson"
)

OUTPUT_FILE = CONFLICT_DIR / "unified_conflict_report.csv"


# ============================================================
# 2. Load conflict files
# ============================================================

print("\nLoading conflict files...")

area_data = pd.read_csv(AREA_FILE)
owner_data = pd.read_csv(OWNER_FILE)
geometry_data = pd.read_csv(GEOMETRY_FILE)

print("Area conflicts     :", len(area_data))
print("Owner conflicts    :", len(owner_data))
print("Geometry conflicts :", len(geometry_data))


# ============================================================
# 3. Load cadastral data
# ============================================================

print("\nLoading cadastral data...")

cadastral = gpd.read_file(CADASTRAL_FILE)

print("Cadastral parcels  :", len(cadastral))


# ============================================================
# 4. Create survey number → parcel ID mapping
# ============================================================

print("\nCreating parcel mapping...")

parcel_map = cadastral[
    ["cadastral_id", "survey_no"]
].copy()

parcel_map["cadastral_id"] = (
    parcel_map["cadastral_id"]
    .astype(str)
    .str.strip()
)

parcel_map["survey_no"] = (
    pd.to_numeric(
        parcel_map["survey_no"],
        errors="coerce"
    )
)


# ============================================================
# 5. Add parcel ID to area conflicts
# ============================================================

print("\nConnecting area conflicts to parcels...")

area_data["parcel_id"] = (
    area_data["parcel_id"]
    .astype(str)
    .str.strip()
)

print(
    "Area parcel IDs found :",
    area_data["parcel_id"].notna().sum()
)


# ============================================================
# 6. Prepare owner conflicts
# ============================================================

owner_data["parcel_id"] = (
    owner_data["parcel_id"]
    .astype(str)
    .str.strip()
)

owner_data["municipal_plot_id"] = (
    owner_data["municipal_plot_id"]
    .astype(str)
    .str.strip()
)


# ============================================================
# 7. Prepare geometry conflicts
# ============================================================

geometry_data["cadastral_id"] = (
    geometry_data["cadastral_id"]
    .astype(str)
    .str.strip()
)

geometry_data["municipal_plot_id"] = (
    geometry_data["municipal_plot_id"]
    .astype(str)
    .str.strip()
)

geometry_data = geometry_data.rename(
    columns={
        "cadastral_id": "parcel_id"
    }
)


# ============================================================
# 8. Create base report
# ============================================================

print("\nBuilding unified report...")

report = owner_data.copy()


# ============================================================
# 9. Merge area information
# ============================================================

area_columns = [
    "parcel_id",
    "survey_no",
    "reference_area_sqm",
    "municipal_area_sqm",
    "area_difference_sqm",
    "area_difference_percent",
    "severity"
]

area_columns = [
    col for col in area_columns
    if col in area_data.columns
]

report = report.merge(
    area_data[area_columns],
    on="parcel_id",
    how="left"
)


# ============================================================
# 10. Merge geometry information
# ============================================================

geometry_columns = [
    "parcel_id",
    "municipal_plot_id",
    "geometry_similarity",
    "centroid_distance_m",
    "area_difference_sqm",
    "conflict_type",
    "reason",
    "recommendation"
]

geometry_columns = [
    col
    for col in geometry_columns
    if col in geometry_data.columns
]


report = report.merge(
    geometry_data[geometry_columns],
    on=["parcel_id", "municipal_plot_id"],
    how="left",
    suffixes=("_owner", "_geometry")
)


# ============================================================
# 11. Add overall conflict status
# ============================================================

def determine_status(row):

    owner_conflict = str(
        row.get("relationship", "")
    )

    geometry_conflict = str(
        row.get("conflict_type_geometry", "")
    )

    area_severity = str(
        row.get("severity", "")
    )

    if (
        "CONFLICT" in owner_conflict
        or "CONFLICT" in geometry_conflict
        or area_severity in ["MODERATE", "HIGH"]
    ):
        return "REVIEW REQUIRED"

    return "NO MAJOR CONFLICT"


report["overall_status"] = report.apply(
    determine_status,
    axis=1
)


# ============================================================
# 12. Save report
# ============================================================

report.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# 13. Display results
# ============================================================

print("\nUNIFIED REPORT SUMMARY")
print("=" * 60)

print("Total unified records :", len(report))

print("\nStatus summary:")

print(
    report["overall_status"]
    .value_counts()
    .to_string()
)


print("\nSample unified records:")

print(
    report
    .head(10)
    .to_string(index=False)
)


print("\nOutput file:")
print(OUTPUT_FILE)

print("\n" + "=" * 60)
print("UNIFIED CONFLICT REPORT COMPLETE")
print("=" * 60)
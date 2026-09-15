from pathlib import Path
import random

import geopandas as gpd
import pandas as pd
from shapely.affinity import translate
from shapely.geometry import Polygon


# ============================================================
# BHOOMI-X
# Milestone 1.1 — Synthetic Urban Land Dataset Generator
# ============================================================

random.seed(42)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

FOLDERS = {
    "ground_truth": DATA_DIR / "ground_truth",
    "cadastral": DATA_DIR / "cadastral",
    "municipal": DATA_DIR / "municipal",
    "revenue": DATA_DIR / "revenue",
    "drone": DATA_DIR / "drone",
}

for folder in FOLDERS.values():
    folder.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# SETTINGS
# ------------------------------------------------------------

NUM_ROWS = 20
NUM_COLUMNS = 25

# Each synthetic parcel is 40m x 30m
PARCEL_WIDTH = 40
PARCEL_HEIGHT = 30

# Synthetic city origin near an Indian urban area.
# We create geometry in UTM meters first.
CITY_X = 300000
CITY_Y = 2100000

# Projected CRS for metric calculations.
# UTM Zone 43N.
PROJECTED_CRS = "EPSG:32643"

# CRS used for GeoJSON/web mapping.
WEB_CRS = "EPSG:4326"


OWNERS = [
    "Rajesh Kumar",
    "Suresh Patil",
    "Amit Sharma",
    "Priya Singh",
    "Neha Verma",
    "Vijay More",
    "Anita Joshi",
    "Rohit Kulkarni",
    "Sunita Pawar",
    "Mahesh Deshmukh",
]

LAND_USES = [
    "Residential",
    "Commercial",
    "Mixed Use",
    "Vacant",
]


# ------------------------------------------------------------
# 1. CREATE GROUND TRUTH
# ------------------------------------------------------------

ground_truth_records = []

parcel_number = 1

for row in range(NUM_ROWS):

    for column in range(NUM_COLUMNS):

        x1 = CITY_X + column * PARCEL_WIDTH
        y1 = CITY_Y + row * PARCEL_HEIGHT

        x2 = x1 + PARCEL_WIDTH
        y2 = y1 + PARCEL_HEIGHT

        geometry = Polygon([
            (x1, y1),
            (x2, y1),
            (x2, y2),
            (x1, y2),
            (x1, y1),
        ])

        area = geometry.area

        ground_truth_records.append({
            "parcel_id": f"P{parcel_number:04d}",
            "survey_no": f"SRV-{1000 + parcel_number}",
            "owner_name": random.choice(OWNERS),
            "area_sqm": round(area, 2),
            "land_use": random.choice(LAND_USES),
            "geometry": geometry,
        })

        parcel_number += 1


ground_truth = gpd.GeoDataFrame(
    ground_truth_records,
    crs=PROJECTED_CRS,
)


# Save projected version for analysis
ground_truth.to_file(
    FOLDERS["ground_truth"] / "ground_truth_projected.geojson",
    driver="GeoJSON",
)

# Save WGS84 version for web maps
ground_truth.to_crs(WEB_CRS).to_file(
    FOLDERS["ground_truth"] / "ground_truth.geojson",
    driver="GeoJSON",
)

print(f"[1/4] Ground truth created: {len(ground_truth)} parcels")


# ------------------------------------------------------------
# 2. CREATE CADASTRAL DATASET
# ------------------------------------------------------------

cadastral = ground_truth.copy()

cadastral["cadastral_id"] = cadastral["parcel_id"]
cadastral["recorded_area"] = cadastral["area_sqm"]

cadastral = cadastral[
    [
        "cadastral_id",
        "survey_no",
        "owner_name",
        "recorded_area",
        "land_use",
        "geometry",
    ]
]


# ----- Inject realistic area errors -----

area_error_indices = [10, 25, 70, 120, 200]

for index in area_error_indices:
    cadastral.loc[index, "recorded_area"] *= 0.97


# ----- Inject owner-name variations -----

cadastral.loc[5, "owner_name"] = "Rajesh K."
cadastral.loc[15, "owner_name"] = "Suresh P."
cadastral.loc[35, "owner_name"] = "Amit S."


# ----- Save -----

cadastral.to_crs(WEB_CRS).to_file(
    FOLDERS["cadastral"] / "cadastral.geojson",
    driver="GeoJSON",
)

print("[2/4] Cadastral dataset created")


# ------------------------------------------------------------
# 3. CREATE MUNICIPAL DATASET
# ------------------------------------------------------------

municipal = ground_truth.copy()

municipal["plot_id"] = [
    f"M-{8000 + i}"
    for i in range(len(municipal))
]

municipal["property_owner"] = municipal["owner_name"]
municipal["plot_area"] = municipal["area_sqm"]
municipal["property_type"] = municipal["land_use"]

municipal = municipal[
    [
        "plot_id",
        "property_owner",
        "plot_area",
        "property_type",
        "geometry",
    ]
]


# ----- Area discrepancies -----

municipal.loc[30, "plot_area"] *= 1.03
municipal.loc[50, "plot_area"] *= 0.96
municipal.loc[100, "plot_area"] *= 1.04
municipal.loc[150, "plot_area"] *= 0.95
municipal.loc[250, "plot_area"] *= 1.02


# ----- Geometry shift -----

municipal.loc[40, "geometry"] = translate(
    municipal.loc[40, "geometry"],
    xoff=2.0,
    yoff=1.5,
)


# ----- Save -----

municipal.to_crs(WEB_CRS).to_file(
    FOLDERS["municipal"] / "municipal.geojson",
    driver="GeoJSON",
)

print("[3/4] Municipal dataset created")


# ------------------------------------------------------------
# 4. CREATE REVENUE DATASET
# ------------------------------------------------------------

revenue = ground_truth.copy()

revenue["survey_number"] = revenue["survey_no"]
revenue["holder_name"] = revenue["owner_name"]
revenue["registered_area"] = revenue["area_sqm"]
revenue["land_category"] = revenue["land_use"]

revenue = revenue[
    [
        "survey_number",
        "holder_name",
        "registered_area",
        "land_category",
    ]
]


# ----- Owner variations -----

revenue.loc[20, "holder_name"] = "R. Kumar"
revenue.loc[60, "holder_name"] = "Vijay M."
revenue.loc[90, "holder_name"] = "Neha V."


# ----- Area discrepancies -----

revenue.loc[45, "registered_area"] *= 0.95
revenue.loc[75, "registered_area"] *= 1.04


# ----- Save -----

revenue.to_csv(
    FOLDERS["revenue"] / "revenue.csv",
    index=False,
)

print("[4/4] Revenue dataset created")


# ------------------------------------------------------------
# 5. CREATE DRONE / ORI BUILDING FOOTPRINTS
# ------------------------------------------------------------

drone_records = []

for index, parcel in ground_truth.iterrows():

    # Approximately 65% of parcels contain buildings.
    if random.random() > 0.65:
        continue

    minx, miny, maxx, maxy = parcel.geometry.bounds

    building_width = (maxx - minx) * 0.55
    building_height = (maxy - miny) * 0.55

    building_x = minx + (maxx - minx) * 0.225
    building_y = miny + (maxy - miny) * 0.225

    building = Polygon([
        (building_x, building_y),
        (building_x + building_width, building_y),
        (
            building_x + building_width,
            building_y + building_height,
        ),
        (building_x, building_y + building_height),
        (building_x, building_y),
    ])

    drone_records.append({
        "parcel_reference": parcel["parcel_id"],
        "building_id": f"B-{index + 1:04d}",
        "building_area_sqm": round(building.area, 2),
        "geometry": building,
    })


drone = gpd.GeoDataFrame(
    drone_records,
    crs=PROJECTED_CRS,
)

drone.to_crs(WEB_CRS).to_file(
    FOLDERS["drone"] / "drone_buildings.geojson",
    driver="GeoJSON",
)

print(f"Drone/ORI building footprints created: {len(drone)}")


# ------------------------------------------------------------
# 6. DATASET SUMMARY
# ------------------------------------------------------------

print()
print("=" * 55)
print("              BHOOMI-X DATASET READY")
print("=" * 55)

print(f"Ground truth parcels : {len(ground_truth)}")
print(f"Cadastral parcels    : {len(cadastral)}")
print(f"Municipal parcels    : {len(municipal)}")
print(f"Revenue records      : {len(revenue)}")
print(f"Drone buildings      : {len(drone)}")

print()
print("Intentional conflicts injected:")
print("  • Cadastral area discrepancies")
print("  • Cadastral owner-name variations")
print("  • Municipal area discrepancies")
print("  • Municipal geometry shift")
print("  • Revenue owner-name variations")
print("  • Revenue area discrepancies")

print()
print("Dataset location:")
print(DATA_DIR)

print()
print("Milestone 1.1 complete!")
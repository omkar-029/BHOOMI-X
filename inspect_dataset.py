from pathlib import Path

import geopandas as gpd
import pandas as pd


# ============================================================
# BHOOMI-X
# Milestone 1.2 — Dataset Inspector
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

REVENUE_FILE = (
    DATA_DIR / "revenue" / "revenue.csv"
)


# ------------------------------------------------------------
# Load datasets
# ------------------------------------------------------------

print("\nLoading BHOOMI-X datasets...\n")

ground_truth = gpd.read_file(GROUND_TRUTH_FILE)
cadastral = gpd.read_file(CADASTRAL_FILE)
municipal = gpd.read_file(MUNICIPAL_FILE)
revenue = pd.read_csv(REVENUE_FILE)

print("Datasets loaded successfully.\n")


# ------------------------------------------------------------
# Basic statistics
# ------------------------------------------------------------

print("=" * 65)
print("                 BHOOMI-X DATASET INSPECTOR")
print("=" * 65)

print(f"\nGround truth parcels : {len(ground_truth)}")
print(f"Cadastral records    : {len(cadastral)}")
print(f"Municipal records    : {len(municipal)}")
print(f"Revenue records      : {len(revenue)}")


# ------------------------------------------------------------
# Check missing values
# ------------------------------------------------------------

print("\n" + "-" * 65)
print("MISSING VALUE CHECK")
print("-" * 65)

print("\nCadastral:")
print(cadastral.isna().sum())

print("\nMunicipal:")
print(municipal.isna().sum())

print("\nRevenue:")
print(revenue.isna().sum())


# ------------------------------------------------------------
# AREA DISCREPANCY ANALYSIS
# ------------------------------------------------------------

print("\n" + "-" * 65)
print("AREA DISCREPANCY ANALYSIS")
print("-" * 65)

# Join cadastral records to ground truth using survey number
area_check = ground_truth[
    ["parcel_id", "survey_no", "area_sqm"]
].merge(
    cadastral[
        ["cadastral_id", "survey_no", "recorded_area"]
    ],
    on="survey_no",
    how="inner",
)

area_check["area_difference_sqm"] = (
    area_check["recorded_area"]
    - area_check["area_sqm"]
)

area_check["area_difference_percent"] = (
    area_check["area_difference_sqm"].abs()
    / area_check["area_sqm"]
    * 100
)

area_conflicts = area_check[
    area_check["area_difference_percent"] > 1
]

print(
    f"\nCadastral area conflicts (>1%): "
    f"{len(area_conflicts)}"
)

if len(area_conflicts) > 0:

    print("\nTop cadastral area conflicts:")

    print(
        area_conflicts[
            [
                "parcel_id",
                "survey_no",
                "area_sqm",
                "recorded_area",
                "area_difference_percent",
            ]
        ]
        .sort_values(
            "area_difference_percent",
            ascending=False,
        )
        .head(10)
        .to_string(index=False)
    )


# ------------------------------------------------------------
# OWNER NAME ANALYSIS
# ------------------------------------------------------------

print("\n" + "-" * 65)
print("OWNER NAME CONSISTENCY ANALYSIS")
print("-" * 65)


owner_check = ground_truth[
    ["parcel_id", "survey_no", "owner_name"]
].merge(
    cadastral[
        ["survey_no", "owner_name"]
    ],
    on="survey_no",
    how="inner",
    suffixes=("_ground_truth", "_cadastral"),
)


owner_conflicts = owner_check[
    owner_check["owner_name_ground_truth"]
    != owner_check["owner_name_cadastral"]
]


print(
    f"\nCadastral owner-name conflicts: "
    f"{len(owner_conflicts)}"
)

if len(owner_conflicts) > 0:

    print("\nOwner-name conflicts:")

    print(
        owner_conflicts[
            [
                "parcel_id",
                "survey_no",
                "owner_name_ground_truth",
                "owner_name_cadastral",
            ]
        ]
        .head(10)
        .to_string(index=False)
    )


# ------------------------------------------------------------
# MUNICIPAL AREA ANALYSIS
# ------------------------------------------------------------

print("\n" + "-" * 65)
print("MUNICIPAL AREA ANALYSIS")
print("-" * 65)


municipal_check = ground_truth[
    ["parcel_id", "area_sqm"]
].merge(
    municipal[
        ["plot_id", "plot_area"]
    ],
    left_index=True,
    right_index=True,
    how="inner",
)

municipal_check["difference_percent"] = (
    (
        municipal_check["plot_area"]
        - municipal_check["area_sqm"]
    ).abs()
    / municipal_check["area_sqm"]
    * 100
)

municipal_conflicts = municipal_check[
    municipal_check["difference_percent"] > 1
]

print(
    f"\nMunicipal area conflicts (>1%): "
    f"{len(municipal_conflicts)}"
)


# ------------------------------------------------------------
# GEOMETRY VALIDATION
# ------------------------------------------------------------

print("\n" + "-" * 65)
print("GEOMETRY VALIDATION")
print("-" * 65)

invalid_ground_truth = (
    ~ground_truth.geometry.is_valid
).sum()

invalid_cadastral = (
    ~cadastral.geometry.is_valid
).sum()

invalid_municipal = (
    ~municipal.geometry.is_valid
).sum()

print(
    f"\nInvalid ground-truth geometries : "
    f"{invalid_ground_truth}"
)

print(
    f"Invalid cadastral geometries    : "
    f"{invalid_cadastral}"
)

print(
    f"Invalid municipal geometries    : "
    f"{invalid_municipal}"
)


# ------------------------------------------------------------
# DATASET SUMMARY
# ------------------------------------------------------------

print("\n" + "=" * 65)
print("                    INSPECTION SUMMARY")
print("=" * 65)

total_conflicts = (
    len(area_conflicts)
    + len(owner_conflicts)
    + len(municipal_conflicts)
)

print(
    f"\nTotal detected attribute conflicts: "
    f"{total_conflicts}"
)

print(
    f"  • Cadastral area conflicts   : "
    f"{len(area_conflicts)}"
)

print(
    f"  • Owner-name conflicts       : "
    f"{len(owner_conflicts)}"
)

print(
    f"  • Municipal area conflicts   : "
    f"{len(municipal_conflicts)}"
)

print(
    f"\nInvalid geometries:"
)

print(
    f"  • Ground truth : {invalid_ground_truth}"
)

print(
    f"  • Cadastral   : {invalid_cadastral}"
)

print(
    f"  • Municipal   : {invalid_municipal}"
)

print("\n" + "=" * 65)
print("              MILESTONE 1.2 COMPLETE")
print("=" * 65)
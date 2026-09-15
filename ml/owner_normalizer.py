import re


def normalize_owner_name(name):
    """
    Convert an owner name into a consistent format
    so names from different government datasets
    can be compared more reliably.
    """

    if name is None:
        return ""

    # Convert to string
    name = str(name)

    # Convert to lowercase
    name = name.lower()

    # Remove punctuation
    name = re.sub(r"[^a-z0-9\s]", " ", name)

    # Remove extra spaces
    name = re.sub(r"\s+", " ", name).strip()

    return name


# --------------------------------------------------
# TEST
# --------------------------------------------------

test_names = [
    "Rajesh Kumar",
    "RAJESH KUMAR",
    "  Rajesh   Kumar  ",
    "Rajesh-Kumar",
]

print("\nBHOOMI-X OWNER NAME NORMALIZER")
print("-" * 50)

for name in test_names:
    print(f"{name!r}  ->  {normalize_owner_name(name)!r}")

print("-" * 50)
print("OWNER NORMALIZATION COMPLETE")
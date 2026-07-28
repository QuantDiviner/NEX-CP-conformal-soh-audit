#!/usr/bin/env python3
"""Print manual download instructions for the three public battery datasets.

This repository does not redistribute raw battery data, and the download
portals of all three datasets require manual interaction (registration forms,
terms-of-use pages, or multi-file archives), so no automated downloading is
attempted here. Running this script prints where to obtain each dataset and
where to place it locally.

Expected local layout after manual download:

    data/raw/calce/    CALCE Excel workbooks (*.xlsx), any subfolder layout
    data/raw/nasa/     NASA PCoE "cleaned_dataset" (metadata.csv + data files)
    data/raw/oxford/   Oxford_Battery_Degradation_Dataset_1.mat

Once the raw files are in place, run:

    python scripts/preprocess_real_battery.py

which builds data/processed/real_battery_cycle_level_features.csv and the
split manifests under data/splits/.
"""

from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"

DATASETS = [
    {
        "name": "CALCE Battery Research Group (University of Maryland)",
        "url": "https://calce.umd.edu/battery-data",
        "place_under": "data/raw/calce/",
        "notes": (
            "Download the lithium-ion cell cycling Excel workbooks (*.xlsx). "
            "Any subfolder layout works: the preprocessing script globs "
            "recursively for *.xlsx files."
        ),
    },
    {
        "name": "NASA Ames Prognostics Center of Excellence (PCoE) Data Set Repository",
        "url": (
            "https://www.nasa.gov/intelligent-systems-division/"
            "discovery-and-systems-health/pcoe/pcoe-data-set-repository/"
        ),
        "place_under": "data/raw/nasa/",
        "notes": (
            "Use the Li-ion battery 'cleaned_dataset' archive. The "
            "preprocessing script expects cleaned_dataset/metadata.csv and "
            "the accompanying per-run data files."
        ),
    },
    {
        "name": "Oxford Battery Degradation Dataset 1 (Oxford Research Archive)",
        "url": "https://ora.ox.ac.uk/objects/uuid:03ba4b01-cfed-46d3-9b1a-7d4a7bdf6fac",
        "place_under": "data/raw/oxford/",
        "notes": (
            "Download Oxford_Battery_Degradation_Dataset_1.mat and place the "
            ".mat file directly under data/raw/oxford/."
        ),
    },
]


def main() -> None:
    print("=" * 72)
    print("Manual data acquisition guide (no automated download is performed)")
    print("=" * 72)
    print(f"\nTarget raw-data root: {RAW_DIR}\n")
    for i, ds in enumerate(DATASETS, start=1):
        print(f"[{i}] {ds['name']}")
        print(f"    Source page : {ds['url']}")
        print(f"    Place under : {ds['place_under']}")
        print(f"    Notes       : {ds['notes']}")
        print()
    print("After placing the files, run:")
    print("    python scripts/preprocess_real_battery.py")
    print("to build the QA-gated cycle-level SOH table and split manifests.")


if __name__ == "__main__":
    main()

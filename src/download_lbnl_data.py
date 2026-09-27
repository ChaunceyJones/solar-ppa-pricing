"""
Downloads the LBNL Utility-Scale Solar 2025 Edition data file, confirmed directly against the
source before writing this script (data.openei.org/submissions/8541 — published Sep 2025,
updated Oct 2025, CC BY 4.0 licensed).

The source filename contains literal spaces and parentheses, so the URL needs proper encoding —
this is handled here rather than left for the person running it to get wrong.

Usage:
    python src/download_lbnl_data.py                # main 57-tab workbook (54.31 MB)
    python src/download_lbnl_data.py --companion     # smaller companion file (1.59 MB):
                                                       # per-plant annual energy/capacity value
"""

import argparse
from pathlib import Path
from urllib.parse import quote

import requests

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"

# Confirmed directly against data.openei.org/submissions/8541 before use.
MAIN_FILE_URL = "https://data.openei.org/files/8541/2025 Utility-Scale Solar Data Update (1).xlsx"
MAIN_FILE_NAME = "utility_scale_solar_2025_data_update.xlsx"

COMPANION_FILE_URL = (
    "https://data.openei.org/files/8541/"
    "Project-level annual energy and capacity value estimates through 2024.xlsx"
)
COMPANION_FILE_NAME = "project_level_annual_energy_capacity_value.xlsx"


def download(url: str, out_name: str):
    encoded_url = quote(url, safe=":/")
    print(f"Downloading {out_name} ...")
    resp = requests.get(encoded_url, stream=True, timeout=60)
    resp.raise_for_status()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAW_DIR / out_name
    total = int(resp.headers.get("content-length", 0))
    written = 0
    with open(out_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024 * 1024):
            f.write(chunk)
            written += len(chunk)
            if total:
                print(f"\r  {written / 1e6:.1f} / {total / 1e6:.1f} MB", end="", flush=True)
    print(f"\nSaved to {out_path} ({written / 1e6:.1f} MB)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--companion", action="store_true",
                         help="Download the smaller companion file instead of the main workbook")
    args = parser.parse_args()

    if args.companion:
        download(COMPANION_FILE_URL, COMPANION_FILE_NAME)
    else:
        download(MAIN_FILE_URL, MAIN_FILE_NAME)
        print("\nNext: run `python src/inspect_tabs.py` to see what's actually in the 57 tabs "
              "before deciding what to load.")

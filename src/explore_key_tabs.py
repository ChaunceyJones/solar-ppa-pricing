"""
Full exploration of the two tabs that look most promising after inspect_tabs.py's overview:
- Individual_Project_Data: the master project-level table
- LevelTen & Trio 2024 PPA Index: a real third-party market-price benchmark

Usage:
    python src/explore_key_tabs.py
"""

from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
WORKBOOK_PATH = RAW_DIR / "utility_scale_solar_2025_data_update.xlsx"

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)


def explore(sheet_name: str, n_rows: int = 5):
    print(f"\n{'=' * 80}\n{sheet_name}\n{'=' * 80}")
    df = pd.read_excel(WORKBOOK_PATH, sheet_name=sheet_name)
    print(f"Shape: {df.shape}")
    print(f"\nColumns:\n{df.columns.tolist()}")
    print(f"\nDtypes:\n{df.dtypes}")
    print(f"\nFirst {n_rows} rows:")
    print(df.head(n_rows))
    return df


if __name__ == "__main__":
    if not WORKBOOK_PATH.exists():
        raise SystemExit(f"{WORKBOOK_PATH} not found — run download_lbnl_data.py first.")

    explore("Individual_Project_Data")
    explore("LevelTen & Trio 2024 PPA Index")

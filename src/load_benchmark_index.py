"""
Loads the LevelTen & Trio 2024 PPA Index tab cleanly.

Two things this tab needs that a plain pd.read_excel() default won't handle:
1. A two-row merged header (row 25: "Region" / a combined label; row 26: "Level10" / "Trio")
   rather than a single header row — found by inspecting raw rows directly (see
   peek_raw_rows.py), not by guessing.
2. Some cells contain literal Excel formula-error strings ("#N/A", "#DIV/0!") instead of
   numbers — ISO-NE and NYISO both have at least one broken value in LBNL's own workbook.
   These need to become proper NaN, not be left as strings that silently break downstream math.

Usage:
    python src/load_benchmark_index.py
"""

from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
WORKBOOK_PATH = RAW_DIR / "utility_scale_solar_2025_data_update.xlsx"

EXCEL_ERROR_STRINGS = ["#N/A", "#DIV/0!", "#VALUE!", "#REF!", "#NAME?", "#NULL!", "#NUM!"]


def load_benchmark_index() -> pd.DataFrame:
    df = pd.read_excel(
        WORKBOOK_PATH,
        sheet_name="LevelTen & Trio 2024 PPA Index",
        skiprows=26,  # data starts row 27; rows 25-26 are the merged header, handled manually below
        header=None,
        names=["region", "levelten_ppa_2024_usd_mwh", "trio_ppa_2024_usd_mwh"],
        nrows=9,  # rows 27-35 inclusive
    )

    for col in ["levelten_ppa_2024_usd_mwh", "trio_ppa_2024_usd_mwh"]:
        df[col] = df[col].replace(EXCEL_ERROR_STRINGS, pd.NA)
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


if __name__ == "__main__":
    if not WORKBOOK_PATH.exists():
        raise SystemExit(f"{WORKBOOK_PATH} not found — run download_lbnl_data.py first.")

    df = load_benchmark_index()
    print(df)
    print(f"\n{df.isna().sum().sum()} formula-error cells converted to NaN.")

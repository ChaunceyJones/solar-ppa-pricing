"""
Builds the core pricing analysis table: project-level PPA prices, filtered to rows where a
price is actually disclosed, joined against the regional LevelTen/Trio market benchmark from
load_benchmark_index.py.

Key filtering decision, stated explicitly rather than silently applied:
- Only rows with a non-null 'Levelized PV PPA 2024$/MWh' are kept. Most projects in the source
  don't have a disclosed PPA price at all (utility self-build projects typically don't have an
  arm's-length PPA) — this is a real selection-bias caveat, not a data quality issue to hide.
  See README Limitations.
- Restricted to Solar Tech Main == 'PV' (excludes CSP), since CSP pricing isn't structured the
  same way and the LevelTen/Trio benchmark is solar-PV-specific.

Usage:
    python src/build_pricing_table.py

Writes:
    data/processed/pricing_table.csv
"""

from pathlib import Path

import pandas as pd

from load_benchmark_index import load_benchmark_index

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"
WORKBOOK_PATH = RAW_DIR / "utility_scale_solar_2025_data_update.xlsx"

PPA_COL = "Levelized PV PPA 2024$/MWh"


def load_projects() -> pd.DataFrame:
    df = pd.read_excel(WORKBOOK_PATH, sheet_name="Individual_Project_Data")
    total = len(df)

    df = df[df["Solar Tech Main"] == "PV"].copy()
    after_pv_filter = len(df)

    df = df.dropna(subset=[PPA_COL]).copy()
    after_ppa_filter = len(df)

    print(f"Loaded {total} total projects.")
    print(f"  -> {after_pv_filter} after restricting to Solar Tech Main == 'PV' (excludes CSP)")
    print(f"  -> {after_ppa_filter} after keeping only rows with a disclosed PPA price "
          f"({after_ppa_filter / after_pv_filter:.0%} of PV projects have one)")
    return df


def build_pricing_table() -> pd.DataFrame:
    projects = load_projects()
    benchmark = load_benchmark_index()

    df = projects.merge(
        benchmark,
        left_on="Region",
        right_on="region",
        how="left",
    )

    unmatched = df["region"].isna().sum()
    if unmatched:
        unmatched_regions = df.loc[df["region"].isna(), "Region"].unique()
        print(f"\nWarning: {unmatched} projects didn't match a benchmark region. "
              f"Unmatched Region values: {list(unmatched_regions)}")
        print("These will have a NaN benchmark comparison rather than being silently dropped.")

    df["vs_levelten_usd_mwh"] = df[PPA_COL] - df["levelten_ppa_2024_usd_mwh"]
    df["vs_trio_usd_mwh"] = df[PPA_COL] - df["trio_ppa_2024_usd_mwh"]

    return df


if __name__ == "__main__":
    if not WORKBOOK_PATH.exists():
        raise SystemExit(f"{WORKBOOK_PATH} not found — run download_lbnl_data.py first.")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df = build_pricing_table()
    df.to_csv(PROCESSED_DIR / "pricing_table.csv", index=False)
    print(f"\nSaved {len(df)} rows to data/processed/pricing_table.csv")

    # Diagnostic: is the benchmark gap actually driven by project vintage rather than real
    # pricing skill? The 2024 benchmark should only be a fair comparison for recent-vintage
    # projects — an old project's price reflects a completely different cost era, not whether
    # the deal itself was priced well.
    print(f"\nDiagnostic — mean vs_levelten_usd_mwh by COD year (checking for a vintage effect):")
    by_year = df.groupby("Solar COD Year")["vs_levelten_usd_mwh"].agg(["mean", "count"])
    print(by_year)

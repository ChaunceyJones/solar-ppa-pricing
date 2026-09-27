"""
Two separate, both-valid analyses built from data/processed/pricing_table.csv:

1. PPA price trend over time (all vintages) — the well-documented industry cost decline,
   showing up directly in this project's own disclosed-PPA subset.
2. Recent-vintage (2022-2024) benchmark comparison — the actually fair version of "is this
   priced well relative to the market," restricted to projects from the same era as the
   2024 LevelTen/Trio benchmark. Segment counts are printed and thin segments (n<5) are
   explicitly flagged rather than reported as if they were reliable.

Usage:
    python src/analyze_pricing.py

Reads:
    data/processed/pricing_table.csv

Writes:
    data/processed/ppa_price_trend.png
    data/processed/recent_vintage_segments.csv
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"

PPA_COL = "Levelized PV PPA 2024$/MWh"
LCOE_COL = "PV LCOE no Tax Credits (2024$/MWh)"
MIN_SEGMENT_N = 5  # segments smaller than this are flagged, not reported as reliable


def load_pricing_table() -> pd.DataFrame:
    return pd.read_csv(PROCESSED_DIR / "pricing_table.csv")


def plot_price_trend(df: pd.DataFrame):
    by_year = df.groupby("Solar COD Year").agg(
        median_ppa=(PPA_COL, "median"),
        median_lcoe=(LCOE_COL, "median"),
        n=(PPA_COL, "count"),
    ).reset_index()

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(by_year["Solar COD Year"], by_year["median_ppa"], marker="o",
            label="Median disclosed PPA price")
    ax.plot(by_year["Solar COD Year"], by_year["median_lcoe"], marker="o", linestyle="--",
            label="Median LCOE (no tax credits)", alpha=0.7)
    ax.set_xlabel("COD Year")
    ax.set_ylabel("2024$/MWh")
    ax.set_title("Solar PPA Price and LCOE Trend by Project Vintage")
    ax.legend()
    plt.tight_layout()
    plt.savefig(PROCESSED_DIR / "ppa_price_trend.png", dpi=150)
    plt.close(fig)

    print("Price trend by vintage (median, with sample size):")
    print(by_year.to_string(index=False))
    print(f"\nSaved chart to data/processed/ppa_price_trend.png")


def recent_vintage_segments(df: pd.DataFrame) -> pd.DataFrame:
    recent = df[df["Solar COD Year"] >= 2022].copy()
    print(f"\n{len(recent)} projects from 2022-2024 vintage with a disclosed PPA price.")

    rows = []
    for segment_col in ["Region", "Offtaker Type"]:
        for value, group in recent.groupby(segment_col):
            n = len(group)
            n_with_benchmark = group["vs_levelten_usd_mwh"].notna().sum()

            if n < MIN_SEGMENT_N:
                status = "too few projects"
                mean_val = None
            elif n_with_benchmark < MIN_SEGMENT_N:
                # e.g. NYISO: enough projects, but the region's own LevelTen/Trio value is
                # itself an Excel formula error in the source (see load_benchmark_index.py) —
                # a fundamentally different reason for missing data than "too few projects."
                status = "benchmark unavailable for this region"
                mean_val = None
            else:
                status = "reliable"
                mean_val = group["vs_levelten_usd_mwh"].mean()

            rows.append({
                "segment_type": segment_col,
                "segment_value": value,
                "n": n,
                "n_with_benchmark": n_with_benchmark,
                "mean_vs_levelten": mean_val,
                "status": status,
            })

    result = pd.DataFrame(rows)
    print(f"\nSegment breakdown (status explains exactly why a segment does or doesn't have "
          f"a reliable mean):")
    print(result.to_string(index=False))

    return result


if __name__ == "__main__":
    df = load_pricing_table()
    plot_price_trend(df)
    segments = recent_vintage_segments(df)
    segments.to_csv(PROCESSED_DIR / "recent_vintage_segments.csv", index=False)
    print(f"\nSaved segment table to data/processed/recent_vintage_segments.csv")

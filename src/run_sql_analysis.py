"""
Runs sql/pricing_segments.sql via DuckDB and cross-checks the result against the pandas
implementation in analyze_pricing.py.

Two independent implementations agreeing is a much stronger correctness signal than one
implementation looking plausible. If they disagree, this says exactly where.

Usage:
    python src/run_sql_analysis.py

Requires:
    pip install duckdb   (already in requirements.txt)
    data/processed/pricing_table.csv from build_pricing_table.py
"""

from pathlib import Path

import duckdb
import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent
SQL_PATH = PROJECT_ROOT / "sql" / "pricing_segments.sql"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

TOLERANCE = 0.01  # $/MWh


def run_sql() -> pd.DataFrame:
    query = SQL_PATH.read_text()
    # DuckDB resolves read_csv_auto paths relative to the process cwd, so make them absolute.
    query = query.replace("data/processed/", f"{PROJECT_ROOT}/data/processed/")
    return duckdb.connect().execute(query).fetchdf()


def compare_with_pandas(sql_df: pd.DataFrame):
    pandas_path = PROCESSED_DIR / "recent_vintage_segments.csv"
    if not pandas_path.exists():
        print(f"No pandas output at {pandas_path} — run src/analyze_pricing.py first to "
              f"enable the cross-check. Showing SQL results only.")
        return

    pandas_df = pd.read_csv(pandas_path)

    merged = sql_df.merge(
        pandas_df,
        on=["segment_type", "segment_value"],
        how="outer",
        suffixes=("_sql", "_pandas"),
        indicator=True,
    )

    only_sql = (merged["_merge"] == "left_only").sum()
    only_pandas = (merged["_merge"] == "right_only").sum()
    if only_sql or only_pandas:
        print(f"Segment mismatch: {only_sql} only in SQL, {only_pandas} only in pandas.")
    else:
        print(f"Segment lists match: {len(merged)} segments in both.")

    both = merged[merged["_merge"] == "both"].copy()

    # Compare the means where both produced one
    have_both = both.dropna(subset=["mean_vs_levelten_sql", "mean_vs_levelten_pandas"])
    if len(have_both):
        diff = (have_both["mean_vs_levelten_sql"] - have_both["mean_vs_levelten_pandas"]).abs()
        max_diff = diff.max()
        print(f"Max absolute difference in mean_vs_levelten: {max_diff:.6f} "
              f"({'PASS' if max_diff < TOLERANCE else 'FAIL'}, tolerance {TOLERANCE}) "
              f"across {len(have_both)} segments with a value in both.")

    status_disagreements = both[both["status_sql"] != both["status_pandas"]]
    if len(status_disagreements):
        print(f"\n{len(status_disagreements)} segments where the STATUS disagrees:")
        print(status_disagreements[["segment_type", "segment_value", "n_sql",
                                     "status_sql", "status_pandas"]].to_string(index=False))
    else:
        print(f"Status classifications agree on all {len(both)} segments.")


if __name__ == "__main__":
    print(f"Running {SQL_PATH.name} via DuckDB...\n")
    sql_df = run_sql()
    print(sql_df.to_string(index=False))
    print("\n--- Cross-check against pandas implementation ---")
    compare_with_pandas(sql_df)

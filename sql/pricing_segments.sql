-- Vintage-matched PPA pricing segmentation, in SQL.
--
-- Reimplements the segment logic from src/analyze_pricing.py so the two can be cross-checked
-- (see src/run_sql_analysis.py). The Python version remains the primary implementation.
--
-- Engine: DuckDB — reads data/processed/pricing_table.csv directly, no server required.
--
-- Two things this query handles deliberately, because getting them wrong would produce
-- confident-looking but misleading output:
--   1. Vintage matching: only 2022-2024 projects are compared against the 2024 benchmark.
--      Comparing older vintages produced a +$194/MWh "finding" that was purely an artifact of
--      an 85% industry-wide price decline over the intervening years. See README.
--   2. Two genuinely different reasons for a missing result, kept separate rather than both
--      collapsing into a blank cell: too few projects in the segment, versus the benchmark
--      itself being unavailable for that region (NYISO's benchmark is an Excel formula error
--      in LBNL's source workbook).

WITH recent AS (
    SELECT *
    FROM read_csv_auto('data/processed/pricing_table.csv')
    WHERE "Solar COD Year" >= 2022
),

by_region AS (
    SELECT
        'Region'                                   AS segment_type,
        "Region"                                   AS segment_value,
        COUNT(*)                                   AS n,
        COUNT(vs_levelten_usd_mwh)                 AS n_with_benchmark,
        AVG(vs_levelten_usd_mwh)                   AS mean_vs_levelten
    FROM recent
    GROUP BY "Region"
),

by_offtaker AS (
    SELECT
        'Offtaker Type'                            AS segment_type,
        "Offtaker Type"                            AS segment_value,
        COUNT(*)                                   AS n,
        COUNT(vs_levelten_usd_mwh)                 AS n_with_benchmark,
        AVG(vs_levelten_usd_mwh)                   AS mean_vs_levelten
    FROM recent
    GROUP BY "Offtaker Type"
),

combined AS (
    SELECT * FROM by_region
    UNION ALL
    SELECT * FROM by_offtaker
)

SELECT
    segment_type,
    segment_value,
    n,
    n_with_benchmark,
    -- Only report a mean where it's actually defensible; otherwise NULL, with the reason
    -- given in the status column rather than left for the reader to guess.
    CASE
        WHEN n >= 5 AND n_with_benchmark >= 5
        THEN ROUND(mean_vs_levelten, 2)
    END AS mean_vs_levelten,
    CASE
        WHEN n < 5                  THEN 'too few projects'
        WHEN n_with_benchmark < 5   THEN 'benchmark unavailable for this region'
        ELSE 'reliable'
    END AS status
FROM combined
ORDER BY segment_type, n DESC;

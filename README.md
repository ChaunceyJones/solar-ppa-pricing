[README.md](https://github.com/user-attachments/files/32712603/README.md)
# Solar PPA Pricing & Discounting Analysis

**One-line hook:**
> Realized 2022–2024 solar PPA prices came in $11–33/MWh below the LevelTen/Trio market index —
> but that gap turned out to be a methodology artifact (a signed deal price compared against a
> developer *offer* index), not evidence these deals were priced better than the market.

## 1. Business context
You're acting as a Pricing Analyst supporting a commercial/deal-pricing team (modeled on real
JDs: analyze deal data and market benchmarks, identify pricing trends and win/loss drivers,
prepare pricing analysis for executive consumption). There's no public "deal pricing" dataset
with real win/loss outcomes, so this project uses a strong public analog: LBNL's utility-scale
solar PPA price database, which has the same shape as a deal-pricing problem — negotiated
prices, by region/technology/vintage, that can be benchmarked and segmented the same way a
pricing desk would benchmark discount depth.

## 2. The data
| Source | What | Frequency | Notes |
|---|---|---|---|
| **LBNL Utility-Scale Solar, 2025 Edition** (`data.openei.org/submissions/8541`) | PPA prices, CapEx, LCOE, capacity factors, by project/region/technology/vintage | Annual, 1,775 projects through 2024 | 59-tab Excel workbook (LBNL's own description says 57; a couple of extra tabs exist beyond that count). Genuinely structured, not prose — CC BY 4.0 licensed. 54.31 MB — not committed to git, downloaded locally instead. |
| **LevelTen & Trio 2024 PPA Index** (same workbook) | Regional market-price benchmark, 7 organized ISO/RTO markets | Annual (2024) | Confirmed directly against LevelTen's own published methodology: this is a **P25 index of developer-submitted offer prices** for projects still seeking a buyer — not realized/signed deal prices. This distinction turned out to be the central finding of the project (see Key Findings #5). |

Schema after cleaning: one row per project (`Individual_Project_Data` tab), joined to the
regional benchmark on `Region`.

**Why this source, confirmed before building anything:** verified the 2025 edition is current
(published Sep 2025, updated Oct 2025), the exact direct-download URL, the file size, and the
license before writing any code. Also, unlike Project 1, verified the benchmark's *actual
methodology* (offer vs. realized price) before trusting a comparison built on it — this is the
lesson carried over from Project 1's dead-API surprise: check what a number actually measures,
not just whether it's numerically available.

## 3. Methodology
- Filtered the 1,775-project master table to `Solar Tech Main == 'PV'` (excludes CSP, 16
  projects) and to rows with a disclosed PPA price (`Levelized PV PPA 2024$/MWh` not null) —
  **only 425 of 1,759 PV projects (24%) disclose a price at all**, a real selection-bias
  constraint on everything downstream, not random missingness.
- Cleaned the benchmark tab: it has a two-row merged header (found by inspecting raw rows
  directly rather than guessing `skiprows`) and several cells containing literal Excel
  formula-error strings (`#N/A`, `#DIV/0!`) that needed explicit conversion to `NaN` rather
  than being left as un-computable strings.
- **First pass, and the mistake worth documenting:** naively joined all 425 disclosed-price
  projects (vintage 2007–2024) against the single 2024 benchmark. This produced apparent
  "overpricing" of +$194/MWh for 2011-vintage projects — traced immediately to comparing
  prices from cost eras 14 years apart across an 80%+ industry-wide price decline, not a real
  pricing signal. Fixed by restricting the benchmark comparison to matching-vintage
  (2022–2024) projects only, and treating the full 2007–2024 range as a separate trend
  analysis instead.
- Segment comparisons (region, offtaker type) explicitly flag any group with fewer than 5
  projects as unreliable rather than reporting a mean built on 2–3 data points, and separately
  flag regions where the benchmark itself is unavailable (see Limitations) rather than
  conflating that with "too few projects."

## 4. Key findings
1. **PPA prices fell dramatically by vintage, tracking LCOE closely.** Median disclosed PPA
   price dropped from ~$200/MWh (2010–2011 vintage) to ~$25–32/MWh (2022–2024 vintage) — an
   ~85% decline that closely tracks the median LCOE decline over the same period (see
   `data/processed/ppa_price_trend.png`). This independently reproduces LBNL's own published
   industry trend, a useful sanity check that this dataset behaves as expected.
2. **Only 24% of PV projects disclose a PPA price** (425 of 1,759). Utility self-build
   projects typically don't have an arm's-length PPA at all, so this dataset describes the
   disclosed-price subset specifically — not the full market — and conclusions should be
   framed that way rather than generalized silently.
3. **A naive same-year benchmark comparison across all vintages produces a misleading result.**
   Comparing 2010–2011-vintage projects against a 2024 benchmark showed apparent overpricing
   exceeding +$190/MWh — an artifact of the vintage gap, not a real pricing finding. This is
   documented as a methodology fix, not hidden as if the corrected analysis were the only one
   ever run.
4. **Even after restricting to matching-vintage (2022–2024) projects, every reliably-sized
   segment priced $11–33/MWh below the LevelTen/Trio benchmark** — CAISO (−$18, n=21), MISO
   (−$14, n=13), PJM (−$29, n=15) by region; Corporate (−$33, n=15), Investor-owned Utility
   (−$11, n=31), Monopoly IOU (−$16, n=10), and Public Utilities (−$23, n=36) by offtaker type.
   The consistency across every single segment — not scattered around zero — is itself the
   signal that something structural, not deal-specific, was driving the gap.
5. **The diagnosis: this is a benchmark-methodology artifact, not a pricing finding.**
   Confirmed directly against LevelTen's own published methodology: their index is built from
   developer-*submitted offer* prices (specifically the P25 — the more aggressive end of the
   offer distribution) for projects still under development and seeking a buyer. LBNL's data
   is the opposite: realized, signed prices for completed, operating projects. An asking price
   and a closing price are structurally different measurements, and a realized price coming in
   below a P25 asking-price index is close to the expected outcome, not evidence of skillful
   negotiation. Corporate offtakers showing the largest gap (−$33) is more likely a *reporting/
   disclosure* pattern than a *negotiation-skill* pattern, though that specific claim isn't
   separately verified here.

## 5. Recommendation
For a real pricing-analyst context, the actionable lesson isn't "which segment prices best" —
the data doesn't support that claim once the benchmark's own methodology is accounted for.
Instead:
- **Don't use a third-party offer/asking-price index as a direct realized-price benchmark
  without adjustment.** If a "did we price this deal well" comparison is genuinely needed,
  request a percentile- and stage-matched comparator (e.g. a paid LevelTen tier with signed-deal
  data, if one exists) or build an internal realized-deal benchmark from same-vintage,
  same-region completed projects instead of a live market index.
- **Always vintage-match two PPA price series before comparing them.** This project only
  avoided publishing a materially wrong headline finding (+$194/MWh "overpricing") because
  vintage was checked explicitly as a diagnostic step rather than trusted on first pass.
- **State the disclosure rate up front in any summary.** With only 24% of projects disclosing
  a price, any finding here describes a specific, likely non-random subset of the market —
  say so explicitly rather than letting a reader assume full market coverage.

## 6. Limitations & assumptions
- CSP plants excluded from the core analysis (16 of 1,775 projects) — PPA structure isn't
  directly comparable to PV.
- 184 of 425 disclosed-price projects (43%) are in regions with no matching third-party
  benchmark at all (`West (non-ISO)`, `Southeast (non-ISO)`, `HI`) — these get a `NaN`
  benchmark comparison rather than being silently dropped, but they contribute nothing to the
  benchmark-comparison findings above.
- **NYISO's own benchmark value is an Excel formula error in LBNL's source workbook**
  (`#N/A` for both LevelTen and Trio) — genuinely unavailable, not a small-sample issue. 12
  NYISO projects had enough sample size to analyze but no benchmark to compare against.
- Segment sample sizes are modest even after restricting to matching-vintage projects (n=5 to
  n=36 for the segments reported) — real numbers, but not large enough to support strong
  causal claims about *why* any particular segment's gap is larger or smaller.
- This is a public-data analog for a deal-pricing problem, not real negotiated deal data with
  actual win/loss outcomes — there's no "lost deal" in this dataset, only completed projects.

## 7. Repo structure
```
solar-ppa-pricing/
├── README.md
├── requirements.txt
├── .gitignore                    # excludes data/raw/*.xlsx (too large to commit)
├── src/
│   ├── download_lbnl_data.py     # downloads the confirmed source file → data/raw/
│   ├── inspect_tabs.py           # lists every tab name + shape, before deciding what to load
│   ├── peek_raw_rows.py          # diagnostic: prints raw rows to find real header locations
│   ├── explore_key_tabs.py       # full column/dtype/sample-row dump of the two key tabs
│   ├── load_benchmark_index.py   # cleans the LevelTen/Trio tab (merged header, Excel errors)
│   ├── build_pricing_table.py    # filters + joins project data against the benchmark
│   └── analyze_pricing.py        # vintage trend chart + recent-vintage segment breakdown
├── data/
│   ├── raw/                      # downloaded workbook (gitignored)
│   └── processed/                # pricing_table.csv, recent_vintage_segments.csv, charts
└── notebooks/
    └── 01_ppa_pricing_analysis.ipynb  # consolidated, reproducible walkthrough of everything above
```

## 8. Build order
1. `python src/download_lbnl_data.py` — pulls the confirmed source file.
2. `python src/inspect_tabs.py` — list all tabs before guessing which to load. **Done.**
3. `python src/peek_raw_rows.py "LevelTen & Trio 2024 PPA Index"` — find the real header
   location for the messy benchmark tab. **Done.**
4. `python src/load_benchmark_index.py` — clean loader for the benchmark. **Done.**
5. `python src/build_pricing_table.py` — join project data to the benchmark, printing filter
   counts and unmatched regions explicitly. **Done.**
6. `python src/analyze_pricing.py` — vintage trend + recent-vintage segment breakdown, with
   thin segments and missing-benchmark regions explicitly flagged rather than silently
   reported. **Done.**
7. `notebooks/01_ppa_pricing_analysis.ipynb` — consolidates steps 2-6 into one reproducible
   walkthrough, including the naive-comparison mistake shown deliberately before its fix, and
   the benchmark-methodology diagnosis as the final section. **Done.**
7. Not yet done: a presentation deck following the same structure as Project 1's.

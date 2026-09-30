# Business Entity Resolution: TantraStack (Amazon ML Challenge 2026)

Rule-based pipeline that matches Source-1 business records to Source-2/3 records
across ~10M rows, using only the Python standard library. It runs in about
8 minutes, with peak memory under 1GB.

## Results

| version | train macro F0.5 | leaderboard |
|---|---|---|
| v1 | 0.4289 | 0.435 |
| v2 | **0.5918** | **0.557** |

Final rank: ~5000 of 89,396 registrations (roughly the top 6% of registrants).

## Approach

1. **Blocking:** normalize names (Unicode-aware, legal suffixes stripped, tokens
   sorted) and key on `country | name tokens`. The index is stored in SQLite,
   so it never sits in RAM.

2. **Bucket cap:** keys shared by more than 2000 records are skipped as too generic.

3. **Match filter:** small buckets (≤10) are lenient, and large buckets are strict.
   When a zip is missing, the filter falls back to address-token overlap.
   All thresholds were grid-searched against ground truth.

Full details, tuning sweeps and the bug log are in [METHODOLOGY.md](METHODOLOGY.md).

## Run it

```bash
python3 code/business_entity_resolution/src/01_build_index.py \
    /path/to/test_source2.tsv /path/to/test_source3.tsv work/index.db

python3 code/business_entity_resolution/src/02_run_matching.py \
    --s1 /path/to/test_source1.tsv \
    --db work/index.db \
    --out-match output/matching_results.tsv \
    --out-cand  output/candidate_pairs.tsv

python3 code/business_entity_resolution/src/04_validate_submission.py \
    --matching output/matching_results.tsv \
    --test-dir /path/to/test
```

Datasets are not included. Full outputs are gitignored (~111MB each), and
`output/sample/` has a 1,000-row preview.

## Limitations and future work

- No trained model. The ML notebook (`05_full_ml_pipeline_colab_OPTIONAL.ipynb`,
  rapidfuzz + HistGradientBoosting) was written but never run to completion,
  so it is untested.

- Cross-script names (Telugu, Devanagari, etc.) can't be matched without
  transliteration.

- Next steps: fuzzy features, a classifier, and transliteration.

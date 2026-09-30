# output/

The full `matching_results.tsv` and `candidate_pairs.tsv` files (~107 MB each,
1,732,544 data rows) are excluded from this repository by `.gitignore` because
they exceed GitHub's 100 MB file-size limit.

## Regenerating the output

Run the pipeline end-to-end against the competition test files
(see the "How to reproduce end-to-end" section in the main README):

```bash
# 1. Build the blocking index from Source-2 + Source-3
python3 src/01_build_index.py /path/to/test_source2.tsv /path/to/test_source3.tsv /work/index.db

# 2. Stream Source-1 against the index, write matching_results.tsv + candidate_pairs.tsv
python3 src/02_run_matching.py \
    --s1 /path/to/test_source1.tsv \
    --db /work/index.db \
    --out-match output/matching_results.tsv \
    --out-cand  output/candidate_pairs.tsv
```

Total runtime on modest hardware: ~7–8 minutes, peak ~730 MB RAM.

## Sample

`output/sample/` contains the first 1,000 data rows (plus header) from each
file, drawn from the same `source1_entity_id` values, so you can inspect
the output format without running the full pipeline.

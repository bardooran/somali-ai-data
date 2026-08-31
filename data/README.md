# Data Layout

This directory is the normalized Somali knowledge layer.

Expected subdirectories:

- `vocabulary/` — lemma/sense/POS/variant records
- `morphology/` — exact forms, classes, features and irregulars
- `grammar/` — sourced construction/rule evidence
- `orthography/` — spelling and normalization evidence
- `regional/` — regional forms and preference metadata
- `terminology/` — domain terminology
- `usage/` — bounded natural-language attestations
- `indexes/` — derived lookup/frequency indexes

## Confidence folders are optional

Do not duplicate identical facts into separate `trusted/`, `supported/`, and `provisional/` copies. Prefer one normalized record carrying its confidence/status fields unless a particular export requires physical separation.

## File formats

Use JSONL for record-oriented review and interchange. Use Parquet for large analytical/index datasets. Every generated large file must have an accompanying manifest/checksum.

Do not place evaluation holdouts in ordinary runtime/training directories.

# Somali AI Data

This repository is the durable, provenance-first knowledge layer for `bardooran/somali-ai`.

It is designed to hold reviewed Somali language knowledge, cross-supported evidence, provisional external candidates, regional variants, grammar/orthography records, natural-usage attestations, indexes, and manifests for large corpus shards.

## Confidence model

- `trusted` — directly reviewed evidence. Recognition is allowed; automatic correction still requires explicit permission.
- `supported` — source-backed or cross-supported evidence. Recognition is allowed; automatic correction is off by default.
- `provisional` — external candidate/attestation. Cautious retrieval may be allowed; it never proves correctness.

## Repository roles

- `data/` — normalized knowledge records.
- `schemas/` — machine-readable record/source contracts.
- `manifests/` — source, license, import, and future large-shard metadata.
- `tools/` — validators and reproducible import/sync tools.
- `docs/` — data policy and architecture.

`data/qa` and benchmark/holdout material from the runtime repository are intentionally not synced into ordinary retrieval/training data. Large corpora should live in compressed dataset/object-storage shards, with manifests and hashes committed here rather than millions of Git objects.

The first automated imports include GiellaLT morphology/grammar candidates and SLS rule candidates. A separate reviewed-data sync brings project-reviewed vocabulary and morphology from `bardooran/somali-ai` while preserving original status, provenance, region, and correction-safety boundaries.

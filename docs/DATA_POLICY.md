# Data Policy

## Purpose

`somali-ai-data` is the durable knowledge layer for Somali AI. It may contain millions of normalized records over time, but every record must remain traceable and safe to use.

## Confidence and use

| Tier | Meaning | Recognition | Automatic correction |
|---|---|---:|---:|
| `trusted` | Directly reviewed evidence | yes | only when explicitly allowed |
| `supported` | Cross-supported by independent evidence | yes | no by default |
| `provisional` | Source-backed candidate or attestation | cautious yes | never |

Confidence is not inferred from record count alone. Two records derived from the same underlying publication do not count as two independent sources.

## Required provenance

A stored record must identify enough information to recover or audit its origin. Use source IDs from `manifests/sources.json` and preserve, where available:

- upstream repository/dataset/publication
- pinned commit, dataset snapshot, edition or publication identifier
- source path, row, page or other locator
- content hash for extracted text/data
- evidence role
- license or rights status

## Licensing

Never assume one repository-wide license covers every embedded dataset or source file. Respect per-file and upstream rights. If redistribution rights are unresolved, store metadata, hashes, pointers and derived facts only when legally appropriate; do not bulk-copy restricted source text.

## Corpus policy

Large corpora should not be committed as millions of small Git objects or giant unbounded JSONL files. Use compressed Parquet/JSONL shards in dataset/object storage. Commit manifests, checksums, schemas and reproducible processing metadata here.

Corpus occurrence is evidence of **attestation/use**, not proof that a form is grammatical, preferred, standard or suitable for correction.

## Regional policy

Do not erase regional Somali. Records may carry one or more region/profile labels. A documented regional form is not automatically an error because another region prefers a different form.

## Morphology policy

- Never invent forms.
- Never infer a full paradigm from one observed example.
- Keep lemma facts, inflection facts and sentence-context facts separable.
- Ambiguous surfaces may have multiple analyses.
- Unsupported forms stay unknown/unjudged.

## Evaluation isolation

Benchmark and holdout sets used to measure generalization must not be fed back into ordinary retrieval, promotion or training simply to raise benchmark scores. Evaluation-only material should remain isolated and explicitly marked.

## Deduplication

Deduplicate by normalized identity appropriate to the record type, but never discard distinct provenance. If several sources support the same lexical fact, retain the evidence links rather than cloning the same knowledge record repeatedly.

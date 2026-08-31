# Somali AI Data

Long-term Somali language knowledge store for [`bardooran/somali-ai`](https://github.com/bardooran/somali-ai).

This repository is for **structured, provenance-aware Somali data**. It is not a place to blindly copy every upstream file. The goal is to preserve useful breadth from public/open sources while making source, confidence, region, licensing, and review status explicit.

## Core rule

**Recognition is not the same as correctness authority.**

A source-backed word may be recognized before it is trusted for automatic correction. Records are separated into three operational confidence tiers:

1. `trusted` — directly reviewed evidence; may support correction when the record explicitly allows it.
2. `supported` — cross-supported by independent evidence; may support recognition/analysis, but is not automatically correction authority.
3. `provisional` — useful source-backed candidate; may support cautious recognition, never automatic correctness claims.

## Repository roles

- `somali-ai` — code, analyzers, assistant, rules, tests, evaluation and product runtime.
- `somali-ai-data` — normalized vocabulary, morphology, grammar evidence, regional information, terminology, usage metadata, indexes and source manifests.
- Large corpus/training storage — compressed dataset shards outside ordinary Git when data volume becomes large; this repo stores manifests, hashes, source/license metadata and reproducible build instructions.

## Planned data areas

- `data/vocabulary/`
- `data/morphology/`
- `data/grammar/`
- `data/orthography/`
- `data/regional/`
- `data/terminology/`
- `data/usage/`
- `data/indexes/`
- `manifests/`
- `schemas/`
- `docs/`

## Non-negotiable rules

- Preserve provenance and source version/snapshot.
- Preserve per-source/per-file licensing requirements.
- Do not convert occurrence in a corpus into proof of grammatical correctness.
- Do not promote external candidates automatically.
- Do not guess Somali paradigms from a single form.
- Keep regional variation explicit instead of normalizing it away.
- Keep evaluation holdouts isolated from training/retrieval inputs.
- Unknown is preferable to fabricated certainty.

See `docs/DATA_POLICY.md` and `docs/ARCHITECTURE.md` before adding bulk data.

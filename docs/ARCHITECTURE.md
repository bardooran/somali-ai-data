# Architecture

## Data flow

```text
upstream source / publication / corpus
              ↓
        source manifest
              ↓
      normalized records
              ↓
  ┌───────────┼───────────┐
  ↓           ↓           ↓
trusted    supported   provisional
  ↓           ↓           ↓
correction  recognition  cautious recognition
 authority   + analysis   / evidence lookup
              ↓
         bardooran/somali-ai
```

## Separation of responsibilities

`somali-ai-data` stores knowledge and evidence. `somali-ai` decides how that knowledge is used in an analyzer, checker, retrieval system or assistant.

The data repository should therefore avoid executable product logic when a declarative record can express the same fact.

## Record families

- **Vocabulary** — lemmas, senses, POS, variants and lexical metadata.
- **Morphology** — exact forms, paradigms, classes, features, irregulars and ambiguity.
- **Grammar** — sourced constructions and rule evidence; executable grammar remains in `somali-ai`.
- **Orthography** — spelling/normalization evidence and documented variants.
- **Regional** — geographical/profile preferences and documented alternatives.
- **Terminology** — domain terms and source-backed equivalents.
- **Usage** — bounded natural-language attestations and corpus metadata. Usage never automatically proves correctness.
- **Indexes** — derived lookup/frequency tables with reproducible build provenance.

## Scale strategy

Ordinary Git is for reviewed/structured data, schemas, manifests and bounded shards. Large natural-language corpora and training datasets should live in dataset/object storage, for example compressed Parquet shards. This repository stores their immutable manifests, hashes and provenance.

## Runtime export

Future build tooling should produce explicit exports such as:

- `trusted-runtime` — only trusted records allowed by policy.
- `recognition-runtime` — trusted + supported + eligible provisional recognition records.
- `training-clean` — license-compatible, quality-filtered material excluding evaluation holdouts.
- `evidence-index` — source/provenance lookup for assistant retrieval.

No export should silently upgrade a record's confidence tier.

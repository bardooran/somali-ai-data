#!/usr/bin/env python3
"""Normalize candidate inventories from bardooran/somali-ai into somali-ai-data.

This is a one-way evidence sync. It never promotes candidates, never infers
correctness, and preserves the upstream linguistic source provenance carried by
the source records.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Iterable

SOURCE_REPOSITORY = "bardooran/somali-ai"

INPUTS = {
    "giellalt_lexical": Path("data/imported/giellalt/lexical_candidates.jsonl"),
    "giellalt_grammar": Path("data/imported/giellalt/grammar_candidates.jsonl"),
    "sls_rules": Path("data/imported/sls/rule_candidates.jsonl"),
}

OUTPUTS = {
    "giellalt_lexical": Path("data/morphology/provisional/giellalt.jsonl"),
    "giellalt_grammar": Path("data/grammar/provisional/giellalt_function_words.jsonl"),
    "sls_rules": Path("data/grammar/provisional/sls_rules.jsonl"),
}


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_hash(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _sha256_bytes(encoded)


def _read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            value = json.loads(text)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_no}: row must be a JSON object")
            rows.append(value)
    return rows


def _source_ref(row: dict, *, source_id: str, evidence_role: str) -> dict:
    source_path = str(row.get("source_path", "")).strip()
    source_line = row.get("source_line")
    if not source_path:
        raise ValueError("candidate record is missing source_path")
    if source_line is None:
        raise ValueError("candidate record is missing source_line")
    source_commit = str(row.get("source_commit", "")).strip()
    if not source_commit:
        raise ValueError("candidate record is missing source_commit")
    locator = f"{source_path}:{source_line}"
    return {
        "source_id": source_id,
        "evidence_role": evidence_role,
        "locator": locator,
        "source_version": source_commit,
        "license": row.get("source_license"),
        "content_hash": _canonical_hash(row),
    }


def _record_id(prefix: str, source: dict, semantic: object) -> str:
    digest = _canonical_hash({"source": source, "semantic": semantic})[:24]
    return f"{prefix}:{digest}"


def _base_record(*, record_id: str, record_type: str, surface: str | None, lemma: str | None, features: dict, source: dict, ingest_commit: str, ingest_file: str) -> dict:
    return {
        "record_id": record_id,
        "record_type": record_type,
        "surface": surface,
        "lemma": lemma,
        "sense_id": None,
        "features": features,
        "confidence_tier": "provisional",
        "status": "provisional",
        "regions": [],
        "sources": [source],
        "promotion_allowed": False,
        "correctness_inference_allowed": False,
        "retrieval_allowed": True,
        "training_allowed": False,
        "ingest": {
            "repository": SOURCE_REPOSITORY,
            "repository_commit": ingest_commit,
            "source_file": ingest_file,
        },
    }


def normalize_giellalt_lexical(rows: Iterable[dict], *, ingest_commit: str, ingest_file: str) -> list[dict]:
    records: list[dict] = []
    for row in rows:
        lemma = str(row.get("lemma", "")).strip()
        part_of_speech = str(row.get("record_type", "")).strip()
        if not lemma or part_of_speech not in {"noun", "verb", "adjective", "numeral"}:
            raise ValueError("invalid GiellaLT lexical candidate")
        source = _source_ref(row, source_id="giellalt-somali", evidence_role="external_morphology_candidate")
        features = {
            "part_of_speech": part_of_speech,
            "continuation": row.get("continuation"),
            "raw_lexical_token": row.get("raw_lexical_token"),
            "source_candidate_status": row.get("status"),
        }
        record_id = _record_id("giellalt-morph", source, {"lemma": lemma, "features": features})
        records.append(
            _base_record(
                record_id=record_id,
                record_type="morphology",
                surface=lemma,
                lemma=lemma,
                features=features,
                source=source,
                ingest_commit=ingest_commit,
                ingest_file=ingest_file,
            )
        )
    return records


def normalize_giellalt_grammar(rows: Iterable[dict], *, ingest_commit: str, ingest_file: str) -> list[dict]:
    records: list[dict] = []
    for row in rows:
        lemma = str(row.get("lemma", "")).strip()
        candidate_type = str(row.get("record_type", "")).strip()
        if not lemma or candidate_type not in {"pronoun", "function_particle", "adposition"}:
            raise ValueError("invalid GiellaLT grammar candidate")
        source = _source_ref(row, source_id="giellalt-somali", evidence_role="external_grammar_lexeme_candidate")
        features = {
            "part_of_speech": candidate_type,
            "surface_pattern": row.get("surface_pattern"),
            "continuation": row.get("continuation"),
            "raw_lexical_token": row.get("raw_lexical_token"),
            "gloss": row.get("gloss"),
            "usage_requires_review": bool(row.get("usage_requires_review", True)),
            "source_candidate_status": row.get("status"),
        }
        record_id = _record_id("giellalt-grammar", source, {"lemma": lemma, "features": features})
        records.append(
            _base_record(
                record_id=record_id,
                record_type="grammar",
                surface=lemma,
                lemma=lemma,
                features=features,
                source=source,
                ingest_commit=ingest_commit,
                ingest_file=ingest_file,
            )
        )
    return records


def normalize_sls_rules(rows: Iterable[dict], *, ingest_commit: str, ingest_file: str) -> list[dict]:
    records: list[dict] = []
    for row in rows:
        rule_id = str(row.get("rule_id", "")).strip()
        statement = str(row.get("statement", "")).strip()
        source_path = str(row.get("source_path", ""))
        if not rule_id or not statement:
            raise ValueError("invalid SLS rule candidate")
        source = _source_ref(row, source_id="sls-goobolabs", evidence_role="external_structured_rule_candidate")
        record_type = "orthography" if "/orthography/" in source_path else "grammar"
        features = {
            "rule_id": rule_id,
            "statement": statement,
            "document_id": row.get("document_id"),
            "sls_id": row.get("sls_id"),
            "lifecycle_status": row.get("lifecycle_status"),
            "version": row.get("version"),
            "source_lineage_note": row.get("source_lineage_note"),
            "source_candidate_status": row.get("status"),
        }
        record_id = _record_id("sls-rule", source, {"rule_id": rule_id, "statement": statement})
        records.append(
            _base_record(
                record_id=record_id,
                record_type=record_type,
                surface=None,
                lemma=None,
                features=features,
                source=source,
                ingest_commit=ingest_commit,
                ingest_file=ingest_file,
            )
        )
    return records


def _write_jsonl(records: Iterable[dict], path: Path) -> tuple[int, str]:
    ordered = sorted(records, key=lambda row: row["record_id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in ordered)
    path.write_text(payload, encoding="utf-8")
    return len(ordered), _sha256_bytes(payload.encode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize somali-ai candidate inventories into somali-ai-data")
    parser.add_argument("source_root", type=Path, help="Checkout of bardooran/somali-ai")
    parser.add_argument("--source-commit", required=True, help="Exact somali-ai commit used for the sync")
    parser.add_argument("--output-root", type=Path, default=Path("."))
    args = parser.parse_args()

    source_root = args.source_root.resolve()
    output_root = args.output_root.resolve()
    source_files = {name: source_root / path for name, path in INPUTS.items()}
    for path in source_files.values():
        if not path.is_file():
            raise FileNotFoundError(path)

    raw = {name: _read_jsonl(path) for name, path in source_files.items()}
    normalized = {
        "giellalt_lexical": normalize_giellalt_lexical(raw["giellalt_lexical"], ingest_commit=args.source_commit, ingest_file=str(INPUTS["giellalt_lexical"])),
        "giellalt_grammar": normalize_giellalt_grammar(raw["giellalt_grammar"], ingest_commit=args.source_commit, ingest_file=str(INPUTS["giellalt_grammar"])),
        "sls_rules": normalize_sls_rules(raw["sls_rules"], ingest_commit=args.source_commit, ingest_file=str(INPUTS["sls_rules"])),
    }

    generated: dict[str, dict] = {}
    for name, records in normalized.items():
        output = output_root / OUTPUTS[name]
        count, digest = _write_jsonl(records, output)
        generated[name] = {
            "input": str(INPUTS[name]),
            "input_sha256": _sha256_bytes(source_files[name].read_bytes()),
            "output": str(OUTPUTS[name]),
            "output_sha256": digest,
            "record_count": count,
        }

    manifest = {
        "ingest_repository": SOURCE_REPOSITORY,
        "ingest_repository_commit": args.source_commit,
        "confidence_tier": "provisional",
        "promotion_allowed": False,
        "correctness_inference_allowed": False,
        "generated": generated,
    }
    manifest_path = output_root / "manifests" / "imports" / "somali-ai-sync.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    counts = {name: details["record_count"] for name, details in generated.items()}
    print(json.dumps({"source_commit": args.source_commit, "counts": counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

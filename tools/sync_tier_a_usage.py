#!/usr/bin/env python3
"""Sync bounded Tier-A natural Somali usage from bardooran/somali-ai.

These records are attestation evidence only. They are useful for retrieval,
frequency, style research, and future corpus assembly, but occurrence in a
corpus never proves grammatical correctness and never grants training rights.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Iterable

SOURCE_REPOSITORY = "bardooran/somali-ai"
INPUTS = (
    Path("data/usage/external/wikipedia_usage_candidates.jsonl"),
    Path("data/usage/external/xlsum_usage_candidates.jsonl"),
)
OUTPUT = Path("data/usage/provisional/tier_a_natural_usage.jsonl")
MANIFEST = Path("manifests/imports/somali-ai-tier-a-usage.json")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_hash(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return _sha256_bytes(payload.encode("utf-8"))


def _read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            row = json.loads(text)
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_no}: expected JSON object")
            rows.append(row)
    return rows


def normalize(rows: Iterable[dict], *, ingest_commit: str, ingest_file: str) -> list[dict]:
    result: list[dict] = []
    for row in rows:
        text = str(row.get("text", "")).strip()
        usage_id = str(row.get("usage_id", "")).strip()
        dataset = str(row.get("dataset", "")).strip()
        dataset_config = str(row.get("dataset_config", "")).strip()
        source_commit = str(row.get("source_commit", "")).strip()
        source_row = row.get("source_row")
        license_name = str(row.get("source_license", "")).strip()
        if not all((text, usage_id, dataset, source_commit, license_name)) or source_row is None:
            raise ValueError("Tier-A row is missing required provenance")
        if row.get("evidence_tier") != "A":
            raise ValueError("only Tier-A usage may enter this bounded sync")
        if row.get("promotion_allowed") is not False or row.get("correctness_inference_allowed") is not False:
            raise ValueError("natural usage must not carry correctness authority")

        content_hash = str(row.get("content_hash", "")).strip() or f"sha256:{_canonical_hash(text)}"
        source = {
            "source_id": "somnlp-corpus",
            "evidence_role": str(row.get("evidence_role") or "natural_usage_attestation"),
            "locator": f"{dataset}[{dataset_config}] row {source_row}",
            "source_version": source_commit,
            "license": license_name,
            "content_hash": content_hash,
        }
        identity = {
            "usage_id": usage_id,
            "dataset": dataset,
            "dataset_config": dataset_config,
            "source_commit": source_commit,
            "source_row": source_row,
            "content_hash": content_hash,
        }
        result.append(
            {
                "record_id": f"tier-a-usage:{_canonical_hash(identity)[:24]}",
                "record_type": "usage",
                "surface": None,
                "lemma": None,
                "sense_id": None,
                "features": {
                    "text": text,
                    "usage_id": usage_id,
                    "dataset": dataset,
                    "dataset_config": dataset_config,
                    "dataset_url": row.get("dataset_url"),
                    "provenance_precision": row.get("provenance_precision"),
                    "source_project": row.get("source_project"),
                    "source_repository": row.get("source_repository"),
                    "source_row": source_row,
                    "source_status": row.get("status"),
                    "evidence_tier": "A",
                },
                "confidence_tier": "provisional",
                "status": "provisional",
                "regions": [],
                "sources": [source],
                "promotion_allowed": False,
                "correctness_inference_allowed": False,
                "retrieval_allowed": True,
                "training_allowed": False,
                "notes": "Natural occurrence is attestation evidence, not automatic grammatical correctness or training permission.",
                "ingest": {
                    "repository": SOURCE_REPOSITORY,
                    "repository_commit": ingest_commit,
                    "source_file": ingest_file,
                },
            }
        )
    return result


def _write_jsonl(records: Iterable[dict], path: Path) -> tuple[int, str]:
    ordered = sorted(records, key=lambda row: row["record_id"])
    payload = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in ordered)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")
    return len(ordered), _sha256_bytes(payload.encode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_root", type=Path)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--output-root", type=Path, default=Path("."))
    args = parser.parse_args()

    source_root = args.source_root.resolve()
    output_root = args.output_root.resolve()
    records: list[dict] = []
    inputs: list[dict] = []
    for relative in INPUTS:
        path = source_root / relative
        if not path.is_file():
            raise FileNotFoundError(path)
        raw = _read_jsonl(path)
        records.extend(normalize(raw, ingest_commit=args.source_commit, ingest_file=str(relative)))
        inputs.append({
            "path": str(relative),
            "record_count": len(raw),
            "sha256": _sha256_bytes(path.read_bytes()),
        })

    count, output_hash = _write_jsonl(records, output_root / OUTPUT)
    source_versions = sorted({record["sources"][0]["source_version"] for record in records})
    licenses = sorted({record["sources"][0]["license"] for record in records})
    manifest = {
        "ingest_repository": SOURCE_REPOSITORY,
        "ingest_repository_commit": args.source_commit,
        "record_count": count,
        "output": str(OUTPUT),
        "output_sha256": output_hash,
        "inputs": inputs,
        "source_versions": source_versions,
        "licenses": licenses,
        "confidence_tier": "provisional",
        "promotion_allowed": False,
        "correctness_inference_allowed": False,
        "training_allowed": False,
        "evaluation_data_included": False,
    }
    manifest_path = output_root / MANIFEST
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

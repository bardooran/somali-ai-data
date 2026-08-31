#!/usr/bin/env python3
"""Lightweight repository integrity checks for Somali AI Data.

The validator intentionally uses only the Python standard library so CI can run
without network package installation. JSON Schema files document the full data
contract; this script enforces the highest-risk invariants on every commit.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data"
SOURCES_PATH = ROOT / "manifests" / "sources.json"
MAX_GIT_FILE_BYTES = 25 * 1024 * 1024
REQUIRED_RECORD_KEYS = {
    "record_id",
    "record_type",
    "confidence_tier",
    "status",
    "sources",
    "promotion_allowed",
    "correctness_inference_allowed",
}
CONFIDENCE_TIERS = {"trusted", "supported", "provisional"}


def load_sources() -> set[str]:
    payload = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    sources = payload.get("sources")
    if not isinstance(sources, list) or not sources:
        raise AssertionError("manifests/sources.json must contain a non-empty sources list")
    ids: list[str] = []
    for row in sources:
        if not isinstance(row, dict):
            raise AssertionError("source manifest rows must be objects")
        source_id = row.get("source_id")
        if not isinstance(source_id, str) or not source_id:
            raise AssertionError("every source needs source_id")
        ids.append(source_id)
    if len(ids) != len(set(ids)):
        raise AssertionError("source_id values must be unique")
    return set(ids)


def validate_record(record: dict, *, source_ids: set[str], path: Path, line_no: int) -> None:
    missing = REQUIRED_RECORD_KEYS - record.keys()
    if missing:
        raise AssertionError(f"{path}:{line_no}: missing keys {sorted(missing)}")
    if record["confidence_tier"] not in CONFIDENCE_TIERS:
        raise AssertionError(f"{path}:{line_no}: invalid confidence_tier")
    sources = record["sources"]
    if not isinstance(sources, list) or not sources:
        raise AssertionError(f"{path}:{line_no}: sources must be non-empty")
    for source in sources:
        if not isinstance(source, dict) or source.get("source_id") not in source_ids:
            raise AssertionError(f"{path}:{line_no}: unknown or invalid source_id")
    if record["confidence_tier"] == "provisional":
        if record["promotion_allowed"]:
            raise AssertionError(f"{path}:{line_no}: provisional record cannot auto-promote")
        if record["correctness_inference_allowed"]:
            raise AssertionError(f"{path}:{line_no}: provisional record cannot prove correctness")


def validate_jsonl(source_ids: set[str]) -> int:
    if not DATA_ROOT.exists():
        return 0
    count = 0
    for path in sorted(DATA_ROOT.rglob("*.jsonl")):
        with path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                text = line.strip()
                if not text:
                    continue
                record = json.loads(text)
                if not isinstance(record, dict):
                    raise AssertionError(f"{path}:{line_no}: row must be a JSON object")
                validate_record(record, source_ids=source_ids, path=path, line_no=line_no)
                count += 1
    return count


def validate_git_file_sizes() -> None:
    ignored_roots = {".git"}
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in ignored_roots for part in path.parts):
            continue
        if path.stat().st_size > MAX_GIT_FILE_BYTES:
            raise AssertionError(
                f"{path.relative_to(ROOT)} exceeds 25 MiB; store large shards outside ordinary Git and commit a manifest/hash instead"
            )


def main() -> int:
    source_ids = load_sources()
    record_count = validate_jsonl(source_ids)
    validate_git_file_sizes()
    print(f"validated {len(source_ids)} source manifests and {record_count} JSONL knowledge records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

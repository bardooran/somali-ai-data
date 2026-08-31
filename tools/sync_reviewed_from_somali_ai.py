#!/usr/bin/env python3
"""Normalize reviewed Somali AI vocabulary and morphology into somali-ai-data.

The sync deliberately excludes data/qa and every benchmark/holdout file. It
preserves the source record, maps project review status into the master-store
confidence model, and never grants automatic correction authority merely
because a record is stored here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Iterable, Iterator

SOURCE_REPOSITORY = "bardooran/somali-ai"
SOURCE_ID = "somali-ai-reviewed"
MORPHOLOGY_ROOT = Path("data/morphology")
VOCABULARY_ROOT = Path("data/vocabulary")
MORPHOLOGY_OUTPUT = Path("data/morphology/reviewed/somali_ai_reviewed.jsonl")
VOCABULARY_OUTPUT = Path("data/vocabulary/reviewed/somali_ai_reviewed.jsonl")
MANIFEST_OUTPUT = Path("manifests/imports/somali-ai-reviewed-sync.json")
LEXICAL_KEYS = ("surface", "form", "canonical", "preferred_written", "lemma", "term", "word")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_hash(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return _sha256_bytes(payload.encode("utf-8"))


def _record_id(prefix: str, payload: object) -> str:
    return f"{prefix}:{_canonical_hash(payload)[:24]}"


def _read_jsonl(path: Path) -> Iterator[tuple[dict, str]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            value = json.loads(text)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_no}: expected a JSON object")
            yield value, str(line_no)


def _walk_lexical_dicts(value: object, trail: tuple[str, ...] = ()) -> Iterator[tuple[dict, str]]:
    if isinstance(value, dict):
        if any(key in value and isinstance(value.get(key), str) and value.get(key).strip() for key in LEXICAL_KEYS):
            yield value, "/".join(trail) or "$"
        for key, child in value.items():
            if isinstance(child, (dict, list)):
                yield from _walk_lexical_dicts(child, (*trail, str(key)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            if isinstance(child, (dict, list)):
                yield from _walk_lexical_dicts(child, (*trail, str(index)))


def _status_mapping(status_hint: str, *, locator_hint: str, reviewed_file: bool, executable: bool) -> tuple[str, str, bool, bool, bool]:
    text = f"{status_hint} {locator_hint}".casefold()
    if any(marker in text for marker in ("submitted_but_not", "not_promoted", "rejected")):
        return "provisional", "rejected", False, False, False
    if any(marker in text for marker in ("provisional", "candidate", "unreviewed")):
        return "provisional", "provisional", False, False, True
    if any(marker in text for marker in ("context_required", "context-dependent", "context_dependent", "ambiguous", "usage_sensitive")):
        return "supported", "context_required", False, False, True
    if any(marker in text for marker in ("regional", "jigjiga", "hargeisa", "mogadishu", "southern")):
        return "supported", "regional_variant", False, False, True
    if text.strip() and ("source_backed" in text or "supported" in text):
        return "supported", "reviewed", False, False, True
    if text.strip() and ("native_reviewed" in text or "reviewed" in text):
        return "trusted", "reviewed", True, executable, True
    if reviewed_file:
        return "trusted", "reviewed", True, executable, True
    return "supported", "reviewed", False, False, True


def _regions(row: dict) -> list[str]:
    candidates: list[str] = []
    for key in ("region", "regions", "regional_profile", "project_profile"):
        value = row.get(key)
        if value is not None:
            candidates.append(json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value)
    features = row.get("features")
    if isinstance(features, dict):
        for key in ("region", "regions", "regional_profile"):
            value = features.get(key)
            if value is not None:
                candidates.append(json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value)
    text = " ".join(candidates).casefold()
    result: list[str] = []
    for needle, label in (
        ("jigjiga", "Jigjiga"),
        ("hargeisa", "Hargeisa"),
        ("mogadishu", "Mogadishu"),
        ("southern", "Southern Somali"),
    ):
        if needle in text:
            result.append(label)
    return result


def _source_ref(row: dict, *, relative_path: Path, locator: str, ingest_commit: str, role: str) -> dict:
    return {
        "source_id": SOURCE_ID,
        "evidence_role": role,
        "locator": f"{relative_path}:{locator}",
        "source_version": ingest_commit,
        "license": None,
        "content_hash": _canonical_hash(row),
    }


def _make_record(
    *,
    row: dict,
    relative_path: Path,
    locator: str,
    ingest_commit: str,
    record_type: str,
    surface: str | None,
    lemma: str | None,
    variant_of: str | None = None,
) -> dict:
    status_hint = str(row.get("status", ""))
    executable = bool(row.get("executable", False))
    confidence, status, promotion, correctness, retrieval = _status_mapping(
        status_hint,
        locator_hint=locator,
        reviewed_file=("reviewed" in relative_path.name or "native_review" in relative_path.name),
        executable=executable,
    )
    role = "reviewed_morphology_record" if record_type == "morphology" else "reviewed_vocabulary_record"
    source = _source_ref(
        row,
        relative_path=relative_path,
        locator=locator,
        ingest_commit=ingest_commit,
        role=role,
    )
    features = {
        "original_record_id": row.get("id"),
        "original_status": row.get("status"),
        "analysis_type": row.get("analysis_type"),
        "segmentation": row.get("segmentation"),
        "evidence_type": row.get("evidence_type"),
        "original_source": row.get("source"),
        "source_path": row.get("source_path"),
        "source_family": row.get("source_family"),
        "executable_in_source_repo": executable,
        "source_features": row.get("features", {}),
    }
    if variant_of is not None:
        features["variant_of"] = variant_of
    # Preserve the remaining authored fact fields without turning them into
    # top-level authority in the master schema.
    preserved = {
        key: value
        for key, value in row.items()
        if key not in {"features", "source"} and key not in LEXICAL_KEYS
    }
    if preserved:
        features["source_record_fields"] = preserved

    record_identity = {
        "path": str(relative_path),
        "locator": locator,
        "surface": surface,
        "lemma": lemma,
        "variant_of": variant_of,
        "source_record_id": row.get("id"),
    }
    return {
        "record_id": _record_id("somali-ai-reviewed", record_identity),
        "record_type": record_type,
        "surface": surface,
        "lemma": lemma,
        "sense_id": str(row.get("homograph_index")) if row.get("homograph_index") is not None else None,
        "features": features,
        "confidence_tier": confidence,
        "status": status,
        "regions": _regions(row),
        "sources": [source],
        "promotion_allowed": promotion,
        "correctness_inference_allowed": correctness,
        "retrieval_allowed": retrieval,
        "training_allowed": False,
        "notes": row.get("note") or row.get("execution_note"),
        "ingest": {
            "repository": SOURCE_REPOSITORY,
            "repository_commit": ingest_commit,
            "source_file": str(relative_path),
        },
    }


def normalize_morphology(source_root: Path, *, ingest_commit: str) -> tuple[list[dict], list[str]]:
    records: list[dict] = []
    files: list[str] = []
    root = source_root / MORPHOLOGY_ROOT
    for path in sorted(root.glob("*.jsonl")):
        relative = path.relative_to(source_root)
        files.append(str(relative))
        for row, locator in _read_jsonl(path):
            surface = str(row.get("surface") or row.get("form") or row.get("lemma") or "").strip() or None
            lemma = str(row.get("lemma") or surface or "").strip() or None
            if surface is None and lemma is None:
                continue
            records.append(
                _make_record(
                    row=row,
                    relative_path=relative,
                    locator=locator,
                    ingest_commit=ingest_commit,
                    record_type="morphology",
                    surface=surface,
                    lemma=lemma,
                )
            )
    return records, files


def _primary_surface(row: dict) -> str | None:
    for key in LEXICAL_KEYS:
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def normalize_vocabulary(source_root: Path, *, ingest_commit: str) -> tuple[list[dict], list[str]]:
    records: list[dict] = []
    files: list[str] = []
    root = source_root / VOCABULARY_ROOT
    for path in sorted(root.iterdir()):
        if not path.is_file() or path.name == "README.md" or path.suffix not in {".json", ".jsonl"}:
            continue
        relative = path.relative_to(source_root)
        files.append(str(relative))
        if path.suffix == ".jsonl":
            rows = list(_read_jsonl(path))
        else:
            payload = json.loads(path.read_text(encoding="utf-8"))
            rows = list(_walk_lexical_dicts(payload))
        for row, locator in rows:
            primary = _primary_surface(row)
            if primary is None:
                continue
            lemma_value = row.get("lemma") or row.get("canonical") or row.get("form") or row.get("surface") or primary
            lemma = str(lemma_value).strip() or primary
            records.append(
                _make_record(
                    row=row,
                    relative_path=relative,
                    locator=locator,
                    ingest_commit=ingest_commit,
                    record_type="vocabulary",
                    surface=primary,
                    lemma=lemma,
                )
            )
            variants = row.get("variants")
            if isinstance(variants, list):
                for index, variant in enumerate(variants):
                    if not isinstance(variant, str) or not variant.strip() or variant.strip().casefold() == primary.casefold():
                        continue
                    records.append(
                        _make_record(
                            row=row,
                            relative_path=relative,
                            locator=f"{locator}/variants/{index}",
                            ingest_commit=ingest_commit,
                            record_type="vocabulary",
                            surface=variant.strip(),
                            lemma=lemma,
                            variant_of=primary,
                        )
                    )
    return records, files


def _write_jsonl(records: Iterable[dict], path: Path) -> tuple[int, str]:
    ordered = sorted(records, key=lambda row: row["record_id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in ordered)
    path.write_text(payload, encoding="utf-8")
    return len(ordered), _sha256_bytes(payload.encode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync reviewed Somali AI language data")
    parser.add_argument("source_root", type=Path)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--output-root", type=Path, default=Path("."))
    args = parser.parse_args()

    source_root = args.source_root.resolve()
    output_root = args.output_root.resolve()
    if not (source_root / MORPHOLOGY_ROOT).is_dir() or not (source_root / VOCABULARY_ROOT).is_dir():
        raise FileNotFoundError("Somali AI reviewed data directories are missing")

    morphology, morphology_files = normalize_morphology(source_root, ingest_commit=args.source_commit)
    vocabulary, vocabulary_files = normalize_vocabulary(source_root, ingest_commit=args.source_commit)
    morph_count, morph_hash = _write_jsonl(morphology, output_root / MORPHOLOGY_OUTPUT)
    vocab_count, vocab_hash = _write_jsonl(vocabulary, output_root / VOCABULARY_OUTPUT)

    manifest = {
        "ingest_repository": SOURCE_REPOSITORY,
        "ingest_repository_commit": args.source_commit,
        "evaluation_data_included": False,
        "qa_paths_included": False,
        "training_allowed": False,
        "generated": {
            "reviewed_morphology": {
                "output": str(MORPHOLOGY_OUTPUT),
                "output_sha256": morph_hash,
                "record_count": morph_count,
                "source_files": morphology_files,
            },
            "reviewed_vocabulary": {
                "output": str(VOCABULARY_OUTPUT),
                "output_sha256": vocab_hash,
                "record_count": vocab_count,
                "source_files": vocabulary_files,
            },
        },
    }
    manifest_path = output_root / MANIFEST_OUTPUT
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"morphology": morph_count, "vocabulary": vocab_count, "source_commit": args.source_commit}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

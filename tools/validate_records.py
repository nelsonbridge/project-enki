from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

RECORD_DIRECTORIES = (
    "raw-evidence",
    "metadata",
    "observations",
    "hypotheses",
    "baselines",
    "experiments",
    "results",
    "analysis",
)

SCHEMA_BY_RECORD_TYPE = {
    "evidence": "evidence.schema.json",
    "observation": "observation.schema.json",
    "hypothesis": "hypothesis.schema.json",
    "experiment": "experiment.schema.json",
    "result": "result.schema.json",
    "analysis": "analysis.schema.json",
    "subject": "subject.schema.json",
    "provenance": "provenance.schema.json",
}

CHECKS = {"schemas", "duplicates", "references", "mutations"}


@dataclass(frozen=True)
class Record:
    file_path: Path
    record_type: str
    record_id: str
    payload: dict[str, Any]


def validate_repository(root: Path, selected_checks: set[str] | None = None) -> list[str]:
    checks = CHECKS if selected_checks is None else selected_checks
    errors: list[str] = []

    errors.extend(_check_required_directories(root))
    records, parse_errors = _load_records(root)
    errors.extend(parse_errors)
    if parse_errors:
        return errors

    if "schemas" in checks:
        errors.extend(_validate_schemas(root, records))
    if "duplicates" in checks:
        errors.extend(_check_duplicate_ids(records))
    if "references" in checks:
        errors.extend(_check_references(records))
    if "mutations" in checks:
        errors.extend(_check_mutation_patterns(records))
    return errors


def _check_required_directories(root: Path) -> list[str]:
    errors: list[str] = []
    for name in RECORD_DIRECTORIES + (
        "methodology",
        "schemas",
        "tools",
        "docs",
        ".github/workflows",
    ):
        path = root / name
        if not path.exists() or not path.is_dir():
            errors.append(f"Missing required directory: {name}")
    return errors


def _record_paths(root: Path) -> list[Path]:
    paths: list[Path] = []
    for directory in RECORD_DIRECTORIES:
        record_dir = root / directory
        if record_dir.exists():
            paths.extend(record_dir.rglob("*.json"))
    return sorted(paths)


def _load_records(root: Path) -> tuple[list[Record], list[str]]:
    records: list[Record] = []
    errors: list[str] = []
    for file_path in _record_paths(root):
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{file_path}: invalid JSON ({exc})")
            continue

        if not isinstance(payload, dict):
            errors.append(f"{file_path}: root must be an object")
            continue

        record_type = payload.get("record_type")
        record_id = payload.get("id")
        if not isinstance(record_type, str) or not record_type:
            errors.append(f"{file_path}: missing or invalid record_type")
            continue
        if not isinstance(record_id, str) or not record_id:
            errors.append(f"{file_path}: missing or invalid id")
            continue

        records.append(
            Record(
                file_path=file_path,
                record_type=record_type,
                record_id=record_id,
                payload=payload,
            )
        )
    return records, errors


def _load_validators(root: Path) -> tuple[dict[str, Draft202012Validator], list[str]]:
    validators: dict[str, Draft202012Validator] = {}
    errors: list[str] = []
    for record_type, schema_name in SCHEMA_BY_RECORD_TYPE.items():
        schema_path = root / "schemas" / schema_name
        if not schema_path.exists():
            errors.append(f"Missing schema file: schemas/{schema_name}")
            continue
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{schema_path}: invalid JSON ({exc})")
            continue
        try:
            Draft202012Validator.check_schema(schema)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{schema_path}: invalid schema ({exc})")
            continue

        validators[record_type] = Draft202012Validator(schema)
    return validators, errors


def _validate_schemas(root: Path, records: list[Record]) -> list[str]:
    errors: list[str] = []
    validators, validator_errors = _load_validators(root)
    errors.extend(validator_errors)
    if validator_errors:
        return errors

    for record in records:
        validator = validators.get(record.record_type)
        if validator is None:
            errors.append(
                f"{record.file_path}: no schema registered for record_type '{record.record_type}'"
            )
            continue
        for schema_error in validator.iter_errors(record.payload):
            errors.append(
                f"{record.file_path}: schema validation error at "
                f"{'/'.join(str(i) for i in schema_error.path) or '<root>'}: "
                f"{schema_error.message}"
            )
    return errors


def _check_duplicate_ids(records: list[Record]) -> list[str]:
    by_id: dict[str, list[Record]] = {}
    for record in records:
        by_id.setdefault(record.record_id, []).append(record)

    errors: list[str] = []
    for record_id, group in by_id.items():
        if len(group) > 1:
            locations = ", ".join(str(item.file_path) for item in group)
            errors.append(f"Duplicate record id '{record_id}' found in: {locations}")
    return errors


def _check_references(records: list[Record]) -> list[str]:
    ids = {record.record_id for record in records}
    ids_by_type: dict[str, set[str]] = {}
    for record in records:
        ids_by_type.setdefault(record.record_type, set()).add(record.record_id)

    errors: list[str] = []
    for record in records:
        payload = record.payload
        errors.extend(
            _check_id_list_reference(
                record, payload.get("evidence_ids"), ids_by_type.get("evidence", set()), "evidence_ids"
            )
        )
        errors.extend(
            _check_id_list_reference(
                record,
                payload.get("observation_ids"),
                ids_by_type.get("observation", set()),
                "observation_ids",
            )
        )
        errors.extend(
            _check_id_list_reference(
                record,
                payload.get("hypothesis_ids"),
                ids_by_type.get("hypothesis", set()),
                "hypothesis_ids",
            )
        )
        errors.extend(
            _check_id_list_reference(
                record,
                payload.get("competing_explanation_ids"),
                ids_by_type.get("hypothesis", set()),
                "competing_explanation_ids",
            )
        )
        errors.extend(
            _check_id_list_reference(
                record,
                payload.get("experiment_ids"),
                ids_by_type.get("experiment", set()),
                "experiment_ids",
            )
        )
        errors.extend(
            _check_id_list_reference(
                record, payload.get("result_ids"), ids_by_type.get("result", set()), "result_ids"
            )
        )

        for key in ("supersedes_id", "superseded_by_id"):
            value = payload.get(key)
            if value is None:
                continue
            if not isinstance(value, str) or not value:
                errors.append(f"{record.file_path}: {key} must be a non-empty string when present")
                continue
            if value not in ids:
                errors.append(f"{record.file_path}: {key} '{value}' does not resolve to an existing record")

        references = payload.get("references")
        if references is None:
            continue
        if not isinstance(references, list):
            errors.append(f"{record.file_path}: references must be an array")
            continue
        for idx, reference in enumerate(references):
            if not isinstance(reference, dict):
                errors.append(f"{record.file_path}: references[{idx}] must be an object")
                continue
            ref_type = reference.get("record_type")
            ref_id = reference.get("id")
            if not isinstance(ref_type, str) or not isinstance(ref_id, str):
                errors.append(
                    f"{record.file_path}: references[{idx}] requires string record_type and id"
                )
                continue
            if ref_id not in ids_by_type.get(ref_type, set()):
                errors.append(
                    f"{record.file_path}: references[{idx}] -> {ref_type}:{ref_id} does not resolve"
                )
    return errors


def _check_id_list_reference(
    record: Record, values: Any, allowed_ids: set[str], field_name: str
) -> list[str]:
    errors: list[str] = []
    if values is None:
        return errors
    if not isinstance(values, list):
        return [f"{record.file_path}: {field_name} must be an array"]
    for value in values:
        if not isinstance(value, str) or not value:
            errors.append(f"{record.file_path}: {field_name} entries must be non-empty strings")
            continue
        if value not in allowed_ids:
            errors.append(f"{record.file_path}: {field_name} contains unresolved id '{value}'")
    return errors


def _check_mutation_patterns(records: list[Record]) -> list[str]:
    errors: list[str] = []
    by_id = {record.record_id: record for record in records}

    forward: dict[str, str] = {}
    for record in records:
        supersedes = record.payload.get("supersedes_id")
        if supersedes is None:
            continue
        if supersedes == record.record_id:
            errors.append(f"{record.file_path}: supersedes_id cannot reference itself")
            continue
        if supersedes in forward and forward[supersedes] != record.record_id:
            errors.append(
                f"{record.file_path}: predecessor '{supersedes}' has multiple successors "
                f"('{forward[supersedes]}' and '{record.record_id}')"
            )
        forward[supersedes] = record.record_id

        predecessor = by_id.get(supersedes)
        predecessor_pointer = predecessor.payload.get("superseded_by_id") if predecessor else None
        if predecessor is not None and predecessor_pointer not in (None, record.record_id):
            errors.append(
                f"{record.file_path}: predecessor '{supersedes}' points to "
                f"'{predecessor_pointer}' instead of '{record.record_id}'"
            )

    _detect_cycles_in_edges(forward, errors)

    reverse: dict[str, str] = {}
    for record in records:
        successor = record.payload.get("superseded_by_id")
        if not isinstance(successor, str) or not successor:
            continue
        reverse[record.record_id] = successor
    _detect_cycles_in_edges(reverse, errors)
    return errors


def _detect_cycles_in_edges(edges: dict[str, str], errors: list[str]) -> None:
    for start in edges:
        current = start
        seen: set[str] = set()
        while current in edges:
            if current in seen:
                errors.append(f"Supersession cycle detected involving record '{current}'")
                break
            seen.add(current)
            current = edges[current]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate governed observatory records")
    parser.add_argument("--root", type=Path, default=Path("."), help="Repository root path")
    parser.add_argument(
        "--check",
        choices=["all", "schemas", "duplicates", "references", "mutations"],
        default="all",
        help="Run one check or all checks",
    )
    args = parser.parse_args()

    selected = CHECKS if args.check == "all" else {args.check}
    errors = validate_repository(args.root.resolve(), selected_checks=selected)
    if errors:
        for error in errors:
            print(error)
        return 1
    print("Validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

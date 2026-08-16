import json
import tempfile
import unittest
from pathlib import Path

from tools.validate_records import validate_repository

REPO_ROOT = Path(__file__).resolve().parents[2]

SCHEMA_FILES = (
    "evidence.schema.json",
    "observation.schema.json",
    "hypothesis.schema.json",
    "experiment.schema.json",
    "result.schema.json",
    "analysis.schema.json",
    "subject.schema.json",
    "provenance.schema.json",
)

REQUIRED_DIRS = (
    "raw-evidence",
    "metadata",
    "observations",
    "hypotheses",
    "baselines",
    "experiments",
    "results",
    "analysis",
    "methodology",
    "schemas",
    "tools",
    "docs",
    ".github/workflows",
)


def _build_repo() -> Path:
    temp_dir = Path(tempfile.mkdtemp())
    for directory in REQUIRED_DIRS:
        (temp_dir / directory).mkdir(parents=True, exist_ok=True)
    for schema_file in SCHEMA_FILES:
        src = REPO_ROOT / "schemas" / schema_file
        dst = temp_dir / "schemas" / schema_file
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    return temp_dir


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


class ValidateRecordsTests(unittest.TestCase):
    def test_successful_validation(self) -> None:
        root = _build_repo()
        _write_json(
            root / "raw-evidence" / "ev-1.json",
            {
                "record_type": "evidence",
                "id": "ev-1",
                "schema_version": "1.0.0",
                "recorded_at": "2026-08-16T00:00:00Z",
                "provenance": {
                    "record_type": "provenance",
                    "id": "prov-inline-1",
                    "schema_version": "1.0.0",
                    "recorded_at": "2026-08-16T00:00:00Z",
                    "observer_id": "observer-1",
                    "observer_type": "human"
                },
                "source_references": [
                    "file://capture.txt"
                ]
            },
        )
        _write_json(
            root / "observations" / "obs-1.json",
            {
                "record_type": "observation",
                "id": "obs-1",
                "schema_version": "1.0.0",
                "recorded_at": "2026-08-16T00:05:00Z",
                "evidence_ids": [
                    "ev-1"
                ]
            },
        )
        _write_json(
            root / "hypotheses" / "hyp-1.json",
            {
                "record_type": "hypothesis",
                "id": "hyp-1",
                "schema_version": "1.0.0",
                "recorded_at": "2026-08-16T00:10:00Z",
                "observation_ids": [
                    "obs-1"
                ]
            },
        )
        _write_json(
            root / "experiments" / "exp-1.json",
            {
                "record_type": "experiment",
                "id": "exp-1",
                "schema_version": "1.0.0",
                "recorded_at": "2026-08-16T00:15:00Z",
                "hypothesis_ids": [
                    "hyp-1"
                ]
            },
        )
        _write_json(
            root / "results" / "res-1.json",
            {
                "record_type": "result",
                "id": "res-1",
                "schema_version": "1.0.0",
                "recorded_at": "2026-08-16T00:20:00Z",
                "experiment_ids": [
                    "exp-1"
                ]
            },
        )
        _write_json(
            root / "analysis" / "ana-1.json",
            {
                "record_type": "analysis",
                "id": "ana-1",
                "schema_version": "1.0.0",
                "recorded_at": "2026-08-16T00:25:00Z",
                "result_ids": [
                    "res-1"
                ]
            },
        )

        errors = validate_repository(root)
        self.assertEqual([], errors)

    def test_duplicate_ids_fail(self) -> None:
        root = _build_repo()
        payload = {
            "record_type": "subject",
            "id": "shared-id",
            "schema_version": "1.0.0",
            "recorded_at": "2026-08-16T00:00:00Z"
        }
        _write_json(root / "metadata" / "subject-1.json", payload)
        _write_json(root / "metadata" / "subject-2.json", payload)

        errors = validate_repository(root, selected_checks={"duplicates"})
        self.assertTrue(any("Duplicate record id 'shared-id'" in err for err in errors))

    def test_broken_reference_fails(self) -> None:
        root = _build_repo()
        _write_json(
            root / "observations" / "obs-1.json",
            {
                "record_type": "observation",
                "id": "obs-1",
                "schema_version": "1.0.0",
                "recorded_at": "2026-08-16T00:00:00Z",
                "evidence_ids": [
                    "missing-evidence"
                ]
            },
        )

        errors = validate_repository(root, selected_checks={"references"})
        self.assertTrue(any("unresolved id 'missing-evidence'" in err for err in errors))

    def test_supersession_cycle_fails(self) -> None:
        root = _build_repo()
        _write_json(
            root / "raw-evidence" / "ev-1.json",
            {
                "record_type": "evidence",
                "id": "ev-1",
                "schema_version": "1.0.0",
                "recorded_at": "2026-08-16T00:00:00Z",
                "provenance": {
                    "record_type": "provenance",
                    "id": "prov-1",
                    "schema_version": "1.0.0",
                    "recorded_at": "2026-08-16T00:00:00Z",
                    "observer_id": "observer-1",
                    "observer_type": "human"
                },
                "source_references": [
                    "file://a.txt"
                ],
                "superseded_by_id": "ev-2"
            },
        )
        _write_json(
            root / "raw-evidence" / "ev-2.json",
            {
                "record_type": "evidence",
                "id": "ev-2",
                "schema_version": "1.0.0",
                "recorded_at": "2026-08-16T00:01:00Z",
                "provenance": {
                    "record_type": "provenance",
                    "id": "prov-2",
                    "schema_version": "1.0.0",
                    "recorded_at": "2026-08-16T00:01:00Z",
                    "observer_id": "observer-2",
                    "observer_type": "human"
                },
                "source_references": [
                    "file://b.txt"
                ],
                "supersedes_id": "ev-1",
                "superseded_by_id": "ev-1"
            },
        )

        errors = validate_repository(root, selected_checks={"mutations"})
        self.assertTrue(any("Supersession cycle detected" in err for err in errors))


if __name__ == "__main__":
    unittest.main()

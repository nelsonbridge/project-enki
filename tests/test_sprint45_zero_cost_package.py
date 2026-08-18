from __future__ import annotations

import json
from pathlib import Path

from jsonschema import validate


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "releases" / "enki-hosted-1.0-rc2" / "evidence" / "sprint45"
SCHEMA_PATH = ROOT / "releases" / "enki-hosted-1.0-rc2" / "production-control-evidence.schema.json"
GATES_PATH = ROOT / "releases" / "enki-hosted-1.0-rc2" / "sprint45-control-acceptance-gates.json"
LOCK_PATH = ROOT / "releases" / "enki-hosted-1.0-rc2" / "architecture-lock.json"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_sprint45_evidence_files_exist_for_all_controls() -> None:
    files = sorted(EVIDENCE_DIR.glob("*.json"))
    assert len(files) == 7
    control_ids = {_load(path)["control_id"] for path in files}
    assert control_ids == {
        "cloud-iam",
        "production-identity-federation",
        "managed-database-row-level-isolation",
        "network-segmentation",
        "per-tenant-production-key-management",
        "production-secrets-management",
        "incident-failure-exercises",
    }


def test_sprint45_evidence_conforms_to_schema_and_zero_cost_invariants() -> None:
    schema = _load(SCHEMA_PATH)
    for path in sorted(EVIDENCE_DIR.glob("*.json")):
        payload = _load(path)
        validate(instance=payload, schema=schema)
        assert payload["validation_scope"]["external_services_budget_usd"] == 0
        assert payload["cost_attestation"]["currency"] == "USD"
        assert payload["cost_attestation"]["total_observed_cost_usd"] == 0
        for item in payload["cost_attestation"]["provider_checks"]:
            assert item["observed_cost_usd"] == 0
            assert item["evidence_location"]


def test_sprint45_gate_manifest_preserves_rc2_and_fail_closed_behavior() -> None:
    lock = _load(LOCK_PATH)
    gates = _load(GATES_PATH)
    assert lock["architecture_id"] == "CF-NEON-R2"
    assert gates["architecture_authority"] == "CF-NEON-R2"
    assert gates["fail_closed_default_status"] == "PARTIAL"
    assert len(gates["controls"]) == 7


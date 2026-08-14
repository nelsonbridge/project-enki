from __future__ import annotations

import json
from pathlib import Path

from nks.application.hosting_validation import (
    HostedExecutionState,
    evaluate_hosted_preflight,
    read_hosted_capabilities_from_env,
)
from nks.application.sprint26_path_manifest import sprint26_cf_native_path_manifest
from nks.governance.approvals import ExecutionContext


ROOT = Path(__file__).resolve().parents[1]


def _record(path: str) -> dict[str, object]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_cf_native_preflight_fails_closed_without_external_capabilities() -> None:
    preflight = evaluate_hosted_preflight("CF-NATIVE", {})

    assert preflight.state == HostedExecutionState.BLOCKED_EXTERNAL_CAPABILITY
    assert preflight.missing_capabilities == (
        "provider_test_identity",
        "provider_test_credentials",
        "teardown_authority",
    )


def test_cf_native_records_are_in_progress_with_capability_evidence() -> None:
    sprint = _record("records/sprints/NKS-SPR-026.json")
    work_item = _record("records/work-items/BL-026.json")

    assert sprint["status"] == "in_progress"
    assert work_item["status"] == "in_progress"
    assert sprint["blocked_reason"] is None
    assert work_item["blocked_reason"] is None

    sprint_refs = {e["evidence_id"] for e in sprint.get("evidence", [])}
    work_item_refs = {e["evidence_id"] for e in work_item.get("evidence", [])}
    assert "E-S26-CAPABILITIES" in sprint_refs
    assert "E-S26-WORKFLOW" in sprint_refs
    assert "E-BL026-CAPABILITIES" in work_item_refs
    assert "E-BL026-WORKFLOW" in work_item_refs


SPRINT26_TESTED_PATHS = {
    "external-test-capabilities-required",
    "missing-capabilities-fail-closed",
    "blocked-reason-explicit-and-attributable",
    "production-credential-substitution-prohibited",
    "hosted-success-claim-without-capabilities-prohibited",
}


def test_every_declared_sprint26_path_has_automated_coverage() -> None:
    sprint26_cf_native_path_manifest().assert_complete_coverage(SPRINT26_TESTED_PATHS)


def test_sprint26_paths_are_test_only_and_prohibit_unsafe_effects() -> None:
    manifest = sprint26_cf_native_path_manifest()
    assert manifest.execution_context == ExecutionContext.TEST
    for path in manifest.paths:
        assert "production-effect" in path.prohibited_effects
        assert "production-approval" in path.prohibited_effects
        assert "credential-reuse" in path.prohibited_effects
        assert "teardown-bypass" in path.prohibited_effects
        assert "simulated-hosted-success-without-capabilities" in path.prohibited_effects


def test_read_hosted_capabilities_from_env_fails_closed_when_secrets_absent(
    monkeypatch: object,
) -> None:
    import pytest

    for var in ("CF_TEST_ACCOUNT_ID", "CF_TEST_API_TOKEN", "CF_TEST_TEARDOWN_TOKEN"):
        monkeypatch.delenv(var, raising=False)

    caps = read_hosted_capabilities_from_env("CF-NATIVE")
    assert caps["provider_test_identity"] is False
    assert caps["provider_test_credentials"] is False
    assert caps["teardown_authority"] is False

    preflight = evaluate_hosted_preflight("CF-NATIVE", caps)
    assert preflight.state == HostedExecutionState.BLOCKED_EXTERNAL_CAPABILITY


def test_read_hosted_capabilities_from_env_ready_when_all_secrets_present(
    monkeypatch: object,
) -> None:
    monkeypatch.setenv("CF_TEST_ACCOUNT_ID", "test-acct-id")
    monkeypatch.setenv("CF_TEST_API_TOKEN", "test-api-token")
    monkeypatch.setenv("CF_TEST_TEARDOWN_TOKEN", "test-teardown-token")

    caps = read_hosted_capabilities_from_env("CF-NATIVE")
    assert caps["provider_test_identity"] is True
    assert caps["provider_test_credentials"] is True
    assert caps["teardown_authority"] is True

    preflight = evaluate_hosted_preflight("CF-NATIVE", caps)
    assert preflight.state == HostedExecutionState.READY
    assert preflight.missing_capabilities == ()


def test_read_hosted_capabilities_from_env_rejects_unknown_finalist() -> None:
    import pytest

    with pytest.raises(ValueError, match="unknown hosting finalist"):
        read_hosted_capabilities_from_env("UNKNOWN-FINALIST")

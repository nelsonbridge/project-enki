from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from nks.enki.federation_intake import (
    FederationPromotionDecision,
    FederationPromotionDisposition,
    FederationReconciliation,
    FederationReconciliationDisposition,
    GovernedFederationIntake,
)
from nks.enki.federation_portability import (
    FederationPortableBundle,
    export_federation_bundle,
    replay_federation_bundle,
)
from nks.enki.temporal_graph import (
    TemporalGraphLifecycleStatus,
    TemporalGraphNodeType,
    TemporalGraphRecord,
    TemporalGraphRecordKind,
)


T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
T1 = datetime(2026, 2, 1, tzinfo=timezone.utc)
T2 = datetime(2026, 3, 1, tzinfo=timezone.utc)
T3 = datetime(2026, 4, 1, tzinfo=timezone.utc)
T4 = datetime(2026, 5, 1, tzinfo=timezone.utc)


def source_record(
    record_id: str = "source-1",
    *,
    namespace: str = "observatory:study",
    recorded_at: datetime = T0,
    effective_from: datetime | None = T0,
    **overrides: object,
) -> TemporalGraphRecord:
    payload: dict[str, object] = {
        "graph_record_id": record_id,
        "graph_namespace": namespace,
        "record_kind": TemporalGraphRecordKind.NODE,
        "node_type": TemporalGraphNodeType.OBSERVATION,
        "domain_id": "general",
        "context_ids": ("ctx",),
        "content": {"value": record_id},
        "provenance_refs": (f"source:{record_id}",),
        "authority_state_ref": None,
        "recorded_at": recorded_at,
        "effective_from": effective_from,
        "effective_to": None,
        "authority_from": None,
        "authority_to": None,
        "superseded_at": None,
        "lifecycle_status": TemporalGraphLifecycleStatus.ACTIVE,
    }
    payload.update(overrides)
    return TemporalGraphRecord(**payload)


def target_record(
    record_id: str = "target-1",
    *,
    authority_to: datetime | None = None,
    **overrides: object,
) -> TemporalGraphRecord:
    payload: dict[str, object] = {
        "graph_record_id": record_id,
        "graph_namespace": "project:enki",
        "record_kind": TemporalGraphRecordKind.NODE,
        "node_type": TemporalGraphNodeType.INTERPRETATION,
        "domain_id": "general",
        "context_ids": ("ctx",),
        "content": {"interpretation": record_id},
        "provenance_refs": (f"proposal:{record_id}",),
        "authority_state_ref": "authority-state:1",
        "recorded_at": T2,
        "effective_from": T0,
        "effective_to": None,
        "authority_from": T2,
        "authority_to": authority_to,
        "superseded_at": None,
        "lifecycle_status": TemporalGraphLifecycleStatus.ACTIVE,
    }
    payload.update(overrides)
    return TemporalGraphRecord(**payload)


def reconciliation(
    reconciliation_id: str = "recon-1",
    *,
    source_namespace: str = "observatory:study",
    source_record_id: str = "source-1",
    disposition: FederationReconciliationDisposition = FederationReconciliationDisposition.MATCH,
    recorded_at: datetime = T1,
    reopens_reconciliation_id: str | None = None,
) -> FederationReconciliation:
    return FederationReconciliation(
        reconciliation_id=reconciliation_id,
        source_namespace=source_namespace,
        source_record_id=source_record_id,
        target_namespace="project:enki",
        disposition=disposition,
        evidence_refs=(f"evidence:{reconciliation_id}",),
        rationale=f"reconcile {reconciliation_id}",
        recorded_at=recorded_at,
        reopens_reconciliation_id=reopens_reconciliation_id,
    )


def decision(
    decision_id: str = "decision-1",
    *,
    reconciliation_id: str = "recon-1",
    source_namespace: str = "observatory:study",
    source_record_id: str = "source-1",
    disposition: FederationPromotionDisposition = FederationPromotionDisposition.PROMOTE,
    recorded_at: datetime = T2,
) -> FederationPromotionDecision:
    return FederationPromotionDecision(
        decision_id=decision_id,
        source_namespace=source_namespace,
        source_record_id=source_record_id,
        target_namespace="project:enki",
        reconciliation_id=reconciliation_id,
        disposition=disposition,
        authority_decision_ref=f"authority:{decision_id}",
        recorded_at=recorded_at,
    )


def governing_ledger(
    *,
    source: TemporalGraphRecord | None = None,
    target: TemporalGraphRecord | None = None,
) -> GovernedFederationIntake:
    ledger = GovernedFederationIntake()
    ledger.ingest(source or source_record(), source_namespace="observatory:study", received_at=T1)
    ledger.reconcile(reconciliation())
    ledger.decide(decision(), proposed_target=target or target_record())
    return ledger


def test_json_round_trip_reconstructs_exact_governed_ledger() -> None:
    original = governing_ledger()
    bundle = export_federation_bundle(original)

    replayed = replay_federation_bundle(bundle.to_json())

    assert replayed.ledger_hash == original.ledger_hash
    assert replayed.target_record("project:enki", "target-1").record_hash == original.target_record(
        "project:enki", "target-1"
    ).record_hash
    assert replayed.target_record("project:enki", "target-1").is_authoritative_at(T3) is True


def test_authority_window_survives_export_and_replay() -> None:
    original = governing_ledger(target=target_record(authority_to=T4))

    replayed = replay_federation_bundle(export_federation_bundle(original))
    target = replayed.target_record("project:enki", "target-1")

    assert target.authority_from == T2
    assert target.authority_to == T4
    assert target.is_authoritative_at(T3) is True
    assert target.is_authoritative_at(T4) is False


def test_unknown_effective_time_and_recorded_time_are_preserved() -> None:
    source = source_record(recorded_at=T2, effective_from=None)
    original = governing_ledger(source=source)

    replayed = replay_federation_bundle(export_federation_bundle(original).to_json())
    replayed_source = replayed.source_record("observatory:study", "source-1")

    assert replayed_source.recorded_at == T2
    assert replayed_source.effective_from is None


def test_revision_and_supersession_fields_survive_round_trip() -> None:
    source = source_record(
        lifecycle_status=TemporalGraphLifecycleStatus.SUPERSEDED,
        superseded_at=T1,
        supersedes_record_ids=("older-1",),
        revises_record_ids=("older-2",),
    )
    original = governing_ledger(source=source)

    replayed = replay_federation_bundle(export_federation_bundle(original))
    replayed_source = replayed.source_record("observatory:study", "source-1")

    assert replayed_source.lifecycle_status == TemporalGraphLifecycleStatus.SUPERSEDED
    assert replayed_source.superseded_at == T1
    assert replayed_source.supersedes_record_ids == ("older-1",)
    assert replayed_source.revises_record_ids == ("older-2",)


def test_conflict_and_later_reopened_reconciliation_are_both_preserved() -> None:
    ledger = GovernedFederationIntake()
    ledger.ingest(source_record(), source_namespace="observatory:study", received_at=T1)
    ledger.reconcile(
        reconciliation(
            "recon-conflict",
            disposition=FederationReconciliationDisposition.CONFLICT,
        )
    )
    ledger.reconcile(
        reconciliation(
            "recon-reopened",
            disposition=FederationReconciliationDisposition.MATCH,
            recorded_at=T2,
            reopens_reconciliation_id="recon-conflict",
        )
    )

    replayed = replay_federation_bundle(export_federation_bundle(ledger).to_json())

    assert [item.reconciliation_id for item in replayed.reconciliations] == [
        "recon-conflict",
        "recon-reopened",
    ]
    assert replayed.reconciliations[1].reopens_reconciliation_id == "recon-conflict"
    assert replayed.ledger_hash == ledger.ledger_hash


def test_rejected_decision_remains_auditable_without_target() -> None:
    ledger = GovernedFederationIntake()
    ledger.ingest(source_record(), source_namespace="observatory:study", received_at=T1)
    ledger.reconcile(
        reconciliation(disposition=FederationReconciliationDisposition.REJECT)
    )
    ledger.decide(decision(disposition=FederationPromotionDisposition.REJECT))

    replayed = replay_federation_bundle(export_federation_bundle(ledger))

    assert len(replayed.promotion_receipts) == 1
    assert replayed.promotion_receipts[0].disposition == FederationPromotionDisposition.REJECT
    assert replayed.promotion_receipts[0].target_record_id is None
    assert replayed.ledger_hash == ledger.ledger_hash


def test_tampered_source_record_fails_closed() -> None:
    bundle = export_federation_bundle(governing_ledger())
    payload = bundle.model_dump(mode="json")
    payload["intake_events"][0]["record"]["content"] = {"value": "tampered"}

    with pytest.raises(ValidationError, match="receipt hash does not match source record"):
        FederationPortableBundle.model_validate(payload)


def test_tampered_expected_target_fails_closed() -> None:
    bundle = export_federation_bundle(governing_ledger())
    payload = bundle.model_dump(mode="json")
    payload["decision_events"][0]["expected_target"]["content"] = {
        "interpretation": "tampered"
    }

    with pytest.raises(ValidationError, match="target hash does not match expected target"):
        FederationPortableBundle.model_validate(payload)


def test_unknown_bundle_or_temporal_contract_version_is_rejected() -> None:
    bundle = export_federation_bundle(governing_ledger())
    unknown_bundle = bundle.model_dump(mode="json")
    unknown_bundle["bundle_version"] = "2.0"
    with pytest.raises(ValidationError):
        FederationPortableBundle.model_validate(unknown_bundle)

    unknown_contract = bundle.model_dump(mode="json")
    unknown_contract["temporal_contract_version"] = "2.0"
    with pytest.raises(ValidationError):
        FederationPortableBundle.model_validate(unknown_contract)


def test_equivalent_source_insertion_orders_have_same_bundle_hash() -> None:
    a = source_record("a")
    b = source_record("b", namespace="project:producer")
    first = GovernedFederationIntake()
    second = GovernedFederationIntake()

    first.ingest(a, source_namespace="observatory:study", received_at=T1)
    first.ingest(b, source_namespace="project:producer", received_at=T1)
    second.ingest(b, source_namespace="project:producer", received_at=T1)
    second.ingest(a, source_namespace="observatory:study", received_at=T1)

    first_bundle = export_federation_bundle(first)
    second_bundle = export_federation_bundle(second)
    assert first.ledger_hash == second.ledger_hash
    assert first_bundle.bundle_hash == second_bundle.bundle_hash


def test_tampered_exported_ledger_hash_fails_replay() -> None:
    bundle = export_federation_bundle(governing_ledger())
    payload = bundle.model_dump(mode="json")
    payload["source_ledger_hash"] = "0" * 64

    with pytest.raises(ValueError, match="ledger hash does not match"):
        replay_federation_bundle(payload)

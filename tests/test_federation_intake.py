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
from nks.enki.temporal_graph import (
    TemporalGraphEdgeType,
    TemporalGraphLifecycleStatus,
    TemporalGraphNodeType,
    TemporalGraphPromotion,
    TemporalGraphRecord,
    TemporalGraphRecordKind,
)


T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
T1 = datetime(2026, 2, 1, tzinfo=timezone.utc)
T2 = datetime(2026, 3, 1, tzinfo=timezone.utc)
T3 = datetime(2026, 4, 1, tzinfo=timezone.utc)


def source_record(
    record_id: str = "source-1",
    *,
    namespace: str = "observatory:study",
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
        "recorded_at": T0,
        "effective_from": T0,
        "effective_to": None,
        "authority_state_ref": None,
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
    lifecycle_status: TemporalGraphLifecycleStatus = TemporalGraphLifecycleStatus.QUALIFIED,
    authority_state_ref: str | None = None,
    authority_from: datetime | None = None,
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
        "authority_state_ref": authority_state_ref,
        "recorded_at": T2,
        "effective_from": T0,
        "effective_to": None,
        "authority_from": authority_from,
        "authority_to": None,
        "superseded_at": None,
        "lifecycle_status": lifecycle_status,
    }
    payload.update(overrides)
    return TemporalGraphRecord(**payload)


def reconciliation(
    reconciliation_id: str = "recon-1",
    *,
    source_namespace: str = "observatory:study",
    source_record_id: str = "source-1",
    target_namespace: str = "project:enki",
    disposition: FederationReconciliationDisposition = FederationReconciliationDisposition.MATCH,
    recorded_at: datetime = T1,
    **overrides: object,
) -> FederationReconciliation:
    payload: dict[str, object] = {
        "reconciliation_id": reconciliation_id,
        "source_namespace": source_namespace,
        "source_record_id": source_record_id,
        "target_namespace": target_namespace,
        "disposition": disposition,
        "evidence_refs": ("evidence:1",),
        "rationale": "explicit comparison",
        "recorded_at": recorded_at,
    }
    payload.update(overrides)
    return FederationReconciliation(**payload)


def decision(
    decision_id: str = "decision-1",
    *,
    reconciliation_id: str = "recon-1",
    disposition: FederationPromotionDisposition = FederationPromotionDisposition.QUALIFY,
    source_namespace: str = "observatory:study",
    source_record_id: str = "source-1",
    target_namespace: str = "project:enki",
    recorded_at: datetime = T2,
) -> FederationPromotionDecision:
    return FederationPromotionDecision(
        decision_id=decision_id,
        source_namespace=source_namespace,
        source_record_id=source_record_id,
        target_namespace=target_namespace,
        reconciliation_id=reconciliation_id,
        disposition=disposition,
        authority_decision_ref=f"authority:{decision_id}",
        recorded_at=recorded_at,
    )


def admitted_ledger() -> GovernedFederationIntake:
    ledger = GovernedFederationIntake()
    ledger.ingest(source_record(), source_namespace="observatory:study", received_at=T1)
    return ledger


def reconciled_ledger() -> GovernedFederationIntake:
    ledger = admitted_ledger()
    ledger.reconcile(reconciliation())
    return ledger


def test_intake_preserves_unknown_effective_time_without_granting_authority() -> None:
    ledger = GovernedFederationIntake()
    record = source_record(effective_from=None)

    receipt = ledger.ingest(record, source_namespace="observatory:study", received_at=T1)
    stored = ledger.source_record("observatory:study", "source-1")

    assert receipt.admitted_as_candidate is True
    assert stored.record_hash == record.record_hash
    assert stored.effective_from is None
    assert stored.authority_from is None
    assert stored.is_authoritative_at(T2) is False


def test_intake_is_idempotent_but_same_id_changed_content_fails() -> None:
    ledger = GovernedFederationIntake()
    first = source_record()
    receipt = ledger.ingest(first, source_namespace="observatory:study", received_at=T1)

    repeated = ledger.ingest(first, source_namespace="observatory:study", received_at=T2)
    assert repeated == receipt

    changed = source_record(content={"value": "changed"})
    with pytest.raises(ValueError, match="different content"):
        ledger.ingest(changed, source_namespace="observatory:study", received_at=T2)


def test_intake_rejects_namespace_mismatch_and_authority_escalation() -> None:
    ledger = GovernedFederationIntake()
    with pytest.raises(ValueError, match="source namespace"):
        ledger.ingest(source_record(), source_namespace="project:other", received_at=T1)

    authoritative = source_record(authority_state_ref="local:authority", authority_from=T0)
    with pytest.raises(ValueError, match="cannot transfer authority"):
        ledger.ingest(authoritative, source_namespace="observatory:study", received_at=T1)


def test_intake_rejects_pre_authorized_cross_namespace_promotion() -> None:
    ledger = GovernedFederationIntake()
    promotion = TemporalGraphPromotion(
        source_namespace="project:other",
        target_namespace="observatory:study",
        reconciliation_ref="recon:external",
        authority_decision_ref="authority:external",
    )
    record = source_record(promotion=promotion)

    with pytest.raises(ValueError, match="cannot arrive with cross-namespace promotion"):
        ledger.ingest(record, source_namespace="observatory:study", received_at=T1)


def test_reconciliation_is_explicit_non_authoritative_and_reopenable() -> None:
    ledger = admitted_ledger()
    first = reconciliation(
        "recon-conflict",
        disposition=FederationReconciliationDisposition.CONFLICT,
    )
    ledger.reconcile(first)
    reopened = reconciliation(
        "recon-reopened",
        disposition=FederationReconciliationDisposition.MATCH,
        recorded_at=T2,
        reopens_reconciliation_id="recon-conflict",
    )

    stored = ledger.reconcile(reopened)

    assert stored.reopens_reconciliation_id == "recon-conflict"
    assert len(ledger.reconciliations) == 2
    assert ledger.source_record("observatory:study", "source-1").authority_from is None


def test_reconciliation_requires_admitted_source_and_distinct_namespace() -> None:
    ledger = GovernedFederationIntake()
    with pytest.raises(ValueError, match="has not passed federation intake"):
        ledger.reconcile(reconciliation())

    with pytest.raises(ValidationError, match="distinct namespaces"):
        reconciliation(target_namespace="observatory:study")


def test_qualification_creates_lineage_but_not_governing_authority() -> None:
    ledger = reconciled_ledger()
    proposal = target_record()

    receipt = ledger.decide(decision(), proposed_target=proposal)
    target = ledger.target_record("project:enki", "target-1")
    source = ledger.source_record("observatory:study", "source-1")

    assert receipt.disposition == FederationPromotionDisposition.QUALIFY
    assert target.lifecycle_status == TemporalGraphLifecycleStatus.QUALIFIED
    assert target.is_authoritative_at(T3) is False
    assert target.promotion is not None
    assert target.promotion.reconciliation_ref == "recon-1"
    assert "federation-source:observatory:study:source-1" in target.provenance_refs
    assert source.promotion is None
    assert source.record_hash == source_record().record_hash


def test_governing_promotion_requires_explicit_authority_state_and_interval() -> None:
    ledger = reconciled_ledger()
    promote = decision(disposition=FederationPromotionDisposition.PROMOTE)
    non_authoritative_target = target_record(
        lifecycle_status=TemporalGraphLifecycleStatus.ACTIVE,
    )

    with pytest.raises(ValueError, match="explicit authority state and authority interval"):
        ledger.decide(promote, proposed_target=non_authoritative_target)

    authoritative_target = target_record(
        lifecycle_status=TemporalGraphLifecycleStatus.ACTIVE,
        authority_state_ref="authority-state:1",
        authority_from=T2,
    )
    receipt = ledger.decide(promote, proposed_target=authoritative_target)
    target = ledger.target_record("project:enki", "target-1")

    assert receipt.disposition == FederationPromotionDisposition.PROMOTE
    assert target.is_authoritative_at(T3) is True
    assert target.promotion is not None
    assert target.promotion.authority_decision_ref == "authority:decision-1"


def test_promotion_requires_reconciliation_and_cannot_predate_it() -> None:
    ledger = admitted_ledger()
    proposal = target_record()

    with pytest.raises(ValueError, match="requires an existing reconciliation"):
        ledger.decide(decision(), proposed_target=proposal)

    ledger.reconcile(reconciliation(recorded_at=T2))
    early = decision(recorded_at=T1)
    with pytest.raises(ValueError, match="cannot predate reconciliation"):
        ledger.decide(early, proposed_target=proposal)


def test_rejected_reconciliation_can_only_produce_auditable_rejection() -> None:
    ledger = admitted_ledger()
    ledger.reconcile(
        reconciliation(disposition=FederationReconciliationDisposition.REJECT)
    )

    rejected = decision(disposition=FederationPromotionDisposition.REJECT)
    receipt = ledger.decide(rejected)

    assert receipt.target_record_id is None
    assert receipt.disposition == FederationPromotionDisposition.REJECT
    assert ledger.promotion_receipts == (receipt,)

    promote = decision(
        "decision-promote",
        disposition=FederationPromotionDisposition.PROMOTE,
    )
    proposal = target_record(
        lifecycle_status=TemporalGraphLifecycleStatus.ACTIVE,
        authority_state_ref="authority-state:1",
        authority_from=T2,
    )
    with pytest.raises(ValueError, match="cannot be qualified or promoted"):
        ledger.decide(promote, proposed_target=proposal)


def test_cross_namespace_edge_alone_never_transfers_authority() -> None:
    ledger = GovernedFederationIntake()
    edge = TemporalGraphRecord(
        graph_record_id="edge-1",
        graph_namespace="project:producer",
        record_kind=TemporalGraphRecordKind.EDGE,
        edge_type=TemporalGraphEdgeType.SUPPORTS,
        domain_id="general",
        source_record_id="a",
        target_record_id="b",
        provenance_refs=("source:edge-1",),
        recorded_at=T0,
        effective_from=T0,
        effective_to=None,
        authority_from=None,
        authority_to=None,
        superseded_at=None,
        lifecycle_status=TemporalGraphLifecycleStatus.ACTIVE,
    )

    ledger.ingest(edge, source_namespace="project:producer", received_at=T1)

    assert ledger.source_record("project:producer", "edge-1").is_authoritative_at(T2) is False


def test_candidate_causation_cannot_become_governing_through_promotion() -> None:
    ledger = reconciled_ledger()
    promote = decision(disposition=FederationPromotionDisposition.PROMOTE)
    candidate_edge = TemporalGraphRecord(
        graph_record_id="target-cause",
        graph_namespace="project:enki",
        record_kind=TemporalGraphRecordKind.EDGE,
        edge_type=TemporalGraphEdgeType.CANDIDATE_CAUSE_OF,
        domain_id="general",
        source_record_id="x",
        target_record_id="y",
        provenance_refs=("proposal:cause",),
        authority_state_ref=None,
        recorded_at=T2,
        effective_from=T0,
        effective_to=None,
        authority_from=None,
        authority_to=None,
        superseded_at=None,
        lifecycle_status=TemporalGraphLifecycleStatus.QUALIFIED,
    )

    with pytest.raises(ValueError, match="must use active lifecycle status"):
        ledger.decide(promote, proposed_target=candidate_edge)


def test_proposed_target_cannot_self_assert_promotion_or_wrong_namespace() -> None:
    ledger = reconciled_ledger()
    preauthorized = target_record(
        promotion=TemporalGraphPromotion(
            source_namespace="observatory:study",
            target_namespace="project:enki",
            reconciliation_ref="recon-1",
            authority_decision_ref="authority:other",
        )
    )
    with pytest.raises(ValueError, match="cannot self-assert"):
        ledger.decide(decision(), proposed_target=preauthorized)

    wrong_namespace = target_record(graph_namespace="project:other")
    with pytest.raises(ValueError, match="namespace does not match"):
        ledger.decide(decision(), proposed_target=wrong_namespace)


def test_decision_is_idempotent_but_changed_target_fails() -> None:
    ledger = reconciled_ledger()
    governed_decision = decision()
    first = ledger.decide(governed_decision, proposed_target=target_record())
    repeated = ledger.decide(governed_decision, proposed_target=target_record())
    assert repeated == first

    changed_target = target_record(content={"interpretation": "changed"})
    with pytest.raises(ValueError, match="different target"):
        ledger.decide(governed_decision, proposed_target=changed_target)


def test_ledger_hash_is_deterministic_across_equivalent_insertion_orders() -> None:
    first = GovernedFederationIntake()
    second = GovernedFederationIntake()
    a = source_record("a")
    b = source_record("b", namespace="project:producer")

    first.ingest(a, source_namespace="observatory:study", received_at=T1)
    first.ingest(b, source_namespace="project:producer", received_at=T1)
    second.ingest(b, source_namespace="project:producer", received_at=T1)
    second.ingest(a, source_namespace="observatory:study", received_at=T1)

    assert first.ledger_hash == second.ledger_hash

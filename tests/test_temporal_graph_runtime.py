from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from nks.enki.temporal_graph import (
    TemporalGraphEdgeType,
    TemporalGraphLifecycleStatus,
    TemporalGraphNodeType,
    TemporalGraphPromotion,
    TemporalGraphRecord,
    TemporalGraphRecordKind,
    TemporalGraphStore,
)


T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
T1 = datetime(2026, 2, 1, tzinfo=timezone.utc)
T2 = datetime(2026, 3, 1, tzinfo=timezone.utc)
T3 = datetime(2026, 4, 1, tzinfo=timezone.utc)


def _node(
    record_id: str,
    *,
    namespace: str = "project:enki",
    node_type: TemporalGraphNodeType = TemporalGraphNodeType.OBSERVATION,
    recorded_at: datetime = T0,
    effective_from: datetime | None = T0,
    effective_to: datetime | None = None,
    authority_from: datetime | None = T0,
    authority_to: datetime | None = None,
    superseded_at: datetime | None = None,
    lifecycle_status: TemporalGraphLifecycleStatus = TemporalGraphLifecycleStatus.ACTIVE,
    promotion: TemporalGraphPromotion | None = None,
) -> TemporalGraphRecord:
    return TemporalGraphRecord(
        graph_record_id=record_id,
        graph_namespace=namespace,
        record_kind=TemporalGraphRecordKind.NODE,
        node_type=node_type,
        domain_id="general",
        context_ids=("ctx-1",),
        content={"value": record_id},
        provenance_refs=(f"source:{record_id}",),
        recorded_at=recorded_at,
        effective_from=effective_from,
        effective_to=effective_to,
        authority_from=authority_from,
        authority_to=authority_to,
        superseded_at=superseded_at,
        lifecycle_status=lifecycle_status,
        promotion=promotion,
    )


def _edge(
    record_id: str,
    *,
    edge_type: TemporalGraphEdgeType = TemporalGraphEdgeType.SUPPORTS,
    lifecycle_status: TemporalGraphLifecycleStatus = TemporalGraphLifecycleStatus.ACTIVE,
) -> TemporalGraphRecord:
    return TemporalGraphRecord(
        graph_record_id=record_id,
        graph_namespace="project:enki",
        record_kind=TemporalGraphRecordKind.EDGE,
        edge_type=edge_type,
        domain_id="general",
        context_ids=("ctx-1",),
        source_record_id="n1",
        target_record_id="n2",
        content=None,
        provenance_refs=(f"source:{record_id}",),
        recorded_at=T0,
        effective_from=T0,
        effective_to=None,
        authority_from=T0,
        authority_to=None,
        superseded_at=None,
        lifecycle_status=lifecycle_status,
    )


def test_node_and_edge_shapes_are_mutually_exclusive() -> None:
    node = _node("n1")
    edge = _edge("e1")

    assert node.node_type == TemporalGraphNodeType.OBSERVATION
    assert node.edge_type is None
    assert edge.edge_type == TemporalGraphEdgeType.SUPPORTS
    assert edge.node_type is None

    with pytest.raises(ValidationError, match="node records cannot declare edge_type"):
        TemporalGraphRecord(
            **{
                **node.model_dump(),
                "edge_type": TemporalGraphEdgeType.SUPPORTS,
            }
        )


def test_edges_require_distinct_source_and_target() -> None:
    edge = _edge("e1")

    with pytest.raises(ValidationError, match="edge records require source_record_id"):
        TemporalGraphRecord(
            **{
                **edge.model_dump(),
                "source_record_id": None,
            }
        )

    with pytest.raises(ValidationError, match="self-referential graph edges"):
        TemporalGraphRecord(
            **{
                **edge.model_dump(),
                "target_record_id": "n1",
            }
        )


def test_candidate_causation_cannot_be_authoritative_by_assertion() -> None:
    with pytest.raises(ValidationError, match="candidate_cause_of cannot be authoritative"):
        _edge(
            "candidate-cause",
            edge_type=TemporalGraphEdgeType.CANDIDATE_CAUSE_OF,
            lifecycle_status=TemporalGraphLifecycleStatus.ACTIVE,
        )

    qualified = _edge(
        "qualified-cause",
        edge_type=TemporalGraphEdgeType.CANDIDATE_CAUSE_OF,
        lifecycle_status=TemporalGraphLifecycleStatus.QUALIFIED,
    )
    assert qualified.lifecycle_status == TemporalGraphLifecycleStatus.QUALIFIED


def test_unknown_effective_time_is_preserved_not_invented() -> None:
    unknown = _node("unknown-effective", effective_from=None)
    snapshot = TemporalGraphStore([unknown]).query(as_of=T2, known_at=T2)

    assert snapshot.known_record_ids == ("unknown-effective",)
    assert snapshot.effective_record_ids == ()
    assert snapshot.authoritative_record_ids == ()
    assert snapshot.unknown_effective_record_ids == ("unknown-effective",)


def test_as_of_and_known_at_can_legitimately_return_different_answers() -> None:
    retroactive = _node(
        "retroactive",
        recorded_at=T2,
        effective_from=T0,
        authority_from=T2,
    )
    store = TemporalGraphStore([retroactive])

    not_yet_known = store.query(as_of=T1, known_at=T1)
    later_known = store.query(as_of=T1, known_at=T3)

    assert not_yet_known.known_record_ids == ()
    assert not_yet_known.effective_record_ids == ()
    assert later_known.known_record_ids == ("retroactive",)
    assert later_known.effective_record_ids == ("retroactive",)
    assert later_known.authoritative_record_ids == ("retroactive",)


def test_authority_window_is_independent_from_effective_and_known_time() -> None:
    record = _node(
        "authority-window",
        recorded_at=T0,
        effective_from=T0,
        authority_from=T1,
        authority_to=T3,
    )
    store = TemporalGraphStore([record])

    before = store.query(as_of=T2, known_at=T2, authority_at=T0)
    during = store.query(as_of=T2, known_at=T2, authority_at=T2)
    after = store.query(as_of=T2, known_at=T3, authority_at=T3)

    assert before.effective_record_ids == ("authority-window",)
    assert before.authoritative_record_ids == ()
    assert during.authoritative_record_ids == ("authority-window",)
    assert after.authoritative_record_ids == ()


def test_superseded_record_remains_historically_authoritative_before_terminal_time() -> None:
    old = _node(
        "old",
        lifecycle_status=TemporalGraphLifecycleStatus.SUPERSEDED,
        authority_from=T0,
        authority_to=T2,
        superseded_at=T2,
    )
    new = _node(
        "new",
        recorded_at=T2,
        effective_from=T2,
        authority_from=T2,
    )
    store = TemporalGraphStore([old, new])

    historical = store.query(as_of=T1, known_at=T3, authority_at=T1)
    current = store.query(as_of=T3, known_at=T3, authority_at=T3)

    assert historical.authoritative_record_ids == ("old",)
    assert "old" in historical.known_record_ids
    assert current.authoritative_record_ids == ("new",)
    assert "old" in current.known_record_ids


def test_cross_namespace_promotion_requires_governed_evidence_and_target_namespace() -> None:
    promotion = TemporalGraphPromotion(
        source_namespace="project:golden-nibiru",
        target_namespace="project:enki",
        reconciliation_ref="recon-1",
        authority_decision_ref="authority-1",
    )
    promoted = _node("promoted", namespace="project:enki", promotion=promotion)
    assert promoted.promotion == promotion

    with pytest.raises(ValidationError, match="promoted record must be written in the target namespace"):
        _node("wrong-target", namespace="project:other", promotion=promotion)

    with pytest.raises(ValidationError, match="promotion must cross namespaces"):
        TemporalGraphPromotion(
            source_namespace="project:enki",
            target_namespace="project:enki",
            reconciliation_ref="recon-2",
            authority_decision_ref="authority-2",
        )


def test_duplicate_identifiers_and_duplicate_provenance_fail_closed() -> None:
    n1 = _node("n1")

    with pytest.raises(ValueError, match="graph_record_id values must be unique"):
        TemporalGraphStore([n1, n1])

    with pytest.raises(ValidationError, match="provenance_refs must contain unique values"):
        TemporalGraphRecord(
            **{
                **n1.model_dump(),
                "provenance_refs": ("source:n1", "source:n1"),
            }
        )


def test_store_and_snapshot_hashes_are_deterministic_across_input_order() -> None:
    n1 = _node("n1")
    n2 = _node("n2", recorded_at=T1)
    first = TemporalGraphStore([n1, n2])
    second = TemporalGraphStore([n2, n1])

    first_snapshot = first.query(as_of=T2, known_at=T2)
    second_snapshot = second.query(as_of=T2, known_at=T2)

    assert first.store_hash == second.store_hash
    assert first_snapshot.snapshot_hash == second_snapshot.snapshot_hash

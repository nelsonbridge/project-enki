from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from nks.enki.cognitive_lineage import (
    CognitiveLineage,
    CognitiveLineageEntry,
    CognitiveLineageLink,
    CognitiveStance,
)
from nks.enki.temporal_graph import (
    TemporalGraphEdgeType,
    TemporalGraphNodeType,
)


T0 = datetime(2026, 8, 16, 20, 0, tzinfo=timezone.utc)
T1 = datetime(2026, 8, 16, 21, 0, tzinfo=timezone.utc)
T2 = datetime(2026, 8, 16, 22, 0, tzinfo=timezone.utc)
T3 = datetime(2026, 8, 16, 23, 0, tzinfo=timezone.utc)
T4 = datetime(2026, 8, 17, 0, 0, tzinfo=timezone.utc)


def _entry(
    entry_id: str,
    *,
    node_type: TemporalGraphNodeType = TemporalGraphNodeType.HYPOTHESIS,
    stance: CognitiveStance = CognitiveStance.CONSIDERED,
    recorded_at: datetime = T0,
    effective_from: datetime | None = T0,
    effective_to: datetime | None = None,
    context_ids: tuple[str, ...] = ("ctx:project-enki-design",),
    revises_entry_ids: tuple[str, ...] = (),
    supersedes_entry_ids: tuple[str, ...] = (),
    superseded_at: datetime | None = None,
    subject_id: str = "subject:origin-authority",
) -> CognitiveLineageEntry:
    return CognitiveLineageEntry(
        entry_id=entry_id,
        subject_id=subject_id,
        node_type=node_type,
        stance=stance,
        domain_id="domain:project-enki-architecture",
        context_ids=context_ids,
        content={"text": entry_id},
        provenance_refs=(f"conversation:{entry_id}",),
        recorded_at=recorded_at,
        effective_from=effective_from,
        effective_to=effective_to,
        revises_entry_ids=revises_entry_ids,
        supersedes_entry_ids=supersedes_entry_ids,
        superseded_at=superseded_at,
    )


def _link(
    link_id: str,
    source: str,
    target: str,
    edge_type: TemporalGraphEdgeType,
    *,
    recorded_at: datetime = T0,
    effective_from: datetime | None = T0,
) -> CognitiveLineageLink:
    return CognitiveLineageLink(
        link_id=link_id,
        subject_id="subject:origin-authority",
        edge_type=edge_type,
        source_entry_id=source,
        target_entry_id=target,
        domain_id="domain:project-enki-architecture",
        context_ids=("ctx:project-enki-design",),
        provenance_refs=(f"conversation:{link_id}",),
        recorded_at=recorded_at,
        effective_from=effective_from,
    )


def test_considered_thought_is_not_authority_or_current_belief() -> None:
    entry = _entry("idea:one", stance=CognitiveStance.CONSIDERED)
    graph_record = entry.to_graph_record()

    assert graph_record.metadata["cognitive_stance"] == "considered"
    assert graph_record.authority_from is None
    assert graph_record.authority_state_ref is None
    assert graph_record.metadata["identity_inference_authorized"] is False
    assert graph_record.metadata["stable_identity_inference_authorized"] is False
    assert graph_record.metadata["person_object_inference_authorized"] is False
    assert graph_record.is_authoritative_at(T1) is False


def test_subject_acceptance_still_does_not_manufacture_project_enki_authority() -> None:
    accepted = _entry("idea:accepted", stance=CognitiveStance.ACCEPTED)
    graph_record = accepted.to_graph_record()

    assert graph_record.lifecycle_status.value == "active"
    assert graph_record.authority_from is None
    assert graph_record.is_authoritative_at(T1) is False


def test_abandoned_hypothesis_remains_historical_record() -> None:
    abandoned = _entry("idea:abandoned", stance=CognitiveStance.ABANDONED)
    lineage = CognitiveLineage([abandoned])

    snapshot = lineage.snapshot(as_of=T1, known_at=T1)

    assert snapshot.entry_ids_by_stance["abandoned"] == ("idea:abandoned",)
    assert "idea:abandoned" in lineage.store.query(
        as_of=T1,
        known_at=T1,
    ).known_record_ids


def test_context_qualification_is_preserved_without_generalization() -> None:
    qualified = _entry(
        "idea:qualified",
        stance=CognitiveStance.QUALIFIED,
        context_ids=("ctx:project-enki", "ctx:temporal-graph"),
    )

    record = qualified.to_graph_record()

    assert record.context_ids == ("ctx:project-enki", "ctx:temporal-graph")
    assert record.graph_namespace == "cognitive:subject:origin-authority"
    assert record.metadata["authority_scope"] == "subject-local-cognitive"


def test_bounded_real_design_lineage_can_represent_reasoning_chain() -> None:
    observation = _entry(
        "cog:obs:map-evolving-thought",
        node_type=TemporalGraphNodeType.OBSERVATION,
        stance=CognitiveStance.ACCEPTED,
        recorded_at=T0,
    )
    question = _entry(
        "cog:q:shared-grammar",
        node_type=TemporalGraphNodeType.QUESTION,
        stance=CognitiveStance.UNRESOLVED,
        recorded_at=T0,
    )
    hypothesis = _entry(
        "cog:h:federated-grammar",
        node_type=TemporalGraphNodeType.HYPOTHESIS,
        stance=CognitiveStance.SUSPECTED,
        recorded_at=T1,
    )
    evidence = _entry(
        "cog:e:temporal-authority-existing",
        node_type=TemporalGraphNodeType.EVIDENCE,
        stance=CognitiveStance.ACCEPTED,
        recorded_at=T1,
    )
    interpretation = _entry(
        "cog:i:federate-not-collapse",
        node_type=TemporalGraphNodeType.INTERPRETATION,
        stance=CognitiveStance.QUALIFIED,
        recorded_at=T2,
    )
    decision = _entry(
        "cog:d:one-grammar-many-namespaces",
        node_type=TemporalGraphNodeType.DECISION,
        stance=CognitiveStance.ACCEPTED,
        recorded_at=T2,
    )
    outcome = _entry(
        "cog:o:project-enki-temporal-runtime",
        node_type=TemporalGraphNodeType.OUTCOME,
        stance=CognitiveStance.ACCEPTED,
        recorded_at=T3,
    )

    links = [
        _link(
            "edge:obs-q",
            observation.entry_id,
            question.entry_id,
            TemporalGraphEdgeType.INFORMS,
        ),
        _link(
            "edge:q-h",
            question.entry_id,
            hypothesis.entry_id,
            TemporalGraphEdgeType.INFORMS,
            recorded_at=T1,
        ),
        _link(
            "edge:e-h",
            evidence.entry_id,
            hypothesis.entry_id,
            TemporalGraphEdgeType.SUPPORTS,
            recorded_at=T1,
        ),
        _link(
            "edge:h-i",
            hypothesis.entry_id,
            interpretation.entry_id,
            TemporalGraphEdgeType.INFORMS,
            recorded_at=T2,
        ),
        _link(
            "edge:i-d",
            interpretation.entry_id,
            decision.entry_id,
            TemporalGraphEdgeType.DECIDED_FROM,
            recorded_at=T2,
        ),
        _link(
            "edge:d-o",
            decision.entry_id,
            outcome.entry_id,
            TemporalGraphEdgeType.RESULTED_IN,
            recorded_at=T3,
        ),
    ]

    lineage = CognitiveLineage(
        [
            observation,
            question,
            hypothesis,
            evidence,
            interpretation,
            decision,
            outcome,
        ],
        links,
    )

    snapshot = lineage.snapshot(as_of=T3, known_at=T3)
    assert snapshot.entry_ids_by_stance["suspected"] == (
        "cog:h:federated-grammar",
    )
    assert snapshot.entry_ids_by_stance["qualified"] == (
        "cog:i:federate-not-collapse",
    )
    assert set(snapshot.entry_ids_by_stance["accepted"]) == {
        "cog:d:one-grammar-many-namespaces",
        "cog:e:temporal-authority-existing",
        "cog:o:project-enki-temporal-runtime",
        "cog:obs:map-evolving-thought",
    }
    assert snapshot.unresolved_entry_ids == ("cog:q:shared-grammar",)


def test_same_as_of_can_differ_by_known_at_without_rewriting_thought_history() -> None:
    initial = _entry(
        "idea:initial",
        stance=CognitiveStance.SUSPECTED,
        recorded_at=T0,
        effective_from=T0,
    )
    later_recorded_revision = _entry(
        "idea:retroactive-revision",
        stance=CognitiveStance.QUALIFIED,
        recorded_at=T2,
        effective_from=T1,
        revises_entry_ids=("idea:initial",),
    )
    lineage = CognitiveLineage([initial, later_recorded_revision])

    before_project_enki_knew = lineage.snapshot(as_of=T1, known_at=T1)
    after_project_enki_knew = lineage.snapshot(as_of=T1, known_at=T3)

    assert "idea:retroactive-revision" not in {
        item
        for ids in before_project_enki_knew.entry_ids_by_stance.values()
        for item in ids
    }
    assert after_project_enki_knew.entry_ids_by_stance["qualified"] == (
        "idea:retroactive-revision",
    )


def test_future_effective_thought_is_known_but_not_yet_in_as_of_snapshot() -> None:
    future = _entry(
        "idea:future-effective",
        stance=CognitiveStance.CONSIDERED,
        recorded_at=T0,
        effective_from=T3,
    )
    lineage = CognitiveLineage([future])

    before_effective = lineage.snapshot(as_of=T2, known_at=T2)
    after_effective = lineage.snapshot(as_of=T4, known_at=T4)

    assert "considered" not in before_effective.entry_ids_by_stance
    assert after_effective.entry_ids_by_stance["considered"] == (
        "idea:future-effective",
    )


def test_unknown_effective_time_is_visible_without_time_imputation() -> None:
    unknown = _entry(
        "idea:unknown-effective",
        stance=CognitiveStance.CONSIDERED,
        effective_from=None,
    )
    lineage = CognitiveLineage([unknown])

    snapshot = lineage.snapshot(as_of=T3, known_at=T3)

    assert "considered" not in snapshot.entry_ids_by_stance
    assert snapshot.unknown_effective_time_entry_ids == ("idea:unknown-effective",)


def test_superseded_thought_requires_explicit_terminal_time() -> None:
    with pytest.raises(ValidationError, match="superseded cognitive stance requires"):
        _entry("idea:superseded", stance=CognitiveStance.SUPERSEDED)


def test_revision_reference_must_exist_and_cycles_fail_closed() -> None:
    dangling = _entry("idea:dangling", revises_entry_ids=("idea:missing",))
    with pytest.raises(ValueError, match="refs must exist"):
        CognitiveLineage([dangling])

    first = _entry("idea:first", revises_entry_ids=("idea:second",))
    second = _entry("idea:second", revises_entry_ids=("idea:first",))
    with pytest.raises(ValueError, match="revision cycle"):
        CognitiveLineage([first, second])


def test_lineage_cannot_mix_subjects_or_cross_subject_links() -> None:
    first = _entry("idea:first")
    second = _entry("idea:second", subject_id="subject:other")

    with pytest.raises(ValueError, match="cannot mix subjects"):
        CognitiveLineage([first, second])


def test_lineage_hash_is_deterministic_across_input_order() -> None:
    first = _entry("idea:first")
    second = _entry("idea:second", recorded_at=T1)
    link = _link(
        "edge:first-second",
        first.entry_id,
        second.entry_id,
        TemporalGraphEdgeType.INFORMS,
        recorded_at=T1,
    )

    a = CognitiveLineage([first, second], [link])
    b = CognitiveLineage([second, first], [link])

    assert a.lineage_hash == b.lineage_hash
    assert (
        a.snapshot(as_of=T2, known_at=T2).snapshot_hash
        == b.snapshot(as_of=T2, known_at=T2).snapshot_hash
    )

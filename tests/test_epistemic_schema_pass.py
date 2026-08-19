from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from nks.enki.contracts import (
    ConfidenceAssertion,
    ConfidenceLevel,
    ExpressionOrigin,
    SubjectRef,
)
from nks.enki.epistemic_records import (
    AssertionOccurrence,
    ConflictClass,
    ConflictClassificationStatus,
    ConflictMemberRef,
    ConflictRecord,
    CoverageDisposition,
    DerivationAttempt,
    DerivationAttemptStatus,
    DerivationBatch,
    DerivationCoverageItem,
    DerivationCoverageStatus,
    DerivationExecutionStatus,
    EpistemicTransition,
    EpistemicTransitionKind,
    GovernedRegistryRecord,
    Proposition,
    PropositionResolutionStatus,
    RegistryKind,
    RegistryLifecycleStatus,
)
from nks.enki.transitions import ConflictKind, StateTransition, TransitionPayload


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"
NOW = datetime(2026, 8, 18, 23, 0, tzinfo=timezone.utc)


def _subject() -> SubjectRef:
    return SubjectRef(subject_id="PERSON-1", subject_type="PERSON", namespace="person")


def _confidence() -> ConfidenceAssertion:
    return ConfidenceAssertion(
        level=ConfidenceLevel.MODERATE,
        rationale="Attributed source assertion pending broader reconciliation.",
        evidence_ids=["E-1"],
    )


def test_occurrence_identity_is_separate_from_proposition_identity() -> None:
    proposition = Proposition(
        proposition_id="PROP-1",
        subject=_subject(),
        claim_domain="employment_history",
        claim_type="employment.role_title",
        predicate="served_as",
        value="Director",
        resolution_status=PropositionResolutionStatus.CANDIDATE,
        recorded_at=NOW,
    )
    first = AssertionOccurrence(
        assertion_occurrence_id="AO-1",
        subject=_subject(),
        proposition_ref=proposition.proposition_id,
        claim_domain=proposition.claim_domain,
        claim_type=proposition.claim_type,
        statement="Director",
        evidence_ids=("E-1",),
        derivation_batch_ref="DB-1",
        expression_origin=ExpressionOrigin.OBSERVED,
        confidence=_confidence(),
        recorded_at=NOW,
        provenance_refs=("PROV-1",),
    )
    second = first.model_copy(
        update={
            "assertion_occurrence_id": "AO-2",
            "statement": "Director of Enterprise Support",
            "provenance_refs": ("PROV-2",),
        }
    )

    assert first.assertion_occurrence_id != second.assertion_occurrence_id
    assert first.proposition_ref == second.proposition_ref == "PROP-1"


def test_proposition_resolution_does_not_rewrite_occurrence() -> None:
    occurrence = AssertionOccurrence(
        assertion_occurrence_id="AO-1",
        subject=_subject(),
        proposition_ref="PROP-CANDIDATE",
        claim_domain="employment_history",
        claim_type="employment.role_title",
        statement="Director",
        evidence_ids=("E-1",),
        expression_origin=ExpressionOrigin.OBSERVED,
        confidence=_confidence(),
        recorded_at=NOW,
        provenance_refs=("PROV-1",),
    )
    resolved = Proposition(
        proposition_id="PROP-RESOLVED",
        subject=_subject(),
        claim_domain="employment_history",
        claim_type="employment.role_title",
        predicate="served_as",
        value="Director of Enterprise Support",
        resolution_status=PropositionResolutionStatus.RESOLVED,
        recorded_at=NOW + timedelta(minutes=1),
        supersedes_refs=("PROP-CANDIDATE",),
    )

    assert resolved.supersedes_refs == ("PROP-CANDIDATE",)
    assert occurrence.proposition_ref == "PROP-CANDIDATE"
    with pytest.raises(ValidationError):
        occurrence.proposition_ref = "PROP-RESOLVED"


def test_detected_conflict_does_not_require_premature_classification() -> None:
    conflict = ConflictRecord(
        conflict_id="CF-1",
        conflict_class=ConflictClass.SEMANTIC,
        detection_kind="INCOMPATIBLE_VALUES",
        members=(
            ConflictMemberRef(ref_kind="PROPOSITION", ref_id="P-1"),
            ConflictMemberRef(ref_kind="PROPOSITION", ref_id="P-2"),
        ),
        classification_status=ConflictClassificationStatus.DETECTED,
        subject=_subject(),
        claim_domain="compensation_economics",
        provenance_refs=("PROV-1",),
        detected_at=NOW,
    )

    assert conflict.classification is None
    assert conflict.classification_status == ConflictClassificationStatus.DETECTED


def test_confirmed_conflict_requires_classification_lineage() -> None:
    with pytest.raises(ValidationError, match="classification and classified_at"):
        ConflictRecord(
            conflict_id="CF-1",
            conflict_class=ConflictClass.SEMANTIC,
            detection_kind="INCOMPATIBLE_VALUES",
            members=(
                ConflictMemberRef(ref_kind="PROPOSITION", ref_id="P-1"),
                ConflictMemberRef(ref_kind="PROPOSITION", ref_id="P-2"),
            ),
            classification_status=ConflictClassificationStatus.CONFIRMED,
            provenance_refs=("PROV-1",),
            detected_at=NOW,
        )


def _attempt() -> DerivationAttempt:
    return DerivationAttempt(
        attempt_id="ATT-1",
        ordinal=1,
        status=DerivationAttemptStatus.SUCCEEDED,
        started_at=NOW,
        completed_at=NOW + timedelta(seconds=5),
        execution_ref="RUN-1",
    )


def test_derivation_execution_and_coverage_are_independent() -> None:
    batch = DerivationBatch(
        derivation_batch_id="DB-1",
        input_refs=("SNAPSHOT-1",),
        derivation_profile_ref="REG-DERIVE-1",
        attempts=(_attempt(),),
        declared_scope=("employment_history", "compensation_economics"),
        coverage_manifest=(
            DerivationCoverageItem(
                scope_ref="employment_history",
                disposition=CoverageDisposition.COMPLETE,
            ),
            DerivationCoverageItem(
                scope_ref="compensation_economics",
                disposition=CoverageDisposition.PARTIAL,
                limitation_refs=("LIMIT-1",),
            ),
        ),
        execution_status=DerivationExecutionStatus.SUCCEEDED,
        coverage_status=DerivationCoverageStatus.PARTIAL,
        assertion_manifest=("AO-1",),
        started_at=NOW,
        completed_at=NOW + timedelta(seconds=5),
        provenance_refs=("PROV-1",),
    )

    assert batch.execution_status == DerivationExecutionStatus.SUCCEEDED
    assert batch.coverage_status == DerivationCoverageStatus.PARTIAL


def test_complete_coverage_can_legitimately_produce_zero_assertions() -> None:
    batch = DerivationBatch(
        derivation_batch_id="DB-EMPTY",
        input_refs=("SNAPSHOT-1",),
        derivation_profile_ref="REG-DERIVE-1",
        attempts=(_attempt(),),
        declared_scope=("compensation_economics",),
        coverage_manifest=(
            DerivationCoverageItem(
                scope_ref="compensation_economics",
                disposition=CoverageDisposition.COMPLETE,
            ),
        ),
        execution_status=DerivationExecutionStatus.SUCCEEDED,
        coverage_status=DerivationCoverageStatus.COMPLETE,
        assertion_manifest=(),
        started_at=NOW,
        completed_at=NOW + timedelta(seconds=5),
        provenance_refs=("PROV-1",),
    )

    assert batch.assertion_manifest == ()
    assert batch.coverage_status == DerivationCoverageStatus.COMPLETE


def test_complete_coverage_rejects_partial_scope() -> None:
    with pytest.raises(ValidationError, match="every declared scope"):
        DerivationBatch(
            derivation_batch_id="DB-BAD",
            input_refs=("SNAPSHOT-1",),
            derivation_profile_ref="REG-DERIVE-1",
            attempts=(_attempt(),),
            declared_scope=("employment_history",),
            coverage_manifest=(
                DerivationCoverageItem(
                    scope_ref="employment_history",
                    disposition=CoverageDisposition.PARTIAL,
                ),
            ),
            execution_status=DerivationExecutionStatus.SUCCEEDED,
            coverage_status=DerivationCoverageStatus.COMPLETE,
            started_at=NOW,
            completed_at=NOW + timedelta(seconds=5),
            provenance_refs=("PROV-1",),
        )


def test_active_registry_record_requires_temporal_authority() -> None:
    with pytest.raises(ValidationError, match="authority_from"):
        GovernedRegistryRecord(
            registry_record_id="REG-TAX-1",
            registry_kind=RegistryKind.TAXONOMY_TERM,
            namespace="enki.claim-domain",
            version="1",
            definition={"term": "employment_history"},
            recorded_at=NOW,
            lifecycle_status=RegistryLifecycleStatus.ACTIVE,
            provenance_refs=("PROV-1",),
        )


def test_registry_record_preserves_effective_and_authority_time_separately() -> None:
    record = GovernedRegistryRecord(
        registry_record_id="REG-TAX-1",
        registry_kind=RegistryKind.TAXONOMY_TERM,
        namespace="enki.claim-domain",
        version="1",
        definition={"term": "employment_history"},
        recorded_at=NOW,
        effective_from=NOW - timedelta(days=1),
        authority_from=NOW,
        lifecycle_status=RegistryLifecycleStatus.ACTIVE,
        authority_ref="ADR-0003",
        provenance_refs=("PROV-1",),
    )

    assert record.effective_from != record.authority_from


def test_epistemic_transition_can_increase_uncertainty_without_state_replacement() -> None:
    transition = EpistemicTransition(
        epistemic_transition_id="ET-1",
        transition_kind=EpistemicTransitionKind.UNCERTAINTY_CHANGE,
        subject=_subject(),
        claim_domain="employment_history",
        from_refs=("PROP-1",),
        transition_event_ref="EVIDENCE-NEW-1",
        preserved=("prior source remains historically attributable",),
        remaining_uncertainty=("role boundary remains unresolved",),
        next_required_evidence=("contemporaneous organization record",),
        provenance_refs=("PROV-1",),
        occurred_at=NOW,
        recorded_at=NOW + timedelta(minutes=1),
    )

    assert transition.remaining_uncertainty
    assert transition.next_required_evidence


def test_state_transition_compatibility_alias_and_legacy_collision_value() -> None:
    assert TransitionPayload is StateTransition
    assert ConflictKind("CONTRADICTION") is ConflictKind.TARGET_STATE_ID_COLLISION
    assert ConflictKind.CONTRADICTION is ConflictKind.TARGET_STATE_ID_COLLISION
    assert ConflictKind.CONTRADICTION.value == "TARGET_STATE_ID_COLLISION"


@pytest.mark.parametrize(
    "schema_name",
    [
        "assertion-occurrence.schema.json",
        "proposition.schema.json",
        "conflict-record.schema.json",
        "derivation-batch.schema.json",
        "governed-registry-record.schema.json",
        "epistemic-transition.schema.json",
        "state-transition.schema.json",
    ],
)
def test_new_schemas_are_valid_draft_2020_12(schema_name: str) -> None:
    schema = json.loads((SCHEMA_DIR / schema_name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)


def test_core_runtime_records_validate_against_boundary_schemas() -> None:
    proposition = Proposition(
        proposition_id="PROP-1",
        subject=_subject(),
        claim_domain="employment_history",
        claim_type="employment.role_title",
        predicate="served_as",
        value="Director",
        resolution_status=PropositionResolutionStatus.CANDIDATE,
        recorded_at=NOW,
    )
    occurrence = AssertionOccurrence(
        assertion_occurrence_id="AO-1",
        subject=_subject(),
        proposition_ref="PROP-1",
        claim_domain="employment_history",
        claim_type="employment.role_title",
        statement="Director",
        evidence_ids=("E-1",),
        expression_origin=ExpressionOrigin.OBSERVED,
        confidence=_confidence(),
        recorded_at=NOW,
        provenance_refs=("PROV-1",),
    )
    conflict = ConflictRecord(
        conflict_id="CF-1",
        conflict_class=ConflictClass.SEMANTIC,
        detection_kind="INCOMPATIBLE_VALUES",
        members=(
            ConflictMemberRef(ref_kind="PROPOSITION", ref_id="P-1"),
            ConflictMemberRef(ref_kind="PROPOSITION", ref_id="P-2"),
        ),
        classification_status=ConflictClassificationStatus.DETECTED,
        provenance_refs=("PROV-1",),
        detected_at=NOW,
    )
    batch = DerivationBatch(
        derivation_batch_id="DB-1",
        input_refs=("SNAPSHOT-1",),
        derivation_profile_ref="REG-DERIVE-1",
        attempts=(_attempt(),),
        declared_scope=("employment_history",),
        coverage_manifest=(
            DerivationCoverageItem(
                scope_ref="employment_history",
                disposition=CoverageDisposition.COMPLETE,
            ),
        ),
        execution_status=DerivationExecutionStatus.SUCCEEDED,
        coverage_status=DerivationCoverageStatus.COMPLETE,
        assertion_manifest=("AO-1",),
        started_at=NOW,
        completed_at=NOW + timedelta(seconds=5),
        provenance_refs=("PROV-1",),
    )
    registry = GovernedRegistryRecord(
        registry_record_id="REG-TAX-1",
        registry_kind=RegistryKind.TAXONOMY_TERM,
        namespace="enki.claim-domain",
        version="1",
        definition={"term": "employment_history"},
        recorded_at=NOW,
        authority_from=NOW,
        lifecycle_status=RegistryLifecycleStatus.ACTIVE,
        provenance_refs=("PROV-1",),
    )
    epistemic = EpistemicTransition(
        epistemic_transition_id="ET-1",
        transition_kind=EpistemicTransitionKind.FIRST_RECOGNITION,
        subject=_subject(),
        claim_domain="employment_history",
        transition_event_ref="EVENT-1",
        newly_visible=("role overlap candidate",),
        provenance_refs=("PROV-1",),
        occurred_at=NOW,
        recorded_at=NOW,
    )

    cases = [
        ("proposition.schema.json", proposition),
        ("assertion-occurrence.schema.json", occurrence),
        ("conflict-record.schema.json", conflict),
        ("derivation-batch.schema.json", batch),
        ("governed-registry-record.schema.json", registry),
        ("epistemic-transition.schema.json", epistemic),
    ]
    for schema_name, record in cases:
        schema = json.loads((SCHEMA_DIR / schema_name).read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(record.model_dump(mode="json"))

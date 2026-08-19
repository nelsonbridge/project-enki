"""Portable epistemic records for assertions, propositions, conflicts, derivation, registries, and epistemic lineage."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.enki.contracts import ConfidenceAssertion, ExpressionOrigin, SubjectRef


class PropositionResolutionStatus(StrEnum):
    CANDIDATE = "CANDIDATE"
    RESOLVED = "RESOLVED"
    QUALIFIED = "QUALIFIED"
    SUPERSEDED = "SUPERSEDED"
    RETIRED = "RETIRED"


class PropositionParticipant(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    role: str = Field(min_length=1)
    ref_kind: str = Field(min_length=1)
    ref_id: str = Field(min_length=1)
    namespace: str | None = None


class PropositionTemporalScope(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    effective_from: datetime | None = None
    effective_to: datetime | None = None

    @model_validator(mode="after")
    def validate_window(self) -> "PropositionTemporalScope":
        if (
            self.effective_from is not None
            and self.effective_to is not None
            and self.effective_to < self.effective_from
        ):
            raise ValueError("effective_to cannot precede effective_from")
        return self


class Proposition(BaseModel):
    """A candidate or resolved semantic proposition independent of assertion occurrence identity."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    proposition_id: str = Field(min_length=1)
    subject: SubjectRef
    claim_domain: str = Field(min_length=1)
    claim_type: str = Field(min_length=1)
    predicate: str = Field(min_length=1)
    value: Any = None
    participants: tuple[PropositionParticipant, ...] = ()
    temporal_scope: PropositionTemporalScope | None = None
    context: tuple[str, ...] = ()
    qualifiers: dict[str, Any] = Field(default_factory=dict)
    resolution_status: PropositionResolutionStatus
    recorded_at: datetime
    supersedes_refs: tuple[str, ...] = ()
    revises_refs: tuple[str, ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_lineage(self) -> "Proposition":
        if self.proposition_id in self.supersedes_refs:
            raise ValueError("a proposition cannot supersede itself")
        if self.proposition_id in self.revises_refs:
            raise ValueError("a proposition cannot revise itself")
        for name, values in (
            ("context", self.context),
            ("supersedes_refs", self.supersedes_refs),
            ("revises_refs", self.revises_refs),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{name} must contain unique values")
        return self


class AssertionOccurrence(BaseModel):
    """Immutable record of one attributable assertion event.

    Semantic resolution may later merge, split, revise, or supersede propositions. The
    occurrence remains unchanged and continues to point at the proposition reference
    assigned when the occurrence was recorded.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    assertion_occurrence_id: str = Field(min_length=1)
    subject: SubjectRef
    proposition_ref: str = Field(min_length=1)
    claim_domain: str = Field(min_length=1)
    claim_type: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    evidence_ids: tuple[str, ...] = ()
    derivation_batch_ref: str | None = None
    expression_origin: ExpressionOrigin
    confidence: ConfidenceAssertion
    source_asserted_at: datetime | None = None
    recorded_at: datetime
    context: tuple[str, ...] = ()
    provenance_refs: tuple[str, ...] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_unique_refs(self) -> "AssertionOccurrence":
        for name, values in (
            ("evidence_ids", self.evidence_ids),
            ("context", self.context),
            ("provenance_refs", self.provenance_refs),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{name} must contain unique values")
        return self


class ConflictClass(StrEnum):
    INTEGRITY = "INTEGRITY"
    SEMANTIC = "SEMANTIC"
    TEMPORAL = "TEMPORAL"
    AUTHORITY = "AUTHORITY"
    IDENTITY_RESOLUTION = "IDENTITY_RESOLUTION"
    COVERAGE = "COVERAGE"
    INTERPRETIVE = "INTERPRETIVE"


class ConflictClassificationStatus(StrEnum):
    DETECTED = "DETECTED"
    CANDIDATE = "CANDIDATE"
    CONFIRMED = "CONFIRMED"
    QUALIFIED = "QUALIFIED"
    DISMISSED = "DISMISSED"
    UNRESOLVED = "UNRESOLVED"
    SUPERSEDED = "SUPERSEDED"


class ConflictMemberRef(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    ref_kind: str = Field(min_length=1)
    ref_id: str = Field(min_length=1)
    role: str | None = None


class ConflictRecord(BaseModel):
    """Governed conflict candidate/classification independent of state-integrity failures."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    conflict_id: str = Field(min_length=1)
    conflict_class: ConflictClass
    detection_kind: str = Field(min_length=1)
    members: tuple[ConflictMemberRef, ...] = Field(min_length=2)
    classification_status: ConflictClassificationStatus
    classification: str | None = None
    subject: SubjectRef | None = None
    claim_domain: str | None = None
    context: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    provenance_refs: tuple[str, ...] = Field(min_length=1)
    detected_at: datetime
    classified_at: datetime | None = None
    authority_policy_ref: str | None = None
    transition_ref: str | None = None
    supersedes_ref: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_classification_lifecycle(self) -> "ConflictRecord":
        unique_members = {(item.ref_kind, item.ref_id, item.role) for item in self.members}
        if len(unique_members) != len(self.members):
            raise ValueError("conflict members must be unique")
        terminal_classification = {
            ConflictClassificationStatus.CONFIRMED,
            ConflictClassificationStatus.QUALIFIED,
            ConflictClassificationStatus.DISMISSED,
            ConflictClassificationStatus.SUPERSEDED,
        }
        if self.classification_status in terminal_classification:
            if not self.classification or self.classified_at is None:
                raise ValueError(
                    "classified conflict states require classification and classified_at"
                )
        if self.classified_at is not None and self.classified_at < self.detected_at:
            raise ValueError("classified_at cannot precede detected_at")
        for name, values in (
            ("context", self.context),
            ("evidence_ids", self.evidence_ids),
            ("provenance_refs", self.provenance_refs),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{name} must contain unique values")
        return self


class DerivationExecutionStatus(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class DerivationAttemptStatus(StrEnum):
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class CoverageDisposition(StrEnum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    NOT_DUE = "NOT_DUE"
    UNKNOWN = "UNKNOWN"


class DerivationCoverageStatus(StrEnum):
    NOT_ASSESSED = "NOT_ASSESSED"
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


class DerivationAttempt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    attempt_id: str = Field(min_length=1)
    ordinal: int = Field(ge=1)
    status: DerivationAttemptStatus
    started_at: datetime
    completed_at: datetime | None = None
    execution_ref: str | None = None
    limitation_refs: tuple[str, ...] = ()
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_attempt(self) -> "DerivationAttempt":
        if self.status != DerivationAttemptStatus.RUNNING and self.completed_at is None:
            raise ValueError("terminal derivation attempt requires completed_at")
        if self.completed_at is not None and self.completed_at < self.started_at:
            raise ValueError("completed_at cannot precede started_at")
        if len(self.limitation_refs) != len(set(self.limitation_refs)):
            raise ValueError("limitation_refs must contain unique values")
        return self


class DerivationCoverageItem(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    scope_ref: str = Field(min_length=1)
    disposition: CoverageDisposition
    limitation_refs: tuple[str, ...] = ()
    notes: str | None = None


class DerivationBatch(BaseModel):
    """One auditable derivation over declared scope with separate execution and coverage state."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    derivation_batch_id: str = Field(min_length=1)
    input_refs: tuple[str, ...] = Field(min_length=1)
    derivation_profile_ref: str = Field(min_length=1)
    attempts: tuple[DerivationAttempt, ...] = Field(min_length=1)
    declared_scope: tuple[str, ...] = Field(min_length=1)
    coverage_manifest: tuple[DerivationCoverageItem, ...] = Field(min_length=1)
    execution_status: DerivationExecutionStatus
    coverage_status: DerivationCoverageStatus
    assertion_manifest: tuple[str, ...] = ()
    started_at: datetime
    completed_at: datetime | None = None
    provenance_refs: tuple[str, ...] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_batch(self) -> "DerivationBatch":
        for name, values in (
            ("input_refs", self.input_refs),
            ("declared_scope", self.declared_scope),
            ("assertion_manifest", self.assertion_manifest),
            ("provenance_refs", self.provenance_refs),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{name} must contain unique values")
        attempt_ids = [item.attempt_id for item in self.attempts]
        attempt_ordinals = [item.ordinal for item in self.attempts]
        if len(attempt_ids) != len(set(attempt_ids)):
            raise ValueError("derivation attempt ids must be unique")
        if len(attempt_ordinals) != len(set(attempt_ordinals)):
            raise ValueError("derivation attempt ordinals must be unique")
        scope_refs = [item.scope_ref for item in self.coverage_manifest]
        if len(scope_refs) != len(set(scope_refs)):
            raise ValueError("coverage scope refs must be unique")
        if set(scope_refs) != set(self.declared_scope):
            raise ValueError("coverage manifest must account for every declared scope exactly once")
        if self.coverage_status == DerivationCoverageStatus.COMPLETE and any(
            item.disposition != CoverageDisposition.COMPLETE
            for item in self.coverage_manifest
        ):
            raise ValueError("COMPLETE coverage requires every declared scope to be COMPLETE")
        terminal = {
            DerivationExecutionStatus.SUCCEEDED,
            DerivationExecutionStatus.PARTIAL,
            DerivationExecutionStatus.FAILED,
        }
        if self.execution_status in terminal and self.completed_at is None:
            raise ValueError("terminal derivation batch requires completed_at")
        if self.completed_at is not None and self.completed_at < self.started_at:
            raise ValueError("completed_at cannot precede started_at")
        return self


class RegistryKind(StrEnum):
    NORMALIZATION_PROFILE = "NORMALIZATION_PROFILE"
    DERIVATION_PROFILE = "DERIVATION_PROFILE"
    TAXONOMY_TERM = "TAXONOMY_TERM"
    SEMANTIC_MAPPING = "SEMANTIC_MAPPING"
    CONFLICT_CLASSIFICATION_RULE = "CONFLICT_CLASSIFICATION_RULE"
    AUTHORITY_POLICY = "AUTHORITY_POLICY"


class RegistryLifecycleStatus(StrEnum):
    CANDIDATE = "CANDIDATE"
    ACTIVE = "ACTIVE"
    QUALIFIED = "QUALIFIED"
    SUPERSEDED = "SUPERSEDED"
    REVOKED = "REVOKED"
    REJECTED = "REJECTED"
    RETIRED = "RETIRED"


class GovernedRegistryRecord(BaseModel):
    """Shared temporal-authority envelope for all governed registry families."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    registry_record_id: str = Field(min_length=1)
    registry_kind: RegistryKind
    namespace: str = Field(min_length=1)
    version: str = Field(min_length=1)
    definition: dict[str, Any]
    recorded_at: datetime
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    authority_from: datetime | None = None
    authority_to: datetime | None = None
    supersedes_ref: str | None = None
    lifecycle_status: RegistryLifecycleStatus
    authority_ref: str | None = None
    provenance_refs: tuple[str, ...] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_temporal_authority(self) -> "GovernedRegistryRecord":
        if (
            self.effective_from is not None
            and self.effective_to is not None
            and self.effective_to < self.effective_from
        ):
            raise ValueError("effective_to cannot precede effective_from")
        if (
            self.authority_from is not None
            and self.authority_to is not None
            and self.authority_to < self.authority_from
        ):
            raise ValueError("authority_to cannot precede authority_from")
        if self.supersedes_ref == self.registry_record_id:
            raise ValueError("a registry record cannot supersede itself")
        if self.lifecycle_status == RegistryLifecycleStatus.ACTIVE and self.authority_from is None:
            raise ValueError("ACTIVE registry record requires authority_from")
        if len(self.provenance_refs) != len(set(self.provenance_refs)):
            raise ValueError("provenance_refs must contain unique values")
        return self


class EpistemicTransitionKind(StrEnum):
    NEW_EVIDENCE = "NEW_EVIDENCE"
    FIRST_RECOGNITION = "FIRST_RECOGNITION"
    CONFLICT_CLASSIFICATION = "CONFLICT_CLASSIFICATION"
    FORECAST_RESOLUTION = "FORECAST_RESOLUTION"
    RETROSPECTIVE_REINTERPRETATION = "RETROSPECTIVE_REINTERPRETATION"
    UNCERTAINTY_CHANGE = "UNCERTAINTY_CHANGE"
    OTHER = "OTHER"


class EpistemicTransition(BaseModel):
    """Lineage event describing what changed in knowledge without requiring state replacement."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    epistemic_transition_id: str = Field(min_length=1)
    transition_kind: EpistemicTransitionKind
    subject: SubjectRef | None = None
    claim_domain: str = Field(min_length=1)
    from_refs: tuple[str, ...] = ()
    transition_event_ref: str = Field(min_length=1)
    newly_visible: tuple[str, ...] = ()
    preserved: tuple[str, ...] = ()
    invalidated_or_reduced: tuple[str, ...] = ()
    remaining_uncertainty: tuple[str, ...] = ()
    next_required_evidence: tuple[str, ...] = ()
    questions_opened: tuple[str, ...] = ()
    questions_closed: tuple[str, ...] = ()
    provenance_refs: tuple[str, ...] = Field(min_length=1)
    authority_ref: str | None = None
    occurred_at: datetime
    recorded_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_epistemic_effect(self) -> "EpistemicTransition":
        effect_sets = (
            self.newly_visible,
            self.invalidated_or_reduced,
            self.remaining_uncertainty,
            self.next_required_evidence,
            self.questions_opened,
            self.questions_closed,
        )
        if not any(effect_sets):
            raise ValueError("epistemic transition must record at least one epistemic effect")
        if self.recorded_at < self.occurred_at:
            raise ValueError("recorded_at cannot precede occurred_at")
        for name, values in (
            ("from_refs", self.from_refs),
            ("newly_visible", self.newly_visible),
            ("preserved", self.preserved),
            ("invalidated_or_reduced", self.invalidated_or_reduced),
            ("remaining_uncertainty", self.remaining_uncertainty),
            ("next_required_evidence", self.next_required_evidence),
            ("questions_opened", self.questions_opened),
            ("questions_closed", self.questions_closed),
            ("provenance_refs", self.provenance_refs),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{name} must contain unique values")
        return self

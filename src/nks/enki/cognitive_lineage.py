"""Governed cognitive-lineage profile for Project-Enki temporal graphs.

The profile represents how a subject's reasoning changed over time without turning
thought records into global Project-Enki authority, personality claims,
psychological inference, or stable identity claims. Cognitive state is local to
the subject namespace and remains distinct from canonical authority.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Iterable

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.governed_transactions import canonical_sha256
from nks.enki.temporal_graph import (
    TemporalGraphEdgeType,
    TemporalGraphLifecycleStatus,
    TemporalGraphNodeType,
    TemporalGraphRecord,
    TemporalGraphRecordKind,
    TemporalGraphStore,
)


class CognitiveStance(StrEnum):
    """Local reasoning state; never a substitute for Project-Enki authority."""

    CONSIDERED = "considered"
    SUSPECTED = "suspected"
    ACCEPTED = "accepted"
    QUALIFIED = "qualified"
    ABANDONED = "abandoned"
    SUPERSEDED = "superseded"
    UNRESOLVED = "unresolved"


COGNITIVE_NODE_TYPES = {
    TemporalGraphNodeType.OBSERVATION,
    TemporalGraphNodeType.QUESTION,
    TemporalGraphNodeType.HYPOTHESIS,
    TemporalGraphNodeType.EVIDENCE,
    TemporalGraphNodeType.INTERPRETATION,
    TemporalGraphNodeType.DECISION,
    TemporalGraphNodeType.OUTCOME,
    TemporalGraphNodeType.CONTRADICTION,
    TemporalGraphNodeType.LESSON,
}

COGNITIVE_EDGE_TYPES = {
    TemporalGraphEdgeType.DERIVED_FROM,
    TemporalGraphEdgeType.SUPPORTS,
    TemporalGraphEdgeType.CONTRADICTS,
    TemporalGraphEdgeType.INTERPRETS,
    TemporalGraphEdgeType.INFORMS,
    TemporalGraphEdgeType.DECIDED_FROM,
    TemporalGraphEdgeType.RESULTED_IN,
    TemporalGraphEdgeType.REVISES,
    TemporalGraphEdgeType.SUPERSEDES,
}

STANCE_TO_LIFECYCLE = {
    CognitiveStance.CONSIDERED: TemporalGraphLifecycleStatus.CANDIDATE,
    CognitiveStance.SUSPECTED: TemporalGraphLifecycleStatus.CANDIDATE,
    CognitiveStance.ACCEPTED: TemporalGraphLifecycleStatus.ACTIVE,
    CognitiveStance.QUALIFIED: TemporalGraphLifecycleStatus.QUALIFIED,
    CognitiveStance.ABANDONED: TemporalGraphLifecycleStatus.RETIRED,
    CognitiveStance.SUPERSEDED: TemporalGraphLifecycleStatus.SUPERSEDED,
    CognitiveStance.UNRESOLVED: TemporalGraphLifecycleStatus.UNRESOLVED,
}


class CognitiveLineageEntry(BaseModel):
    """One attributable reasoning record in a subject-local cognitive namespace."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    entry_id: str = Field(min_length=1)
    subject_id: str = Field(min_length=1)
    node_type: TemporalGraphNodeType
    stance: CognitiveStance
    domain_id: str = Field(min_length=1)
    context_ids: tuple[str, ...] = ()
    content: Any
    provenance_refs: tuple[str, ...] = Field(min_length=1)
    recorded_at: datetime
    effective_from: datetime | None
    effective_to: datetime | None = None
    superseded_at: datetime | None = None
    revises_entry_ids: tuple[str, ...] = ()
    supersedes_entry_ids: tuple[str, ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_cognitive_semantics(self) -> "CognitiveLineageEntry":
        if self.node_type not in COGNITIVE_NODE_TYPES:
            raise ValueError("unsupported cognitive node type")
        for name, values in (
            ("context_ids", self.context_ids),
            ("provenance_refs", self.provenance_refs),
            ("revises_entry_ids", self.revises_entry_ids),
            ("supersedes_entry_ids", self.supersedes_entry_ids),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{name} must contain unique values")
        if self.entry_id in self.revises_entry_ids:
            raise ValueError("an entry cannot revise itself")
        if self.entry_id in self.supersedes_entry_ids:
            raise ValueError("an entry cannot supersede itself")
        if self.stance == CognitiveStance.SUPERSEDED and self.superseded_at is None:
            raise ValueError("superseded cognitive stance requires superseded_at")
        if self.stance != CognitiveStance.SUPERSEDED and self.superseded_at is not None:
            raise ValueError("superseded_at is only valid for superseded cognitive stance")
        return self

    @property
    def namespace(self) -> str:
        return f"cognitive:{self.subject_id}"

    def to_graph_record(self) -> TemporalGraphRecord:
        """Project this entry without manufacturing authority from subjective acceptance."""

        return TemporalGraphRecord(
            graph_record_id=self.entry_id,
            graph_namespace=self.namespace,
            record_kind=TemporalGraphRecordKind.NODE,
            node_type=self.node_type,
            subject_id=self.subject_id,
            domain_id=self.domain_id,
            context_ids=self.context_ids,
            content=self.content,
            provenance_refs=self.provenance_refs,
            authority_state_ref=None,
            recorded_at=self.recorded_at,
            effective_from=self.effective_from,
            effective_to=self.effective_to,
            authority_from=None,
            authority_to=None,
            superseded_at=self.superseded_at,
            supersedes_record_ids=self.supersedes_entry_ids,
            revises_record_ids=self.revises_entry_ids,
            lifecycle_status=STANCE_TO_LIFECYCLE[self.stance],
            metadata={
                **self.metadata,
                "cognitive_stance": self.stance.value,
                "authority_scope": "subject-local-cognitive",
                "identity_inference_authorized": False,
                "stable_identity_inference_authorized": False,
                "person_object_inference_authorized": False,
            },
        )


class CognitiveLineageLink(BaseModel):
    """Explicit reasoning relationship between two cognitive entries."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    link_id: str = Field(min_length=1)
    subject_id: str = Field(min_length=1)
    edge_type: TemporalGraphEdgeType
    source_entry_id: str = Field(min_length=1)
    target_entry_id: str = Field(min_length=1)
    domain_id: str = Field(min_length=1)
    context_ids: tuple[str, ...] = ()
    provenance_refs: tuple[str, ...] = Field(min_length=1)
    recorded_at: datetime
    effective_from: datetime | None
    effective_to: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_link(self) -> "CognitiveLineageLink":
        if self.edge_type not in COGNITIVE_EDGE_TYPES:
            raise ValueError("unsupported cognitive edge type")
        if self.source_entry_id == self.target_entry_id:
            raise ValueError("cognitive links cannot be self-referential")
        return self

    @property
    def namespace(self) -> str:
        return f"cognitive:{self.subject_id}"

    def to_graph_record(self) -> TemporalGraphRecord:
        return TemporalGraphRecord(
            graph_record_id=self.link_id,
            graph_namespace=self.namespace,
            record_kind=TemporalGraphRecordKind.EDGE,
            edge_type=self.edge_type,
            subject_id=self.subject_id,
            domain_id=self.domain_id,
            context_ids=self.context_ids,
            source_record_id=self.source_entry_id,
            target_record_id=self.target_entry_id,
            provenance_refs=self.provenance_refs,
            recorded_at=self.recorded_at,
            effective_from=self.effective_from,
            effective_to=self.effective_to,
            authority_from=None,
            authority_to=None,
            superseded_at=None,
            lifecycle_status=TemporalGraphLifecycleStatus.ACTIVE,
            metadata={
                **self.metadata,
                "authority_scope": "subject-local-cognitive",
                "identity_inference_authorized": False,
                "stable_identity_inference_authorized": False,
                "person_object_inference_authorized": False,
            },
        )


class CognitiveLineageSnapshot(BaseModel):
    """Non-inferential view of cognitive records at a dual-time coordinate."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    subject_id: str
    as_of: datetime
    known_at: datetime
    entry_ids_by_stance: dict[str, tuple[str, ...]]
    unresolved_entry_ids: tuple[str, ...]
    unknown_effective_time_entry_ids: tuple[str, ...]
    snapshot_hash: str


class CognitiveLineage:
    """Validated subject-local cognitive lineage over the shared temporal grammar."""

    def __init__(
        self,
        entries: Iterable[CognitiveLineageEntry],
        links: Iterable[CognitiveLineageLink] = (),
    ) -> None:
        self._entries = tuple(entries)
        self._links = tuple(links)
        if not self._entries:
            raise ValueError("cognitive lineage requires at least one entry")

        subject_ids = {entry.subject_id for entry in self._entries}
        subject_ids.update(link.subject_id for link in self._links)
        if len(subject_ids) != 1:
            raise ValueError("one cognitive lineage cannot mix subjects")
        self._subject_id = next(iter(subject_ids))

        by_id = {entry.entry_id: entry for entry in self._entries}
        if len(by_id) != len(self._entries):
            raise ValueError("cognitive entry ids must be unique")

        link_ids = [link.link_id for link in self._links]
        if len(link_ids) != len(set(link_ids)):
            raise ValueError("cognitive link ids must be unique")
        if set(link_ids) & set(by_id):
            raise ValueError("cognitive entry and link ids must be globally unique")

        for entry in self._entries:
            for ref in (*entry.revises_entry_ids, *entry.supersedes_entry_ids):
                if ref not in by_id:
                    raise ValueError("revision and supersession refs must exist in lineage")
        for link in self._links:
            if link.source_entry_id not in by_id or link.target_entry_id not in by_id:
                raise ValueError("cognitive links must reference entries in the same lineage")

        self._validate_revision_cycles(by_id)
        self._store = TemporalGraphStore(
            [entry.to_graph_record() for entry in self._entries]
            + [link.to_graph_record() for link in self._links]
        )

    @staticmethod
    def _validate_revision_cycles(by_id: dict[str, CognitiveLineageEntry]) -> None:
        for entry in by_id.values():
            stack = list(entry.revises_entry_ids + entry.supersedes_entry_ids)
            seen: set[str] = set()
            while stack:
                current_id = stack.pop()
                if current_id == entry.entry_id:
                    raise ValueError("cognitive revision cycle detected")
                if current_id in seen:
                    continue
                seen.add(current_id)
                current = by_id[current_id]
                stack.extend(current.revises_entry_ids + current.supersedes_entry_ids)

    @property
    def subject_id(self) -> str:
        return self._subject_id

    @property
    def store(self) -> TemporalGraphStore:
        return self._store

    @property
    def lineage_hash(self) -> str:
        return self._store.store_hash

    def snapshot(self, *, as_of: datetime, known_at: datetime) -> CognitiveLineageSnapshot:
        """Return only explicit states; never synthesize a single current belief."""

        temporal = self._store.query(
            as_of=as_of,
            known_at=known_at,
            namespace=f"cognitive:{self._subject_id}",
        )
        effective_ids = set(temporal.effective_record_ids)
        unknown_effective_ids = set(temporal.unknown_effective_record_ids)
        by_stance: dict[str, list[str]] = {stance.value: [] for stance in CognitiveStance}
        for entry in self._entries:
            if entry.entry_id in effective_ids:
                by_stance[entry.stance.value].append(entry.entry_id)

        frozen = {
            stance: tuple(sorted(ids))
            for stance, ids in sorted(by_stance.items())
            if ids
        }
        unresolved = tuple(sorted(frozen.get(CognitiveStance.UNRESOLVED.value, ())))
        unknown_effective = tuple(
            sorted(
                entry.entry_id
                for entry in self._entries
                if entry.entry_id in unknown_effective_ids
            )
        )
        payload = {
            "subject_id": self._subject_id,
            "as_of": as_of,
            "known_at": known_at,
            "entry_ids_by_stance": frozen,
            "unresolved_entry_ids": unresolved,
            "unknown_effective_time_entry_ids": unknown_effective,
            "lineage_hash": self.lineage_hash,
        }
        return CognitiveLineageSnapshot(
            subject_id=self._subject_id,
            as_of=as_of,
            known_at=known_at,
            entry_ids_by_stance=frozen,
            unresolved_entry_ids=unresolved,
            unknown_effective_time_entry_ids=unknown_effective,
            snapshot_hash=canonical_sha256(payload),
        )

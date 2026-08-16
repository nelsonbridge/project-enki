"""Governed temporal-graph runtime primitives for Enki.

This module implements the first executable slice of the federated temporal graph
contract. It deliberately separates represented-world effective time, Enki
knowledge time, and authority-valid time. Historical records remain queryable
when their current lifecycle status is terminal.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Iterable, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.governed_transactions import canonical_sha256


class TemporalGraphRecordKind(StrEnum):
    NODE = "node"
    EDGE = "edge"


class TemporalGraphNodeType(StrEnum):
    SOURCE = "source"
    OBSERVATION = "observation"
    CLAIM = "claim"
    ASSUMPTION = "assumption"
    QUESTION = "question"
    HYPOTHESIS = "hypothesis"
    EVIDENCE = "evidence"
    INTERPRETATION = "interpretation"
    DECISION = "decision"
    ACTION = "action"
    OUTCOME = "outcome"
    CONTRADICTION = "contradiction"
    AUTHORITY = "authority"
    CONTEXT = "context"
    TRANSITION = "transition"
    LESSON = "lesson"
    INTERVENTION = "intervention"


class TemporalGraphEdgeType(StrEnum):
    DERIVED_FROM = "derived_from"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    BOUNDED_BY = "bounded_by"
    INTERPRETS = "interprets"
    TESTS = "tests"
    INFORMS = "informs"
    DECIDED_FROM = "decided_from"
    ACTED_ON = "acted_on"
    RESULTED_IN = "resulted_in"
    CANDIDATE_CAUSE_OF = "candidate_cause_of"
    SUPERSEDES = "supersedes"
    REVISES = "revises"
    GOVERNED_BY = "governed_by"
    OCCURRED_IN = "occurred_in"
    SELECTED_FROM = "selected_from"
    EXPOSED_TO = "exposed_to"


class TemporalGraphLifecycleStatus(StrEnum):
    CANDIDATE = "candidate"
    ACTIVE = "active"
    QUALIFIED = "qualified"
    SUPERSEDED = "superseded"
    REVOKED = "revoked"
    REJECTED = "rejected"
    RETIRED = "retired"
    UNRESOLVED = "unresolved"


NON_AUTHORITATIVE_STATUSES = {TemporalGraphLifecycleStatus.CANDIDATE, TemporalGraphLifecycleStatus.REJECTED, TemporalGraphLifecycleStatus.UNRESOLVED}
CANDIDATE_CAUSE_STATUSES = {TemporalGraphLifecycleStatus.CANDIDATE, TemporalGraphLifecycleStatus.QUALIFIED, TemporalGraphLifecycleStatus.REJECTED, TemporalGraphLifecycleStatus.RETIRED, TemporalGraphLifecycleStatus.UNRESOLVED}


class TemporalGraphPromotion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    source_namespace: str = Field(min_length=1)
    target_namespace: str = Field(min_length=1)
    reconciliation_ref: str = Field(min_length=1)
    authority_decision_ref: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_namespace_transition(self) -> "TemporalGraphPromotion":
        if self.source_namespace == self.target_namespace:
            raise ValueError("promotion must cross namespaces")
        return self


class TemporalGraphRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    contract_version: Literal["1.0-draft"] = "1.0-draft"
    graph_record_id: str = Field(min_length=1)
    graph_namespace: str = Field(min_length=1)
    record_kind: TemporalGraphRecordKind
    node_type: TemporalGraphNodeType | None = None
    edge_type: TemporalGraphEdgeType | None = None
    subject_id: str | None = None
    domain_id: str = Field(min_length=1)
    context_ids: tuple[str, ...] = ()
    source_record_id: str | None = None
    target_record_id: str | None = None
    content: Any = None
    provenance_refs: tuple[str, ...] = Field(min_length=1)
    authority_state_ref: str | None = None
    recorded_at: datetime
    effective_from: datetime | None
    effective_to: datetime | None
    authority_from: datetime | None
    authority_to: datetime | None
    superseded_at: datetime | None
    supersedes_record_ids: tuple[str, ...] = ()
    revises_record_ids: tuple[str, ...] = ()
    lifecycle_status: TemporalGraphLifecycleStatus
    promotion: TemporalGraphPromotion | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_contract_semantics(self) -> "TemporalGraphRecord":
        if self.record_kind == TemporalGraphRecordKind.NODE:
            if self.node_type is None: raise ValueError("node records require node_type")
            if self.edge_type is not None: raise ValueError("node records cannot declare edge_type")
        else:
            if self.edge_type is None: raise ValueError("edge records require edge_type")
            if self.node_type is not None: raise ValueError("edge records cannot declare node_type")
            if not self.source_record_id or not self.target_record_id: raise ValueError("edge records require source_record_id and target_record_id")
            if self.source_record_id == self.target_record_id: raise ValueError("self-referential graph edges are not permitted")
        if self.effective_from is not None and self.effective_to is not None and self.effective_to < self.effective_from: raise ValueError("effective_to cannot precede effective_from")
        if self.authority_from is not None and self.authority_to is not None and self.authority_to < self.authority_from: raise ValueError("authority_to cannot precede authority_from")
        if self.superseded_at is not None:
            if self.superseded_at < self.recorded_at: raise ValueError("superseded_at cannot precede recorded_at")
            if self.authority_to is not None and self.authority_to != self.superseded_at: raise ValueError("authority_to must equal superseded_at when both are declared")
        for name, values in (("context_ids", self.context_ids), ("provenance_refs", self.provenance_refs), ("supersedes_record_ids", self.supersedes_record_ids), ("revises_record_ids", self.revises_record_ids)):
            if len(values) != len(set(values)): raise ValueError(f"{name} must contain unique values")
        if self.graph_record_id in self.supersedes_record_ids: raise ValueError("a graph record cannot supersede itself")
        if self.graph_record_id in self.revises_record_ids: raise ValueError("a graph record cannot revise itself")
        if self.edge_type == TemporalGraphEdgeType.CANDIDATE_CAUSE_OF and self.lifecycle_status not in CANDIDATE_CAUSE_STATUSES: raise ValueError("candidate_cause_of cannot be authoritative by assertion alone")
        if self.promotion is not None and self.promotion.target_namespace != self.graph_namespace: raise ValueError("promoted record must be written in the target namespace")
        return self

    @property
    def record_hash(self) -> str: return canonical_sha256(self)
    def is_known_at(self, known_at: datetime) -> bool: return self.recorded_at <= known_at
    def is_effective_at(self, as_of: datetime) -> bool:
        return self.effective_from is not None and self.effective_from <= as_of and (self.effective_to is None or as_of < self.effective_to)
    def is_authoritative_at(self, authority_at: datetime) -> bool:
        if self.lifecycle_status in NON_AUTHORITATIVE_STATUSES or self.authority_from is None or authority_at < self.authority_from: return False
        if self.authority_to is not None and authority_at >= self.authority_to: return False
        if self.superseded_at is not None and authority_at >= self.superseded_at: return False
        return True


class TemporalGraphSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    as_of: datetime
    known_at: datetime
    authority_at: datetime
    known_record_ids: tuple[str, ...]
    effective_record_ids: tuple[str, ...]
    authoritative_record_ids: tuple[str, ...]
    unknown_effective_record_ids: tuple[str, ...]
    snapshot_hash: str


class TemporalGraphStore:
    def __init__(self, records: Iterable[TemporalGraphRecord]) -> None:
        self._records = tuple(records)
        ids = [r.graph_record_id for r in self._records]
        if len(ids) != len(set(ids)): raise ValueError("graph_record_id values must be unique")
    @property
    def records(self) -> tuple[TemporalGraphRecord, ...]: return self._records
    @property
    def store_hash(self) -> str: return canonical_sha256(sorted(self._records, key=lambda r: r.graph_record_id))
    def query(self, *, as_of: datetime, known_at: datetime, authority_at: datetime | None = None, namespace: str | None = None) -> TemporalGraphSnapshot:
        resolved = authority_at or known_at
        scoped = tuple(r for r in self._records if namespace is None or r.graph_namespace == namespace)
        known = tuple(r for r in scoped if r.is_known_at(known_at))
        effective = tuple(r for r in known if r.is_effective_at(as_of))
        authoritative = tuple(r for r in effective if r.is_authoritative_at(resolved))
        unknown = tuple(r for r in known if r.effective_from is None)
        known_ids = tuple(sorted(r.graph_record_id for r in known)); effective_ids = tuple(sorted(r.graph_record_id for r in effective)); authoritative_ids = tuple(sorted(r.graph_record_id for r in authoritative)); unknown_ids = tuple(sorted(r.graph_record_id for r in unknown))
        payload = {"as_of": as_of, "known_at": known_at, "authority_at": resolved, "known_record_ids": known_ids, "effective_record_ids": effective_ids, "authoritative_record_ids": authoritative_ids, "unknown_effective_record_ids": unknown_ids, "store_hash": self.store_hash, "namespace": namespace}
        return TemporalGraphSnapshot(as_of=as_of, known_at=known_at, authority_at=resolved, known_record_ids=known_ids, effective_record_ids=effective_ids, authoritative_record_ids=authoritative_ids, unknown_effective_record_ids=unknown_ids, snapshot_hash=canonical_sha256(payload))

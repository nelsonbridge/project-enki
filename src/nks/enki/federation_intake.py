"""Governed cross-namespace intake, reconciliation, and promotion for Project-Enki.

The runtime deliberately keeps three decisions separate:

1. conformance decides whether a producer record may be admitted for review;
2. reconciliation records what that evidence means relative to a target namespace;
3. authority decides whether a reconciled interpretation may qualify, govern, or be rejected.

Admission never transfers authority. Reconciliation never transfers authority. A cross-namespace
edge never transfers authority. Governing promotion requires an explicit authority decision and
an explicit authority interval on the target record.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.governed_transactions import canonical_sha256
from nks.enki.temporal_graph import (
    TemporalGraphLifecycleStatus,
    TemporalGraphPromotion,
    TemporalGraphRecord,
)


class FederationReconciliationDisposition(StrEnum):
    """Result of comparing admitted evidence with a target namespace."""

    MATCH = "match"
    PARTIAL = "partial"
    CONFLICT = "conflict"
    INDETERMINATE = "indeterminate"
    REJECT = "reject"


class FederationPromotionDisposition(StrEnum):
    """Governed outcome after reconciliation."""

    QUALIFY = "qualify"
    PROMOTE = "promote"
    REJECT = "reject"


class FederationIntakeReceipt(BaseModel):
    """Durable proof that a source record passed conformance without gaining authority."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    receipt_id: str = Field(min_length=1)
    source_namespace: str = Field(min_length=1)
    source_record_id: str = Field(min_length=1)
    source_record_hash: str = Field(min_length=1)
    received_at: datetime
    admitted_as_candidate: bool = True

    @property
    def receipt_hash(self) -> str:
        return canonical_sha256(self.model_dump(mode="json"))


class FederationReconciliation(BaseModel):
    """Non-authoritative interpretation of one admitted source record."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    reconciliation_id: str = Field(min_length=1)
    source_namespace: str = Field(min_length=1)
    source_record_id: str = Field(min_length=1)
    target_namespace: str = Field(min_length=1)
    disposition: FederationReconciliationDisposition
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    rationale: str = Field(min_length=1)
    recorded_at: datetime
    reopens_reconciliation_id: str | None = None

    @model_validator(mode="after")
    def validate_reconciliation(self) -> "FederationReconciliation":
        if self.source_namespace == self.target_namespace:
            raise ValueError("cross-namespace reconciliation requires distinct namespaces")
        if len(self.evidence_refs) != len(set(self.evidence_refs)):
            raise ValueError("evidence_refs must contain unique values")
        if self.reopens_reconciliation_id == self.reconciliation_id:
            raise ValueError("a reconciliation cannot reopen itself")
        return self

    @property
    def reconciliation_hash(self) -> str:
        return canonical_sha256(self.model_dump(mode="json"))


class FederationPromotionDecision(BaseModel):
    """Explicit authority decision after reconciliation; it does not rewrite the source."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    decision_id: str = Field(min_length=1)
    source_namespace: str = Field(min_length=1)
    source_record_id: str = Field(min_length=1)
    target_namespace: str = Field(min_length=1)
    reconciliation_id: str = Field(min_length=1)
    disposition: FederationPromotionDisposition
    authority_decision_ref: str = Field(min_length=1)
    recorded_at: datetime

    @model_validator(mode="after")
    def validate_decision(self) -> "FederationPromotionDecision":
        if self.source_namespace == self.target_namespace:
            raise ValueError("cross-namespace promotion requires distinct namespaces")
        return self

    @property
    def decision_hash(self) -> str:
        return canonical_sha256(self.model_dump(mode="json"))


class FederationPromotionReceipt(BaseModel):
    """Auditable result of a governed qualification, promotion, or rejection."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    decision_id: str = Field(min_length=1)
    decision_hash: str = Field(min_length=1)
    source_namespace: str = Field(min_length=1)
    source_record_id: str = Field(min_length=1)
    target_namespace: str = Field(min_length=1)
    reconciliation_id: str = Field(min_length=1)
    disposition: FederationPromotionDisposition
    authority_decision_ref: str = Field(min_length=1)
    decided_at: datetime
    target_record_id: str | None = None
    target_record_hash: str | None = None

    @model_validator(mode="after")
    def validate_receipt(self) -> "FederationPromotionReceipt":
        target_fields = (self.target_record_id, self.target_record_hash)
        if self.disposition == FederationPromotionDisposition.REJECT:
            if any(value is not None for value in target_fields):
                raise ValueError("rejected promotions cannot have a target record")
        elif any(value is None for value in target_fields):
            raise ValueError("accepted federation decisions require a target record")
        return self

    @property
    def receipt_hash(self) -> str:
        return canonical_sha256(self.model_dump(mode="json"))


class GovernedFederationIntake:
    """In-memory governed federation ledger over the shared temporal graph grammar."""

    def __init__(self) -> None:
        self._sources: dict[tuple[str, str], TemporalGraphRecord] = {}
        self._intake_receipts: dict[tuple[str, str], FederationIntakeReceipt] = {}
        self._reconciliations: dict[str, FederationReconciliation] = {}
        self._decisions: dict[str, FederationPromotionDecision] = {}
        self._promotion_receipts: dict[str, FederationPromotionReceipt] = {}
        self._targets: dict[tuple[str, str], TemporalGraphRecord] = {}

    @staticmethod
    def _source_key(namespace: str, record_id: str) -> tuple[str, str]:
        return namespace, record_id

    @staticmethod
    def _append_unique(values: tuple[str, ...], *additional: str) -> tuple[str, ...]:
        merged = list(values)
        for value in additional:
            if value not in merged:
                merged.append(value)
        return tuple(merged)

    def ingest(
        self,
        record: TemporalGraphRecord | dict[str, Any],
        *,
        source_namespace: str,
        received_at: datetime,
    ) -> FederationIntakeReceipt:
        """Validate and admit a producer record as reviewable evidence, never as Enki authority."""

        candidate = TemporalGraphRecord.model_validate(record)
        if candidate.graph_namespace != source_namespace:
            raise ValueError("declared source namespace does not match producer record")
        if candidate.promotion is not None:
            raise ValueError("producer records cannot arrive with cross-namespace promotion authority")
        if any(
            value is not None
            for value in (
                candidate.authority_state_ref,
                candidate.authority_from,
                candidate.authority_to,
            )
        ):
            raise ValueError("producer records cannot transfer authority through federation intake")

        key = self._source_key(source_namespace, candidate.graph_record_id)
        existing = self._sources.get(key)
        if existing is not None:
            if existing.record_hash != candidate.record_hash:
                raise ValueError("source record id already exists with different content")
            return self._intake_receipts[key]

        receipt_payload = {
            "source_namespace": source_namespace,
            "source_record_id": candidate.graph_record_id,
            "source_record_hash": candidate.record_hash,
            "received_at": received_at,
        }
        receipt = FederationIntakeReceipt(
            receipt_id=f"intake:{canonical_sha256(receipt_payload)[:24]}",
            source_namespace=source_namespace,
            source_record_id=candidate.graph_record_id,
            source_record_hash=candidate.record_hash,
            received_at=received_at,
        )
        self._sources[key] = candidate
        self._intake_receipts[key] = receipt
        return receipt

    def reconcile(self, reconciliation: FederationReconciliation) -> FederationReconciliation:
        """Persist a non-authoritative comparison against a target namespace."""

        source_key = self._source_key(
            reconciliation.source_namespace,
            reconciliation.source_record_id,
        )
        if source_key not in self._sources:
            raise ValueError("reconciliation source record has not passed federation intake")

        existing = self._reconciliations.get(reconciliation.reconciliation_id)
        if existing is not None:
            if existing.reconciliation_hash != reconciliation.reconciliation_hash:
                raise ValueError("reconciliation id already exists with different content")
            return existing

        if reconciliation.reopens_reconciliation_id is not None:
            previous = self._reconciliations.get(reconciliation.reopens_reconciliation_id)
            if previous is None:
                raise ValueError("reopened reconciliation does not exist")
            if (
                previous.source_namespace != reconciliation.source_namespace
                or previous.source_record_id != reconciliation.source_record_id
                or previous.target_namespace != reconciliation.target_namespace
            ):
                raise ValueError("reopened reconciliation must govern the same source and target")
            if reconciliation.recorded_at < previous.recorded_at:
                raise ValueError("reopened reconciliation cannot predate the prior reconciliation")

        self._reconciliations[reconciliation.reconciliation_id] = reconciliation
        return reconciliation

    def decide(
        self,
        decision: FederationPromotionDecision,
        *,
        proposed_target: TemporalGraphRecord | None = None,
    ) -> FederationPromotionReceipt:
        """Apply an explicit authority decision without mutating the source record."""

        source_key = self._source_key(decision.source_namespace, decision.source_record_id)
        source = self._sources.get(source_key)
        if source is None:
            raise ValueError("promotion source record has not passed federation intake")

        reconciliation = self._reconciliations.get(decision.reconciliation_id)
        if reconciliation is None:
            raise ValueError("promotion requires an existing reconciliation")
        if (
            reconciliation.source_namespace != decision.source_namespace
            or reconciliation.source_record_id != decision.source_record_id
            or reconciliation.target_namespace != decision.target_namespace
        ):
            raise ValueError("promotion decision does not match its reconciliation")
        if decision.recorded_at < reconciliation.recorded_at:
            raise ValueError("promotion decision cannot predate reconciliation")
        if (
            reconciliation.disposition == FederationReconciliationDisposition.REJECT
            and decision.disposition != FederationPromotionDisposition.REJECT
        ):
            raise ValueError("rejected reconciliation cannot be qualified or promoted")

        final_target: TemporalGraphRecord | None = None
        if decision.disposition == FederationPromotionDisposition.REJECT:
            if proposed_target is not None:
                raise ValueError("rejected promotion cannot create a target record")
        else:
            if proposed_target is None:
                raise ValueError("accepted federation decision requires a proposed target")
            final_target = self._govern_target(
                source=source,
                reconciliation=reconciliation,
                decision=decision,
                proposed_target=proposed_target,
            )

        receipt = FederationPromotionReceipt(
            decision_id=decision.decision_id,
            decision_hash=decision.decision_hash,
            source_namespace=decision.source_namespace,
            source_record_id=decision.source_record_id,
            target_namespace=decision.target_namespace,
            reconciliation_id=decision.reconciliation_id,
            disposition=decision.disposition,
            authority_decision_ref=decision.authority_decision_ref,
            decided_at=decision.recorded_at,
            target_record_id=None if final_target is None else final_target.graph_record_id,
            target_record_hash=None if final_target is None else final_target.record_hash,
        )

        existing_decision = self._decisions.get(decision.decision_id)
        if existing_decision is not None:
            existing_receipt = self._promotion_receipts[decision.decision_id]
            if existing_decision.decision_hash != decision.decision_hash:
                raise ValueError("promotion decision id already exists with different content")
            if existing_receipt.receipt_hash != receipt.receipt_hash:
                raise ValueError("promotion decision id already exists with a different target")
            return existing_receipt

        if final_target is not None:
            target_key = self._source_key(
                final_target.graph_namespace,
                final_target.graph_record_id,
            )
            existing_target = self._targets.get(target_key)
            if existing_target is not None and existing_target.record_hash != final_target.record_hash:
                raise ValueError("target record id already exists with different content")
            self._targets[target_key] = final_target

        self._decisions[decision.decision_id] = decision
        self._promotion_receipts[decision.decision_id] = receipt
        return receipt

    def _govern_target(
        self,
        *,
        source: TemporalGraphRecord,
        reconciliation: FederationReconciliation,
        decision: FederationPromotionDecision,
        proposed_target: TemporalGraphRecord,
    ) -> TemporalGraphRecord:
        if proposed_target.graph_namespace != decision.target_namespace:
            raise ValueError("proposed target namespace does not match promotion decision")
        if proposed_target.graph_record_id == source.graph_record_id:
            raise ValueError("promotion must create a distinct target record id")
        if proposed_target.promotion is not None:
            raise ValueError("proposed target cannot self-assert federation promotion")
        if proposed_target.recorded_at < decision.recorded_at:
            raise ValueError("promoted target cannot be recorded before the authority decision")

        if decision.disposition == FederationPromotionDisposition.QUALIFY:
            if proposed_target.lifecycle_status != TemporalGraphLifecycleStatus.QUALIFIED:
                raise ValueError("qualified federation target must use qualified lifecycle status")
            if any(
                value is not None
                for value in (
                    proposed_target.authority_state_ref,
                    proposed_target.authority_from,
                    proposed_target.authority_to,
                )
            ):
                raise ValueError("qualification cannot create governing authority")
        elif decision.disposition == FederationPromotionDisposition.PROMOTE:
            if proposed_target.lifecycle_status != TemporalGraphLifecycleStatus.ACTIVE:
                raise ValueError("governing federation target must use active lifecycle status")
            if proposed_target.authority_state_ref is None or proposed_target.authority_from is None:
                raise ValueError(
                    "governing promotion requires explicit authority state and authority interval"
                )

        promotion = TemporalGraphPromotion(
            source_namespace=decision.source_namespace,
            target_namespace=decision.target_namespace,
            reconciliation_ref=decision.reconciliation_id,
            authority_decision_ref=decision.authority_decision_ref,
        )
        provenance_refs = self._append_unique(
            proposed_target.provenance_refs,
            f"federation-source:{decision.source_namespace}:{decision.source_record_id}",
            f"reconciliation:{decision.reconciliation_id}",
            f"authority-decision:{decision.authority_decision_ref}",
        )
        metadata = {
            **proposed_target.metadata,
            "federation_source_record_id": decision.source_record_id,
            "federation_source_record_hash": source.record_hash,
            "federation_reconciliation_id": reconciliation.reconciliation_id,
            "federation_reconciliation_hash": reconciliation.reconciliation_hash,
            "federation_decision_id": decision.decision_id,
            "federation_disposition": decision.disposition.value,
        }
        payload = proposed_target.model_dump()
        payload.update(
            {
                "provenance_refs": provenance_refs,
                "promotion": promotion,
                "metadata": metadata,
            }
        )
        return TemporalGraphRecord.model_validate(payload)

    def source_record(self, namespace: str, record_id: str) -> TemporalGraphRecord:
        return self._sources[self._source_key(namespace, record_id)]

    def target_record(self, namespace: str, record_id: str) -> TemporalGraphRecord:
        return self._targets[self._source_key(namespace, record_id)]

    @property
    def intake_receipts(self) -> tuple[FederationIntakeReceipt, ...]:
        return tuple(sorted(self._intake_receipts.values(), key=lambda value: value.receipt_id))

    @property
    def reconciliations(self) -> tuple[FederationReconciliation, ...]:
        return tuple(
            sorted(self._reconciliations.values(), key=lambda value: value.reconciliation_id)
        )

    @property
    def promotion_receipts(self) -> tuple[FederationPromotionReceipt, ...]:
        return tuple(
            sorted(self._promotion_receipts.values(), key=lambda value: value.decision_id)
        )

    @property
    def ledger_hash(self) -> str:
        """Deterministic state hash for replay and portability checks."""

        payload = {
            "sources": sorted(record.record_hash for record in self._sources.values()),
            "intake_receipts": sorted(
                receipt.receipt_hash for receipt in self._intake_receipts.values()
            ),
            "reconciliations": sorted(
                record.reconciliation_hash for record in self._reconciliations.values()
            ),
            "decisions": sorted(record.decision_hash for record in self._decisions.values()),
            "promotion_receipts": sorted(
                receipt.receipt_hash for receipt in self._promotion_receipts.values()
            ),
            "targets": sorted(record.record_hash for record in self._targets.values()),
        }
        return canonical_sha256(payload)

"""Portable export and deterministic replay for governed Project-Enki federation state."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nks.application.governed_transactions import canonical_sha256
from nks.enki.federation_intake import (
    FederationIntakeReceipt,
    FederationPromotionDecision,
    FederationPromotionDisposition,
    FederationPromotionReceipt,
    FederationReconciliation,
    GovernedFederationIntake,
)
from nks.enki.temporal_graph import TemporalGraphRecord


PORTABLE_BUNDLE_VERSION = "1.0-draft"
TEMPORAL_CONTRACT_VERSION = "1.0-draft"

_GOVERNANCE_METADATA_KEYS = {
    "federation_source_record_id",
    "federation_source_record_hash",
    "federation_reconciliation_id",
    "federation_reconciliation_hash",
    "federation_decision_id",
    "federation_disposition",
}


class FederationPortableIntakeEvent(BaseModel):
    """One admitted source record paired with the receipt created at intake."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    record: TemporalGraphRecord
    receipt: FederationIntakeReceipt

    @model_validator(mode="after")
    def validate_event(self) -> "FederationPortableIntakeEvent":
        if self.record.graph_namespace != self.receipt.source_namespace:
            raise ValueError("intake receipt namespace does not match source record")
        if self.record.graph_record_id != self.receipt.source_record_id:
            raise ValueError("intake receipt id does not match source record")
        if self.record.record_hash != self.receipt.source_record_hash:
            raise ValueError("intake receipt hash does not match source record")
        return self


class FederationPortableDecisionEvent(BaseModel):
    """Replayable authority decision with its equivalent pre-governance proposal."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    decision: FederationPromotionDecision
    proposed_target: TemporalGraphRecord | None = None
    expected_receipt: FederationPromotionReceipt
    expected_target: TemporalGraphRecord | None = None

    @model_validator(mode="after")
    def validate_event(self) -> "FederationPortableDecisionEvent":
        receipt = self.expected_receipt
        decision = self.decision
        if decision.decision_hash != receipt.decision_hash:
            raise ValueError("promotion receipt decision hash does not match decision")
        if (
            decision.decision_id != receipt.decision_id
            or decision.source_namespace != receipt.source_namespace
            or decision.source_record_id != receipt.source_record_id
            or decision.target_namespace != receipt.target_namespace
            or decision.reconciliation_id != receipt.reconciliation_id
            or decision.disposition != receipt.disposition
            or decision.authority_decision_ref != receipt.authority_decision_ref
            or decision.recorded_at != receipt.decided_at
        ):
            raise ValueError("promotion receipt does not match decision coordinates")

        if decision.disposition == FederationPromotionDisposition.REJECT:
            if self.proposed_target is not None or self.expected_target is not None:
                raise ValueError("rejected decision cannot carry a target record")
            return self

        if self.proposed_target is None or self.expected_target is None:
            raise ValueError("accepted decision requires proposal and expected target")
        if receipt.target_record_id != self.expected_target.graph_record_id:
            raise ValueError("promotion receipt target id does not match expected target")
        if receipt.target_record_hash != self.expected_target.record_hash:
            raise ValueError("promotion receipt target hash does not match expected target")
        if self.expected_target.graph_namespace != decision.target_namespace:
            raise ValueError("expected target namespace does not match decision")
        promotion = self.expected_target.promotion
        if promotion is None:
            raise ValueError("expected target is missing governed promotion lineage")
        if (
            promotion.source_namespace != decision.source_namespace
            or promotion.target_namespace != decision.target_namespace
            or promotion.reconciliation_ref != decision.reconciliation_id
            or promotion.authority_decision_ref != decision.authority_decision_ref
        ):
            raise ValueError("expected target promotion lineage does not match decision")
        return self


class FederationPortableBundle(BaseModel):
    """Provider-independent replay envelope for governed federation history."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    bundle_version: Literal["1.0-draft"] = PORTABLE_BUNDLE_VERSION
    temporal_contract_version: Literal["1.0-draft"] = TEMPORAL_CONTRACT_VERSION
    intake_events: tuple[FederationPortableIntakeEvent, ...] = ()
    reconciliations: tuple[FederationReconciliation, ...] = ()
    decision_events: tuple[FederationPortableDecisionEvent, ...] = ()
    source_ledger_hash: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_bundle(self) -> "FederationPortableBundle":
        source_keys: set[tuple[str, str]] = set()
        for event in self.intake_events:
            if event.record.contract_version != self.temporal_contract_version:
                raise ValueError("source record contract version does not match bundle")
            key = (event.record.graph_namespace, event.record.graph_record_id)
            if key in source_keys:
                raise ValueError("portable bundle contains duplicate source record")
            source_keys.add(key)

        reconciliation_ids: set[str] = set()
        for reconciliation in self.reconciliations:
            if reconciliation.reconciliation_id in reconciliation_ids:
                raise ValueError("portable bundle contains duplicate reconciliation id")
            reconciliation_ids.add(reconciliation.reconciliation_id)
            key = (reconciliation.source_namespace, reconciliation.source_record_id)
            if key not in source_keys:
                raise ValueError("portable reconciliation references missing source record")

        decision_ids: set[str] = set()
        for event in self.decision_events:
            decision = event.decision
            if decision.decision_id in decision_ids:
                raise ValueError("portable bundle contains duplicate decision id")
            decision_ids.add(decision.decision_id)
            if (decision.source_namespace, decision.source_record_id) not in source_keys:
                raise ValueError("portable decision references missing source record")
            if decision.reconciliation_id not in reconciliation_ids:
                raise ValueError("portable decision references missing reconciliation")
            for record in (event.proposed_target, event.expected_target):
                if record is not None and record.contract_version != self.temporal_contract_version:
                    raise ValueError("target record contract version does not match bundle")
        return self

    @property
    def bundle_hash(self) -> str:
        return canonical_sha256(self.model_dump(mode="json"))

    def to_json(self) -> str:
        return self.model_dump_json()


def _decision_from_receipt(receipt: FederationPromotionReceipt) -> FederationPromotionDecision:
    decision = FederationPromotionDecision(
        decision_id=receipt.decision_id,
        source_namespace=receipt.source_namespace,
        source_record_id=receipt.source_record_id,
        target_namespace=receipt.target_namespace,
        reconciliation_id=receipt.reconciliation_id,
        disposition=receipt.disposition,
        authority_decision_ref=receipt.authority_decision_ref,
        recorded_at=receipt.decided_at,
    )
    if decision.decision_hash != receipt.decision_hash:
        raise ValueError("stored promotion receipt cannot reconstruct its authority decision")
    return decision


def _proposal_from_governed_target(
    target: TemporalGraphRecord,
    receipt: FederationPromotionReceipt,
) -> TemporalGraphRecord:
    """Recover an equivalent proposal whose governance decoration deterministically replays."""

    promotion = target.promotion
    if promotion is None:
        raise ValueError("accepted promotion receipt points to target without promotion lineage")
    expected_refs = {
        f"federation-source:{receipt.source_namespace}:{receipt.source_record_id}",
        f"reconciliation:{receipt.reconciliation_id}",
        f"authority-decision:{receipt.authority_decision_ref}",
    }
    payload = target.model_dump()
    payload["promotion"] = None
    payload["provenance_refs"] = tuple(
        value for value in target.provenance_refs if value not in expected_refs
    )
    payload["metadata"] = {
        key: value for key, value in target.metadata.items() if key not in _GOVERNANCE_METADATA_KEYS
    }
    return TemporalGraphRecord.model_validate(payload)


def export_federation_bundle(ledger: GovernedFederationIntake) -> FederationPortableBundle:
    """Export the governed federation ledger without provider-specific state."""

    intake_events = tuple(
        FederationPortableIntakeEvent(
            record=ledger.source_record(receipt.source_namespace, receipt.source_record_id),
            receipt=receipt,
        )
        for receipt in sorted(
            ledger.intake_receipts,
            key=lambda value: (value.source_namespace, value.source_record_id),
        )
    )

    reconciliations = tuple(
        sorted(
            ledger.reconciliations,
            key=lambda value: (value.recorded_at, value.reconciliation_id),
        )
    )

    decision_events: list[FederationPortableDecisionEvent] = []
    for receipt in sorted(
        ledger.promotion_receipts,
        key=lambda value: (value.decided_at, value.decision_id),
    ):
        decision = _decision_from_receipt(receipt)
        target: TemporalGraphRecord | None = None
        proposal: TemporalGraphRecord | None = None
        if receipt.disposition != FederationPromotionDisposition.REJECT:
            if receipt.target_record_id is None:
                raise ValueError("accepted promotion receipt is missing target record id")
            target = ledger.target_record(receipt.target_namespace, receipt.target_record_id)
            proposal = _proposal_from_governed_target(target, receipt)
        decision_events.append(
            FederationPortableDecisionEvent(
                decision=decision,
                proposed_target=proposal,
                expected_receipt=receipt,
                expected_target=target,
            )
        )

    return FederationPortableBundle(
        intake_events=intake_events,
        reconciliations=reconciliations,
        decision_events=tuple(decision_events),
        source_ledger_hash=ledger.ledger_hash,
    )


def _parse_bundle(
    bundle: FederationPortableBundle | dict[str, Any] | str,
) -> FederationPortableBundle:
    if isinstance(bundle, FederationPortableBundle):
        return bundle
    if isinstance(bundle, str):
        return FederationPortableBundle.model_validate_json(bundle)
    return FederationPortableBundle.model_validate(bundle)


def _replay_reconciliations(
    ledger: GovernedFederationIntake,
    reconciliations: tuple[FederationReconciliation, ...],
) -> None:
    pending = {value.reconciliation_id: value for value in reconciliations}
    completed: set[str] = set()
    while pending:
        progressed = False
        for reconciliation_id in sorted(
            pending,
            key=lambda value: (pending[value].recorded_at, value),
        ):
            reconciliation = pending[reconciliation_id]
            dependency = reconciliation.reopens_reconciliation_id
            if dependency is not None and dependency not in completed:
                continue
            ledger.reconcile(reconciliation)
            completed.add(reconciliation_id)
            del pending[reconciliation_id]
            progressed = True
            break
        if not progressed:
            raise ValueError("portable reconciliation history has unresolved dependency or cycle")


def replay_federation_bundle(
    bundle: FederationPortableBundle | dict[str, Any] | str,
) -> GovernedFederationIntake:
    """Reconstruct and verify the same governed state from a portable event history."""

    portable = _parse_bundle(bundle)
    ledger = GovernedFederationIntake()

    for event in sorted(
        portable.intake_events,
        key=lambda value: (value.receipt.received_at, value.record.graph_namespace, value.record.graph_record_id),
    ):
        receipt = ledger.ingest(
            event.record,
            source_namespace=event.receipt.source_namespace,
            received_at=event.receipt.received_at,
        )
        if receipt.receipt_hash != event.receipt.receipt_hash:
            raise ValueError("federation intake replay receipt mismatch")

    _replay_reconciliations(ledger, portable.reconciliations)

    for event in sorted(
        portable.decision_events,
        key=lambda value: (value.decision.recorded_at, value.decision.decision_id),
    ):
        receipt = ledger.decide(event.decision, proposed_target=event.proposed_target)
        if receipt.receipt_hash != event.expected_receipt.receipt_hash:
            raise ValueError("federation promotion replay receipt mismatch")
        if event.expected_target is not None:
            if receipt.target_record_id is None:
                raise ValueError("accepted federation replay did not create target")
            replayed_target = ledger.target_record(
                event.decision.target_namespace,
                receipt.target_record_id,
            )
            if replayed_target.record_hash != event.expected_target.record_hash:
                raise ValueError("federation target replay hash mismatch")

    if ledger.ledger_hash != portable.source_ledger_hash:
        raise ValueError("federation replay ledger hash does not match exported authority state")
    return ledger

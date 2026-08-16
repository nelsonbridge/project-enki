# ADR-0001: Append-Only Evidence

- **Status:** Accepted
- **Date:** 2026-08-16

## Context

Longitudinal observatories require durable traceability. Silent mutation of prior evidence invalidates lineage and auditability.

## Decision

Adopt an append-only evidence model:

1. Raw evidence records are immutable after ingestion.
2. Provenance for evidence capture is immutable and mandatory.
3. Corrections are represented as new records linked by supersession.
4. Superseded records remain present in history.
5. Supersession links are machine-checkable through stable record IDs.

## Consequences

- Preserved history across corrections and reinterpretations.
- Auditability of what changed, when, and why.
- Downstream systems can reconstruct full lineage without lossy rewrite.

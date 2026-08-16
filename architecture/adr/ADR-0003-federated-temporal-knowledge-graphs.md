# ADR-0003 — Federated Temporal Knowledge Graphs

## Status

Proposed

## Context

Enki must preserve historical truth, current authority, provenance, contradiction, and governed change across multiple downstream products and experimental domains.

A single undifferentiated graph would make it too easy to collapse domain-local observations into global authority. Conversely, unrelated graph models for each project would prevent shared reasoning lineage, portability, and cross-project learning.

The system also requires more than ordinary artifact lineage. It must represent how assumptions, hypotheses, interpretations, decisions, actions, outcomes, lessons, and authority change through time.

## Decision

Adopt a **federated temporal knowledge graph** model.

Enki owns the shared temporal/provenance/authority contract. Individual graph namespaces own domain interpretation and local authority.

Initial scope profiles are:

- cognitive lineage;
- behavioral/observatory lineage;
- project/institutional lineage.

The shared contract distinguishes represented-world effective time from system knowledge/recorded time and supports `as_of` and `known_at` queries.

Cross-namespace relationships are allowed, but a relationship does not itself transfer authority. Promotion requires an explicit governed reconciliation and authority decision.

No direct `caused` edge is part of v1. Candidate causal reasoning uses `candidate_cause_of` until separately supported and governed.

## Consequences

### Positive

- Historical reasoning remains reconstructable after later correction.
- Cognitive, behavioral, and project graphs can use one grammar without becoming one authority domain.
- Cross-project learning can be traced without silent canonicalization.
- Temporal RAG/retrieval can distinguish what was effective from what was known.
- Provider-specific graph technology remains replaceable.
- Person-Object or identity conclusions cannot be smuggled in through repeated observations alone.

### Costs

- More explicit records and edges must be maintained.
- Temporal queries and reconciliation are more complex than present-state lookup.
- Namespace and promotion controls require validation.
- Downstream consumers must map local record families into the common contract.

## Guardrails

1. Shared grammar does not imply shared authority.
2. Models may propose records and relationships but may not manufacture human authority.
3. Unknown remains unknown.
4. Contradictions create resolution work rather than silent merge.
5. Supersession changes current authority but does not erase historical truth.
6. Cross-namespace promotion requires governed reconciliation.
7. A graph implementation must remain exportable and reconstructable without its hosting provider.

## Related artifacts

- `architecture/enki/enki-temporal-knowledge-graph-v1.md`
- `contracts/enki-temporal-graph-v1.json`
- `contracts/payloads/enki-temporal-graph-record-v1.schema.json`
- `architecture/enki/enki-canonical-nine-layer-architecture.md`
- `architecture/knowledge-graph-model.md`

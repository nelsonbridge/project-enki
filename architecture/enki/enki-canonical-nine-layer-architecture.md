# Project-Enki — Canonical Nine-Layer Architecture

This document defines the corrected architectural decomposition used to reason about Project-Enki without conflating logical layers, deployment topology, provider capabilities, or cross-cutting controls.

The architecture is organized as **nine layers plus four cross-cutting planes**.

Current product/system identity is governed by `contracts/project-enki-identity-v1.json`. Historical aliases may remain in historical sources, but present-tense architecture resolves to **Project-Enki**.

The current knowledge-ownership and consumer boundary is governed by `docs/architecture-decisions/ADR-0003-portable-knowledge-ownership-and-consumer-boundary.md`. Domain origin alone does not determine whether knowledge belongs in Enki or a consumer.

The layer model defines **responsibility boundaries, not mandatory subsystem counts**. A layer does not imply a separately deployed service, module, datastore, or framework. Project-Enki SHOULD implement these responsibilities with the fewest stable components that preserve governance, security, portability, recovery, and downstream contract value.

## Layer model

| Layer | Name | Purpose |
|---|---|---|
| 1 | Ecosystem & Consumer Context | Humans, source artifacts, external systems, and downstream product suites that interact with Project-Enki. |
| 2 | Hosted Deployment Topology | Cloud/provider placement, trust boundaries, regions, and core hosting surfaces. |
| 3 | Edge, Identity & Access | Ingress, routing, edge security, authentication, authorization, tenant resolution, and execution context. |
| 4 | Runtime & Service Bindings | Request lifecycle, runtime execution, provider bindings, database connectivity, secrets, and optional runtime adapters. |
| 5 | Application & Governed Knowledge Services | Capture, normalization, state, context, interpretation, retrieval, projection, packaging, and controlled disclosure. |
| 6 | Governance & Governed Execution | Authority, approval, policy, provenance, transactions, reservations, receipts, model-use controls, and governed mutation. |
| 7 | Persistence, Recovery & Lifecycle | Journals, snapshots, replay, retention, reconciliation, backup, recovery, export/import, conflict handling, and audit. |
| 8 | Storage Adapters & Physical Persistence | Relational, object, indexing, caching, serialization, integrity, and provider-specific persistence adapters. |
| 9 | Canonical Record & Knowledge Model | Definitive record families, relationships, temporal semantics, lineage, schema evolution, semantic registries, and integrity metadata. |

```mermaid
flowchart TB
  L1[1. Ecosystem & Consumer Context]
  L2[2. Hosted Deployment Topology]
  L3[3. Edge, Identity & Access]
  L4[4. Runtime & Service Bindings]
  L5[5. Application & Governed Knowledge Services]
  L6[6. Governance & Governed Execution]
  L7[7. Persistence, Recovery & Lifecycle]
  L8[8. Storage Adapters & Physical Persistence]
  L9[9. Canonical Record & Knowledge Model]

  L1 --> L2 --> L3 --> L4 --> L5 --> L6 --> L7 --> L8 --> L9

  GOV[Governance & Authority Plane]
  SEC[Security & Privacy Plane]
  OBS[Observability & Audit Plane]
  PORT[Portability & Recovery Plane]

  GOV -. spans 2-9 .-> L2
  GOV -. spans 2-9 .-> L9
  SEC -. spans 2-9 .-> L2
  SEC -. spans 2-9 .-> L9
  OBS -. spans 2-9 .-> L2
  OBS -. spans 2-9 .-> L9
  PORT -. spans 2-9 .-> L2
  PORT -. spans 2-9 .-> L9
```

## Layer 1 — Ecosystem & Consumer Context

Project-Enki receives source material and governed human inputs and exposes reusable knowledge capabilities to independent downstream suites.

Examples:

- Human operators, reviewers, stewards, and decision-makers
- Documents, conversations, observations, evidence, feedback, and structured data
- External APIs, systems, and partner integrations
- Media Blitz
- Career Intelligence and Placement / Golden-Nibiru
- Personal Cognitive Continuity
- Research and executive decision support

Downstream suites remain consumers. They do not define Project-Enki product identity, product-specific workflows, decision policies, optimization objectives, or local execution authority.

A consumer may nevertheless originate observations, outcomes, or domain-specific evidence that can become governed Enki knowledge through explicit provenance, reconciliation, and authority. Consumer origin does not make a portable knowledge object permanently consumer-owned, and projection into a consumer does not transfer canonical mutation authority back to that consumer.

Architectural separability is mandatory. Shared infrastructure does not collapse product identity, local workflow semantics, local authority, deployment lifecycle, data ownership, or reconstruction boundaries. The governing rules are defined in `architecture/enki/project-enki-identity-and-separation-invariants.md`.

## Layer 2 — Hosted Deployment Topology

Defines where Project-Enki executes and where authoritative data is held.

For the `CF-NEON-R2` candidate:

- Cloudflare Workers: compute and edge runtime
- Neon Postgres: canonical structured data
- Cloudflare R2: object evidence and package storage

Provider services beyond this core are optional until explicitly adopted.

## Layer 3 — Edge, Identity & Access

Responsibilities include:

- TLS termination and ingress
- DNS and routing
- WAF and rate limiting
- authentication and authorization
- tenant, namespace, subject, domain, and audience resolution
- TEST versus PRODUCTION execution-context separation
- request validation and throttling

## Layer 4 — Runtime & Service Bindings

Responsibilities include:

- request routing
- context resolution
- middleware
- handlers
- response orchestration
- Neon connectivity
- R2 object access
- secret bindings
- optional queue/cache/coordination adapters

Optional provider features are not assumed core architecture.

## Layer 5 — Application & Governed Knowledge Services

Core Project-Enki capabilities remain reusable and governed. These are responsibility classes and MAY share implementation components where doing so does not weaken governance or separation:

- capture and ingestion
- entity and relationship normalization
- immutable evidence and derivation lineage
- attributable assertion management
- knowledge-state management
- contextual state
- reconciliation and interpretation
- retrieval and search
- projection and view generation
- packaging
- governed disclosure and delivery

Project-Enki distinguishes **portable knowledge semantics** from **consumer-specific product semantics**.

Domain-originating evidence, assertions, relationships, semantic structures, temporal state, governed vocabularies, and reconciliation state MAY belong to Project-Enki when they represent portable governed knowledge whose provenance, authority, lifecycle, or reuse must survive beyond one consumer. This includes person-, organization-, project-, career-, research-, media-, consulting-, or other domain-originating knowledge when the knowledge object itself is portable.

Consumer-specific workflows, scoring and ranking policies, recommendations, dispositions, optimization objectives, presentation models, product success criteria, and local execution policy remain with the consumer.

A repeated downstream need does not automatically justify promotion into Project-Enki. Conversely, a domain label does not automatically disqualify a knowledge object from Project-Enki. Core admission is based on whether the object is a shared governed knowledge object or epistemic contract, rather than which product first encountered it.

The preferred response is the smallest stable knowledge primitive, contract, registry, port, or adapter that preserves downstream value while keeping consumer workflow and decision semantics local.

## Layer 6 — Governance & Governed Execution

All canonical mutation and governed action passes through explicit control mechanisms:

- authority and approval grants
- policy evaluation
- provenance and lineage
- transaction coordination
- reservations and conflict prevention
- receipts and attestations
- model-ingestion and model-feedback controls
- revocation, consumption, retry, rollback, and recovery semantics

No direct canonical writes are permitted outside governed paths.

## Layer 7 — Persistence, Recovery & Lifecycle

Responsibilities include:

- append-only journals
- snapshots and checkpoints
- deterministic replay
- forensic reconstruction
- retention and archival
- tombstoning and redaction
- recovery and reconciliation
- conflict handling
- backup and export/import
- audit and compliance evidence

Historical truth is preserved even when current authority changes.

## Layer 8 — Storage Adapters & Physical Persistence

Physical-provider implementation is isolated behind adapters.

Core adapters for `CF-NEON-R2`:

- Neon relational adapter
- R2 object adapter

Optional adapters may include:

- search indexes
- caches
- queues
- coordination stores

Adapter adoption must not create a second uncontrolled source of canonical truth.

## Layer 9 — Canonical Record & Knowledge Model

The lowest logical layer defines stable record families and relationships.

Representative families include:

- Tenant / namespace
- Domain / governed semantic term
- Subject / subject reference
- Source
- Artifact / immutable representation
- Assertion
- Evidence
- Derivation / extraction lineage
- Confidence
- Interpretation
- Context
- Authority state
- Approval grant
- Transition
- Provenance
- Lineage
- Policy
- Reconciliation finding
- Conflict record
- Semantic registry / mapping
- Projection reference
- Disclosure receipt
- Transaction journal
- Reservation
- Transaction receipt
- Model-ingestion policy
- Model-feedback receipt
- Work-control record
- Sprint record
- Retention / tombstone state
- Snapshot / checkpoint
- Recovery record
- Audit event

The record model may preserve governed knowledge about Person-Objects, organizations, projects, artifacts, and other subjects without requiring one monolithic product domain model to become the Enki kernel.

Temporal semantics must distinguish, as applicable:

- `recorded_at`
- `effective_from`
- `effective_to`
- `superseded_at`
- authority-valid time
- revocation and consumption time

## Cross-cutting planes

### Governance & Authority Plane

Spans Layers 2–9 and governs authorization, approval, policy, delegation, revocation, decision rights, and human authority.

### Security & Privacy Plane

Spans Layers 2–9 and governs identity, tenant and subject isolation, secrets, encryption, consent, privacy, redaction, disclosure scope, and least privilege.

### Observability & Audit Plane

Spans Layers 2–9 and provides privacy-preserving metrics, traces, logs, receipts, health signals, forensic reconstruction, and immutable audit evidence.

### Portability & Recovery Plane

Spans Layers 2–9 and governs export/import, backup, disaster recovery, provider exit, replay, reconstruction, rollback, migration, and evidence continuity.

## Architectural invariants

1. Historical truth and current authority remain distinct.
2. Evidence precedes assertion where evidence is required.
3. Human authority remains final for explicitly human-governed decisions.
4. TEST authority cannot satisfy PRODUCTION gates.
5. Canonical mutation is governed, journaled, receipted, and reconstructable.
6. Provider-specific services do not redefine Project-Enki core contracts.
7. Downstream products consume Project-Enki knowledge; their product workflows and decision policies do not become Project-Enki merely because they use shared knowledge.
8. Portable domain-originating knowledge MAY become canonical Enki knowledge through governed provenance, reconciliation, and authority; topic or consumer origin alone does not determine ownership.
9. Canonical structured data has one explicitly designated authority at a time for the applicable scope.
10. Object evidence remains distinguishable from structured canonical state.
11. Portability, lineage, auditability, and recoverability are designed in rather than added later.
12. Current identity resolves to **Project-Enki** before present-tense synthesis or architectural reasoning; historical aliases remain provenance only.
13. Project-Enki core does not depend on consumer implementation code.
14. Every consumer remains independently understandable, deployable, governable, exportable, reconstructable, and replaceable at the integration boundary.
15. Cross-product sharing occurs through governed contracts, ports, events, APIs, projections, or export/import rather than internal reach-through.
16. Shared physical infrastructure must not erase logical data ownership, authority, lifecycle, or separation boundaries.
17. Architectural layers classify responsibilities; they do not mandate one subsystem, service, module, datastore, or deployment unit per layer or responsibility.
18. Core growth requires a knowledge-ownership justification. Similarity, convenience, repeated consumer implementation, or domain label alone is insufficient.
19. Core contraction MUST preserve legitimate downstream dependency value through a compatible contract, adapter, migration, or reconstruction path unless the dependency is explicitly retired by governance.
20. When multiple implementations satisfy the same invariant, Project-Enki SHOULD prefer the smallest stable surface that preserves authority, provenance, temporal semantics, portability, and recovery.
21. Projection is not promotion: consumer-local observations, interpretations, outcomes, or lessons require explicit governed promotion before they become canonical Enki knowledge.
22. A document labeled canonical does not override a later accepted architecture decision that explicitly supersedes its interpretation; current-authority synthesis must follow dated supersession lineage.

## Relationship to deployment candidates

This nine-layer model is the architectural frame. Deployment candidates such as `CF-NEON-R2` map provider services onto the frame but do not alter the model unless a separate governed architecture decision changes the canonical architecture.
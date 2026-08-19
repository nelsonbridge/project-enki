# Project Enki Charter

## Mission

Project Enki exists to transform conversations, observations, experiences, documents, evidence, feedback, and other source artifacts into coherent, traceable, governed, and continuously evolving knowledge.

Enki preserves the distinction between historical truth and current authority. It records where knowledge originated, the context in which it was valid, how confidence was established, what changed, why it changed, and which interpretation should presently govern downstream use.

## Vision

Build a portable knowledge-manufacturing and governance system that can preserve lineage, reconstruct decisions, govern transitions, distinguish evolution from drift, and make validated knowledge reusable across independent products and contexts.

## Core Product Boundary

Project Enki is the foundational knowledge system.

It is not:

- Media Blitz;
- Career Intelligence and Placement / Golden-Nibiru;
- Personal Cognitive Continuity;
- Enterprise Operating Architecture;
- Velocity-8;
- a publishing calendar;
- a behavioral oracle;
- a replacement for explicit human authority.

Media Blitz, Career Intelligence and Placement / Golden-Nibiru, and Personal Cognitive Continuity are downstream product suites that consume governed Enki knowledge through bounded interfaces.

Enterprise Operating Architecture and Velocity-8 remain separate product and consulting lines. They may consume Enki-produced knowledge and evidence, but they do not define Enki or become Enki product workflows.

This product separation does **not** imply that every domain-originating fact or semantic structure remains owned by the consumer that first uses it. Portable governed evidence, assertions, relationships, temporal state, semantic registries, and reconciliation state may belong to Enki when their provenance, authority, lifecycle, or reuse must survive beyond one consumer. The current boundary is governed by `docs/architecture-decisions/ADR-0003-portable-knowledge-ownership-and-consumer-boundary.md`.

## Governing Principles

### Provenance Before Assertion

Every governed claim must preserve its source, context, transformation path, and confidence basis.

### Historical Truth Is Not Current Authority

Earlier states remain reconstructable even when they no longer govern present behavior or downstream decisions.

### Explicit Human Authority

Consequential authority, approval, publication, release, and policy decisions remain explicit and auditable. The system must not manufacture human authorization.

### Evolution Without Drift

Knowledge may be corrected, refined, expanded, restricted, superseded, reversed, retracted, merged, split, or deprecated only through governed transitions with reconstructable lineage.

### Portability by Design

Domain semantics, canonical identifiers, authority rules, evidence lineage, and governed semantic mappings must remain independent of any single provider, repository host, model, workflow engine, storage adapter, or downstream consumer.

### Portable Knowledge Ownership

Knowledge ownership is determined by epistemic function and authority, not by topic or by which consumer first encountered the information.

A portable knowledge object may originate in a career, personal, research, media, consulting, organizational, or other context and still become governed Enki knowledge when explicit promotion preserves provenance, reconciliation, and authority.

Consumer-specific workflow, scoring, recommendation, optimization, presentation, and product decision semantics remain local to the consumer.

### Downstream Products Are Consumers

A downstream product may transform governed knowledge into product-specific outputs. It may not silently redefine canonical Enki knowledge or acquire core mutation authority.

Projection is not promotion. Consumer-local observations, outcomes, interpretations, preferences, or lessons require a governed promotion path before becoming canonical Enki knowledge.

### Architecture Has Temporal Authority Too

Repository architecture must preserve the distinction between historical architectural truth and current governing interpretation. A later accepted decision may supersede an older canonical statement without erasing the older record. Material conflicts between later design evidence and repository canon must be reconciled before architecture or schema freeze.

## Core Capabilities

1. Source capture and evidence preservation.
2. Canonical knowledge manufacturing.
3. Contextual knowledge-state management.
4. Governed transition and authority resolution.
5. Lineage reconstruction and forensic audit.
6. Evolution-versus-drift validation.
7. Controlled model feedback and revocation.
8. Portable export, import, recovery, and adapter substitution.
9. Multi-consumer boundary enforcement.
10. Explicit human approval and stewardship.
11. Governed semantic registries and cross-context knowledge mappings.
12. Conflict, contradiction, supersession, and unresolved-state preservation without silent reconciliation.

## Success Measures

Primary indicators include:

- provenance completeness;
- authority clarity;
- deterministic reconstruction;
- governed transition integrity;
- portability and recovery proof;
- consumer-boundary enforcement;
- evidence-backed evolution without historical erasure;
- explicit conflict and uncertainty state;
- reduced ambiguity in downstream decision and product use.

## Failure Modes

Enki fails if it:

- overwrites history;
- confuses historical evidence with current authority;
- promotes inference as fact without governance;
- lets a downstream product redefine the parent system;
- forces portable canonical knowledge into consumer-owned silos solely because of topic or origin;
- binds domain semantics to one provider, model, or consumer;
- silently manufactures approval;
- permits unreconstructable canonical changes;
- silently collapses contradictory identity, evidence, or authority claims instead of preserving explicit conflict, qualification, supersession, or unresolved state;
- allows stale architectural authority to govern after an explicit later supersession.

## Authority Rule

This charter defines the current parent-system identity and product boundary for Project Enki together with accepted architecture decisions that explicitly supersede earlier interpretations. Historical artifacts may retain earlier names and earlier boundary models as provenance, but current authoritative documentation, package metadata, navigation, and system descriptions must identify the parent system as **Project Enki** and follow current supersession lineage.
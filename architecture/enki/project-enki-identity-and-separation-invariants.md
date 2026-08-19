# Project-Enki — Identity and Separation Invariants

## Purpose

Project-Enki is the authoritative product/system name. The repository is `nelsonbridge/project-enki`.

Historical names, shorthand, and prior descriptions may remain in historical source material for provenance. They do not govern current product identity.

This document also defines the separation rules required when Project-Enki provides shared knowledge infrastructure to independent products, projects, research systems, or consulting offerings.

The current knowledge-ownership boundary is governed by `docs/architecture-decisions/ADR-0003-portable-knowledge-ownership-and-consumer-boundary.md`.

## Identity invariant

Current architectural reasoning, generated documentation, cross-project synthesis, product descriptions, and present-tense references MUST resolve the product/system identity to **Project-Enki** before generation.

Historical material MAY retain the label used at the time. Historical labels MUST NOT be promoted to current authority merely because they are frequent, recent, or retrieved alongside current material.

When identity is ambiguous, resolution fails closed rather than guessing.

Machine-readable authority is defined in `contracts/project-enki-identity-v1.json`. Executable resolution is implemented in `src/nks/enki/product_identity.py`.

## Foundation without captivity

Project-Enki may provide shared knowledge infrastructure without absorbing the identity, workflow, decision policy, local authority, or lifecycle of the systems that consume it.

No consumer becomes a Project-Enki module merely because it uses Project-Enki contracts, lineage, provenance, temporal semantics, governance, retrieval, persistence, shared vocabularies, or canonical knowledge.

Likewise, Project-Enki MUST NOT require consumer-specific implementation internals in order to operate.

A consumer may originate evidence or observations that later become governed Project-Enki knowledge. Origin does not determine permanent ownership. Promotion into Enki requires provenance, reconciliation, applicable authority, and an explicit governed transition.

## Separation invariants

1. **Independent bounded contexts.** Each consumer owns its product workflows, product-specific domain behavior, decision policies, success criteria, presentation model, and local execution authority. Consumers do not automatically own portable canonical knowledge merely because they first produced or used it.
2. **One-way implementation dependency.** Consumers may depend on Project-Enki contracts or ports. Project-Enki core MUST NOT depend on consumer implementation code.
3. **No internal reach-through.** Cross-system integration occurs through versioned contracts, ports, events, APIs, projections, or governed export/import. A system may not rely on another system's private classes, filesystem paths, database tables, or secrets.
4. **Local authority remains local.** Shared grammar and shared knowledge do not transfer product decision authority. Cross-namespace promotion requires reconciliation and an explicit authority decision.
5. **Independent data ownership where appropriate.** Shared physical infrastructure is permitted, but logical credentials, migrations, retention, export, and reconstruction boundaries remain separable. Canonical knowledge ownership is governed by epistemic function and authority rather than by deployment location or consumer origin.
6. **Independent deployment.** Each offering must be capable of a separately versioned deployment, rollback, configuration, secrets boundary, and observability boundary.
7. **Independent lifecycle.** One offering may be paused, forked, sold, licensed, retired, rewritten, or moved without requiring equivalent lifecycle action in Project-Enki or another consumer.
8. **Portable reconstruction.** Each offering retains enough of its own product state, policy, and contracts to reconstruct its operation without another consumer's source code. Shared Enki knowledge may be reconstructed through governed Enki interfaces and export packages rather than duplicated as consumer-owned truth.
9. **No workflow leakage into the foundation.** Product-specific workflow, scoring, ranking, recommendation, optimization, presentation, and outcome logic do not enter Project-Enki merely because multiple consumers use similar patterns.
10. **Portable knowledge may cross domain boundaries.** Domain-originating evidence, assertions, relationships, semantic structures, temporal state, governed vocabularies, and reconciliation state MAY belong to Project-Enki when they are portable governed knowledge objects whose provenance, authority, lifecycle, or reuse must survive beyond one consumer.
11. **Provider replaceability.** Consumers should depend on stable knowledge/evidence/lineage ports rather than provider-specific Project-Enki implementation details where practical.
12. **Projection is not promotion.** A consumer projection of Enki knowledge does not transfer canonical mutation authority. A consumer-local observation, inference, outcome, preference, or lesson remains local until explicitly promoted through governed reconciliation.

## Core admission and contraction rules

Project-Enki SHOULD remain the smallest foundation that can preserve its knowledge-manufacturing, governance, lineage, temporal, portability, reconciliation, and recovery obligations while supporting valuable downstream use.

A capability, semantic structure, or knowledge object belongs in Project-Enki core when at least one of the following is true:

- it is required to capture, preserve, derive, reconcile, govern, retrieve, disclose, replay, recover, or transport knowledge independently of any particular consumer;
- it is a portable governed knowledge object whose provenance, authority, temporal lifecycle, semantic identity, or reuse must survive beyond one consumer;
- it is required to preserve a stable shared contract or semantic registry on which governed consumers legitimately depend; or
- a separate architecture decision establishes that the capability is foundational knowledge infrastructure rather than consumer-domain behavior.

The following do **not** by themselves justify promotion into core:

- similar implementations appearing in more than one consumer;
- convenience reuse;
- a consumer-specific workflow becoming broadly useful;
- shared terminology without shared semantic identity or governed mappings;
- a domain label such as career, personal, research, media, consulting, or organizational;
- implementation proximity inside the same repository or deployment.

The governing test is not "is this domain-specific?" but:

> Is this a portable governed knowledge object or epistemic contract, or is it consumer-specific workflow, decision, orchestration, presentation, or outcome logic?

When a stable knowledge primitive can preserve downstream value, Project-Enki SHOULD expose that primitive rather than absorb the consumer workflow around it. When knowledge can remain consumer-local without weakening provenance, authority, portability, reconstruction, semantic reuse, reconciliation, or governed interoperability, it may remain local. Consumer-local is no longer a default based solely on topic or origin.

Core contraction is governed by compatibility, not by code-count reduction alone. A core capability MAY be consolidated, simplified, or removed only when either no governed consumer depends on its contract or a compatible contract, adapter, migration, or reconstruction path preserves the downstream semantics and authority boundary. Tightening Project-Enki MUST NOT silently strand a valuable downstream dependency or force portable canonical knowledge back into consumer-owned silos.

Architectural layers classify responsibilities; they do not require one subsystem, service, module, or deployment unit per responsibility. Implementation SHOULD prefer the fewest stable components that satisfy the invariants.

## Person-Object boundary

A Person-Object is a legitimate governed subject/object representation that may draw on Project-Enki canonical knowledge without becoming the Enki kernel's mandatory domain model.

Project-Enki MAY preserve and reconcile portable person-level knowledge such as identity references, relationships, employment history, roles, capabilities, education, credentials, work products, preferences, constraints, compensation events, locations, outcomes, and other evidence-backed assertions when applicable authority permits it.

Consumers remain free to build career, continuity, research, consulting, or other product behavior on top of that knowledge. Those consumer workflows do not become Enki merely because they depend on the same Person-Object assertions.

## Lift-and-Separate Test

For every consumer or sibling development effort, architecture review asks:

> If this repository were moved to a different organization and Project-Enki were replaced by a compatible adapter, could the offering's product logic, local authority, local state, and purpose still be understood and reconstructed without taking another product's source code with it?

A negative answer indicates architectural captivity and requires remediation.

This test does not require each consumer to duplicate portable canonical knowledge already owned by Enki. A compatible export, projection, or adapter may satisfy reconstruction.

## Reverse-dependency test

For every consumer, Project-Enki architecture review also asks:

> Could Project-Enki continue operating if this consumer disappeared completely?

The required answer is **yes**.

Knowledge originally contributed by that consumer may remain historically and canonically valid if it was previously promoted through governed Enki authority. The consumer's disappearance must not erase that history.

## Architecture temporal-authority rule

Architecture itself follows the same historical-truth/current-authority distinction that Enki applies to knowledge.

A document may remain historically authentic while a later accepted architecture decision supersedes its governing interpretation. Current synthesis MUST follow explicit supersession lineage rather than assuming that a file labeled `canonical` or `invariant` is temporally final.

Conversation and project-folder design streams may contain later architecture evidence. They are not automatically canonical, but material conflict between later design evidence and repository authority MUST be reconciled before schema freeze, architecture freeze, or authoritative synthesis.

## Historical truth versus current authority

Separation applies to naming, semantics, and architecture decisions as well as data and code. Historical identities and earlier boundary interpretations remain historically true. Current identity and current knowledge ownership are independently governed.

This preserves provenance without allowing legacy terminology or stale boundary assumptions to regress the current system architecture.
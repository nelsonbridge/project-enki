# Project-Enki — Identity and Separation Invariants

## Purpose

Project-Enki is the authoritative product/system name. The repository is `nelsonbridge/project-enki`.

Historical names, shorthand, and prior descriptions may remain in historical source material for provenance. They do not govern current product identity.

This document also defines the separation rules required when Project-Enki provides shared infrastructure to independent products, projects, research systems, or consulting offerings.

## Identity invariant

Current architectural reasoning, generated documentation, cross-project synthesis, product descriptions, and present-tense references MUST resolve the product/system identity to **Project-Enki** before generation.

Historical material MAY retain the label used at the time. Historical labels MUST NOT be promoted to current authority merely because they are frequent, recent, or retrieved alongside current material.

When identity is ambiguous, resolution fails closed rather than guessing.

Machine-readable authority is defined in `contracts/project-enki-identity-v1.json`. Executable resolution is implemented in `src/nks/enki/product_identity.py`.

## Foundation without captivity

Project-Enki may provide shared knowledge infrastructure without absorbing the identity, semantics, authority, or lifecycle of the systems that consume it.

No consumer becomes a Project-Enki module merely because it uses Project-Enki contracts, lineage, provenance, temporal semantics, governance, retrieval, or persistence capabilities.

Likewise, Project-Enki MUST NOT require consumer-specific internals in order to operate.

## Separation invariants

1. **Independent bounded contexts.** Each consumer owns its domain model, workflows, terminology, policy, success criteria, and local authority.
2. **One-way dependency direction.** Consumers may depend on Project-Enki contracts or ports. Project-Enki core MUST NOT depend on consumer implementation code.
3. **No internal reach-through.** Cross-system integration occurs through versioned contracts, ports, events, APIs, or governed export/import. A system may not rely on another system's private classes, filesystem paths, database tables, or secrets.
4. **Local authority remains local.** Shared grammar never transfers authority. Cross-namespace promotion requires reconciliation and an explicit authority decision.
5. **Independent data ownership.** Shared physical infrastructure is permitted, but logical ownership, credentials, migrations, retention, export, and reconstruction boundaries remain separable.
6. **Independent deployment.** Each offering must be capable of a separately versioned deployment, rollback, configuration, secrets boundary, and observability boundary.
7. **Independent lifecycle.** One offering may be paused, forked, sold, licensed, retired, rewritten, or moved without requiring equivalent lifecycle action in Project-Enki or another consumer.
8. **Portable reconstruction.** Each offering retains enough of its own domain state and contracts to reconstruct its operation without another consumer's source code.
9. **No semantic leakage into the foundation.** A concept belongs in Project-Enki only when it is genuinely product-neutral knowledge machinery. Similar concepts in multiple consumers do not automatically become Project-Enki core.
10. **Provider replaceability.** Consumers should depend on stable knowledge/evidence/lineage ports rather than provider-specific Project-Enki implementation details where practical.

## Core admission and contraction rules

Project-Enki SHOULD remain the smallest foundation that can preserve its knowledge-manufacturing, governance, lineage, temporal, portability, and recovery obligations while supporting valuable downstream use.

A capability or concept belongs in Project-Enki core only when at least one of the following is true:

- it is required to capture, preserve, reconcile, govern, retrieve, disclose, replay, recover, or transport knowledge independently of any particular consumer;
- it is required to preserve a stable product-neutral contract on which governed consumers legitimately depend; or
- a separate architecture decision establishes that the capability is foundational infrastructure rather than consumer-domain behavior.

The following do **not** by themselves justify promotion into core:

- similar implementations appearing in more than one consumer;
- convenience reuse;
- a consumer-specific workflow becoming broadly useful;
- shared terminology without shared authority or semantics; or
- implementation proximity inside the same repository or deployment.

When a product-neutral primitive can preserve downstream value, Project-Enki SHOULD expose that primitive rather than absorb the consumer workflow around it. If a concept can remain consumer-local without weakening provenance, authority, portability, reconstruction, or governed interoperability, consumer-local is the default location.

Core contraction is governed by compatibility, not by code-count reduction alone. A core capability MAY be consolidated, simplified, or removed only when either no governed consumer depends on its contract or a compatible contract, adapter, migration, or reconstruction path preserves the downstream semantics and authority boundary. Tightening Project-Enki MUST NOT silently strand a valuable downstream dependency.

Architectural layers classify responsibilities; they do not require one subsystem, service, module, or deployment unit per responsibility. Implementation SHOULD prefer the fewest stable product-neutral components that satisfy the invariants.

## Lift-and-Separate Test

For every consumer or sibling development effort, architecture review asks:

> If this repository were moved to a different organization and Project-Enki were replaced by a compatible adapter, could the offering's domain logic, authority, state, and purpose still be understood and reconstructed without taking another product's source code with it?

A negative answer indicates architectural captivity and requires remediation.

## Reverse-dependency test

For every consumer, Project-Enki architecture review also asks:

> Could Project-Enki continue operating if this consumer disappeared completely?

The required answer is **yes**.

## Historical truth versus current authority

Separation applies to naming as well as data and code. Historical identities remain historically true. Current identity is independently governed.

This preserves provenance without allowing legacy terminology to regress the current system boundary.

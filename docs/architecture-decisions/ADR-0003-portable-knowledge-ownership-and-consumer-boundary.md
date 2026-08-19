# ADR-0003: Portable Knowledge Ownership and Consumer Boundary

- Status: Accepted
- Date: 2026-08-18
- Governing scope: Project-Enki core boundary, Person-Object knowledge, downstream consumers, shared vocabularies, and architecture-reconciliation precedence
- Supersedes in part: the broad consumer-local semantic interpretation in `ADR-0002-enki-cognitive-core-boundary.md`, `project-enki-identity-and-separation-invariants.md`, and the canonical nine-layer architecture as written before this decision

## Context

Project-Enki originally tightened its core boundary to prevent downstream products from leaking their workflows, product logic, success criteria, and local authority into the parent knowledge system. That restraint remains valid.

Subsequent architecture work exposed an overreach in that rule. The earlier wording treated topic or domain origin as a proxy for knowledge ownership. In practice, facts and assertions about a person, organization, project, role, capability, credential, preference, compensation event, location, outcome, or other domain object may be portable governed knowledge used by several independent consumers. Keeping those knowledge objects inside the first consumer that happened to need them would recreate consumer-owned silos and undermine Enki's portability, lineage, reconciliation, and reconstruction goals.

The architecture therefore needs to distinguish **portable knowledge semantics** from **consumer-specific product semantics**.

## Decision

### 1. Knowledge ownership is determined by epistemic function, not topic

Project-Enki MAY own domain-originating evidence, assertions, relationships, semantic structures, temporal state, governed vocabularies, and reconciliation state when they are portable knowledge objects whose provenance, authority, lifecycle, or reuse must survive beyond one consumer.

A concept does not belong outside Enki merely because it concerns careers, people, research, media, consulting, organizations, or another recognizable domain.

Likewise, a concept does not belong inside Enki merely because several consumers use it.

The governing question is:

> Is this a portable governed knowledge object or epistemic contract, or is it a consumer-specific workflow, decision policy, orchestration rule, presentation concern, or outcome model?

### 2. Consumers retain product semantics and local decisions

Downstream consumers continue to own their product-specific:

- workflows and orchestration;
- scoring and ranking policies;
- recommendations and dispositions;
- optimization objectives;
- presentation and interaction models;
- product success criteria;
- local authority and execution policy;
- local state that has not been promoted through an explicit Enki knowledge-governance path.

For example, Golden-Nibiru may consume governed employment, capability, credential, compensation, location, preference, and outcome assertions without owning those assertions canonically. Golden-Nibiru still owns job-fit interpretation, opportunity screening, include/hold/exclude policy, application workflow, and career-specific recommendation logic.

### 3. Person-Object knowledge is not synonymous with a consumer-owned Person domain model

Project-Enki may preserve and reconcile governed knowledge about a Person-Object without making a monolithic Person class the core domain model.

Portable person-level knowledge may include identity references, relationships, employment history, roles, capabilities, education, credentials, work products, preferences, constraints, compensation events, locations, outcomes, and other governed assertions when supported by evidence and applicable authority.

Product-specific psychological ranking, career decision logic, social-profile optimization, or other consumer outcome models remain outside core unless separately justified as portable knowledge infrastructure.

### 4. The current logical flow is Enki ingestion -> Enki coherence -> consumer projection

The architecture preserves the logical sequence:

1. **Ingestion and evidence ownership** — capture source identity, immutable snapshots or equivalent representations, provenance, derivation lineage, and attributable assertions.
2. **Coherence and governed interpretation** — reconcile relationships, temporal state, conflict, authority, confidence, and contextual evidence meaning without allowing a consumer to silently rewrite canonical knowledge.
3. **Consumer projection** — expose bounded references and governed views for downstream product-specific interpretation and action.

This sequence defines responsibility and authority flow. It does not require three separately deployed services or modules.

### 5. Shared vocabularies may be Enki-governed without becoming one universal ontology

Enki may own versioned registries, namespaces, mappings, and compatibility rules required for shared assertion semantics across consumers.

A consumer-specific vocabulary may remain namespaced and local while still participating in governed mappings. Promotion of a term into a broader Enki namespace requires explicit governance and evidence of a genuinely shared semantic object, not mere frequency of use.

### 6. Projection is not promotion

A consumer projection of Enki knowledge does not transfer canonical mutation authority to the consumer.

A consumer-local observation, inference, outcome, preference, or lesson does not become canonical Enki knowledge merely because it is exported back. Promotion requires provenance, reconciliation, applicable authority, and an explicit governed transition.

### 7. Architecture evolution must preserve temporal authority

A document labeled `canonical` is not sufficient evidence that its interpretation remains current if later architectural decisions materially supersede it.

Repository architecture reviews MUST distinguish:

- historical architectural truth;
- current governing interpretation;
- later design evidence not yet promoted into repository authority.

Conversation and project-folder design streams may contain later architectural evidence. They are not automatically canonical, but a material conflict between later design evidence and repository canon blocks schema freeze or authoritative synthesis until the conflict is reconciled through a dated repository decision.

Superseded architecture is preserved and explicitly linked rather than silently rewritten solely to erase the prior interpretation.

## Consequences

### Positive

- Enki can support portable Person-Objects and other cross-context objects without turning the first consumer into the canonical owner of shared knowledge.
- Golden-Nibiru and later consumers can reuse the same governed assertions without duplicating evidence or silently reconciling conflicts.
- Core restraint remains intact at the workflow and decision-policy boundary.
- Architecture reviews gain an explicit temporal-authority rule, reducing the risk that stale canonical text overrides newer governed design.

### Cost

- Core admission review must distinguish portable knowledge semantics from consumer workflow semantics rather than relying on domain labels.
- Existing documentation that says domain-specific concepts are presumptively consumer-local requires reconciliation.
- Shared semantic registries and projection contracts must preserve namespace, authority, and lifecycle boundaries.

## Non-goals

This decision does not:

- freeze a final Person-Object ontology;
- make Golden-Nibiru or any other consumer part of Project-Enki core;
- authorize a universal psychological, maturity, fit, or coherence score;
- transfer consumer decision authority into Enki;
- make conversation history canonical without promotion;
- require one physical subsystem per logical responsibility.

## Required Follow-Up

1. Reconcile the canonical nine-layer architecture and identity/separation invariants with this decision.
2. Mark earlier proposed architecture documents where this decision supersedes their consumer-local semantic interpretation.
3. Audit Golden-Nibiru, Mittens Observatory, Lord Harbor, and other linked consumers for stale boundary assumptions.
4. Re-run the Enki pre-schema research and challenge only after the repository boundary is current.

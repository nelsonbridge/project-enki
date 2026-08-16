# Enki Temporal Knowledge Graph v1

## Purpose

Enki requires a graph model that can represent not only what is known, but how knowledge, interpretation, decisions, and authority evolve through time.

The Temporal Knowledge Graph (TKG) extends Enki's storage-independent knowledge graph into a governed temporal lineage model. It is designed to support three related but non-collapsed uses:

1. cognitive lineage: the evolution of a person's observations, questions, hypotheses, interpretations, decisions, and later revisions;
2. behavioral/observatory lineage: observed model or agent behavior across contexts, interventions, outcomes, corrections, and later recurrence;
3. project/institutional lineage: the evolution of project assumptions, evidence, decisions, implementations, outcomes, and learning.

The same grammar may be used across these scopes. The scopes do not share authority merely because they share a grammar.

## Core principle

The graph must preserve the difference between:

- what happened;
- what was observed;
- what was claimed;
- what was believed or hypothesized;
- what evidence supported or contradicted it;
- what interpretation governed at a given time;
- who or what possessed authority to change that governing interpretation;
- what later changed;
- why it changed.

A later state may supersede current authority without rewriting historical truth.

## Common node grammar

The v1 common node vocabulary is intentionally generic:

| Node type | Meaning |
|---|---|
| `source` | Raw originating material or source reference. |
| `observation` | A bounded report of what was observed. |
| `claim` | A proposition asserted by a source or actor. |
| `assumption` | A proposition provisionally treated as true for reasoning or execution. |
| `question` | An unresolved inquiry that may drive investigation. |
| `hypothesis` | A testable or evaluable candidate explanation. |
| `evidence` | Material bearing on one or more claims, assumptions, or hypotheses. |
| `interpretation` | A contextual reading or synthesis of evidence and claims. |
| `decision` | A choice made under a defined authority and context. |
| `action` | An executed step taken because of or in relation to a decision. |
| `outcome` | An observed result following an action, event, or decision. |
| `contradiction` | A recorded incompatibility requiring resolution or qualification. |
| `authority` | A record of authority, approval, delegation, revocation, or governing scope. |
| `context` | Conditions under which other nodes were valid, available, selected, or applied. |
| `transition` | A governed change in state or authority. |
| `lesson` | A candidate or governed learning derived from prior evidence and outcomes. |
| `intervention` | A mechanism intended to alter later behavior or execution. |

Domain-specific node types may extend this vocabulary but may not redefine the temporal or authority semantics below.

## Common edge grammar

| Edge type | Meaning |
|---|---|
| `derived_from` | The target was derived from the source. |
| `supports` | The source provides positive evidentiary support for the target. |
| `contradicts` | The source conflicts with the target and creates resolution work. |
| `bounded_by` | The target is constrained by the source boundary. |
| `interprets` | The source interpretation addresses the target material. |
| `tests` | The source evaluates the target hypothesis or assumption. |
| `informs` | The source contributed to, but did not alone determine, the target. |
| `decided_from` | The decision was made from the referenced basis. |
| `acted_on` | The action implements or responds to the target decision. |
| `resulted_in` | The source action or event preceded the target outcome; this edge is temporal, not automatically causal. |
| `candidate_cause_of` | A causal relationship is proposed but not yet established as governed fact. |
| `supersedes` | The source replaces the target for current authority while preserving the target historically. |
| `revises` | The source changes an earlier interpretation, assumption, hypothesis, or lesson without erasing it. |
| `governed_by` | The source is subject to the target authority or policy. |
| `occurred_in` | The source was valid or observed in the target context. |
| `selected_from` | The source was selected from a larger potentially available context or evidence set. |
| `exposed_to` | The source actor/context was exposed to the target intervention or information. |

No edge named `caused` exists in v1. Causality must remain evidence-backed and explicitly promoted from candidate causal reasoning if the governing domain supports such a promotion.

## Required temporal dimensions

Every temporal graph record must distinguish the time of the represented world-state from the time Enki learned or recorded it.

Required or explicitly nullable fields are:

- `recorded_at`: when this graph record entered the governed corpus;
- `effective_from`: when the represented state became effective or applicable;
- `effective_to`: when that state ceased to be effective, when known;
- `authority_from`: when its governing authority began, if any;
- `authority_to`: when its governing authority ended, if any;
- `superseded_at`: when a later governed state superseded this record, if applicable.

Queries over temporal state must support two distinct questions:

- `as_of`: what state was effective at a point in the represented world;
- `known_at`: what Enki had recorded by a point in system knowledge time.

These dimensions must not be collapsed.

## Required provenance and scope

Every record must identify:

- its stable `graph_record_id`;
- `graph_namespace`;
- `node_type` or edge record type;
- `subject_id` when the record is about a subject;
- `domain_id`;
- `context_ids`;
- source/provenance references;
- governing authority state when authority applies;
- current lifecycle status;
- any supersession or revision links.

Unknown values remain unknown. Missing evidence may not be silently inferred.

## Federated graph model

Enki does not require one giant undifferentiated graph.

The preferred model is a federation of graph namespaces that share a common grammar and governed interchange contract.

Examples:

- `cognitive:<subject>` for cognitive lineage;
- `observatory:<subject-or-instance>` for behavioral evidence and adaptation lineage;
- `project:<project-id>` for institutional reasoning and decision lineage;
- other product/domain namespaces adopted later.

A graph namespace owns its domain interpretation. Enki owns the shared contract, provenance requirements, temporal semantics, authority semantics, and cross-namespace promotion controls.

### Federation invariants

1. Shared vocabulary does not imply shared authority.
2. Cross-namespace edges must preserve both source and target namespace identities.
3. A record from one namespace may inform another without becoming canonical there.
4. Promotion into another namespace requires an explicit governed transition or reconciliation decision.
5. Historical records remain reconstructable after promotion, supersession, or rejection.
6. Downstream products may not mutate Enki canonical state directly.
7. Models may propose graph records or relationships but may not manufacture human authority.

## Scope profile A: cognitive lineage

The cognitive profile is designed to map evolving thought without reducing a person to a single present-tense belief set.

A typical chain may be:

`observation -> question -> hypothesis -> evidence -> interpretation -> decision -> outcome -> revision`

The graph must be able to represent that a person considered a hypothesis, assigned it provisional weight, later weakened or rejected it, and perhaps later restored a qualified form under a different context.

An abandoned idea remains historically useful even when it has no current authority.

A cognitive graph is not automatically a psychological profile, trait model, or Person-Object. Those require separate authority and evidence rules.

## Scope profile B: behavioral / observatory lineage

The observatory profile begins with behavior under conditions, not identity.

A typical chain may be:

`interaction -> observation -> context -> behavior -> outcome -> correction/intervention -> later exposure -> adaptation evaluation`

It must preserve differences among:

- context potentially available;
- context actually selected;
- selection mechanism;
- intervention exposure;
- observed behavior;
- later recurrence or non-recurrence;
- interpretation of that behavior.

Persistent patterns may later support hypotheses. They do not authorize identity claims merely by repetition.

## Scope profile C: project / institutional lineage

The project profile captures reasoning history that ordinary Git history cannot represent completely.

A typical chain may be:

`problem -> assumption -> evidence -> hypothesis -> decision -> implementation -> observation -> outcome -> lesson -> adaptation`

A project graph should be able to answer:

- Why does this architecture exist?
- What alternatives were considered?
- Which assumptions governed the decision at the time?
- Which evidence later contradicted them?
- What decision superseded the earlier one?
- Which external project finding informed the change?
- Which learning remains project-local versus promoted to Enki?

## Governed learning-promotion loop

Cross-namespace learning is explicit rather than implicit.

A candidate promotion path is:

`external observation -> candidate learning -> evidence -> reconciliation -> authority decision -> canonical change or supersession`

The reverse path is equally important:

`canonical knowledge -> project application -> unexpected outcome -> contradictory evidence -> candidate revision -> reconciliation -> superseding authority`

The existence of a cross-namespace edge is not itself a promotion.

## Portability

Temporal graph export must include enough information to reconstruct:

- nodes and edges;
- namespace boundaries;
- provenance;
- effective-time history;
- recorded-time history;
- authority windows;
- supersession and revision chains;
- unresolved contradictions;
- schema/contract version.

A provider-specific graph database may accelerate traversal, but no provider-specific representation may become the only reconstructable source of truth.

## Relationship to the canonical nine-layer architecture

The TKG is primarily a Layer 9 contract with responsibilities extending upward:

- Layer 9 defines record, temporal, and relationship semantics;
- Layer 7 guarantees replay, reconstruction, retention, and history preservation;
- Layer 6 governs promotion, authority, mutation, and reconciliation;
- Layer 5 exposes product-neutral temporal retrieval and projection;
- downstream consumers in Layer 1 use stable interfaces and remain isolated from direct canonical mutation.

## v1 success criteria

The first implementation is considered contract-complete when Enki can represent and validate:

1. a historical state later superseded by a new governing state;
2. different answers to `as_of` and `known_at` for the same subject/domain;
3. a contradiction that remains unresolved rather than being silently merged;
4. a cognitive lineage record without converting it into a personality or identity claim;
5. an observatory lineage record without converting repeated behavior into identity authority;
6. a project decision lineage from assumption through outcome and adaptation;
7. a cross-namespace candidate learning that does not become canonical without explicit authority;
8. export/import or replay that preserves temporal and provenance semantics.

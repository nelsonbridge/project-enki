# Project-Enki

Project-Enki is a portable, governed knowledge-manufacturing system for transforming conversations, observations, experiences, documents, evidence, feedback, and other source artifacts into coherent, traceable, continuously evolving knowledge.

It preserves the distinction between historical truth and current authority. Project-Enki records where knowledge originated, the context in which it was valid, how confidence was established, what changed, why it changed, and which interpretation presently governs downstream use.

## Core Responsibilities

Project-Enki provides product-neutral capabilities for:

- provenance and source traceability
- canonical knowledge creation
- contextual and temporal knowledge states
- governed transitions and reconciliation
- lineage reconstruction
- contradiction and supersession handling
- controlled model feedback
- portability, replay, recovery, and auditability
- explicit human authority where required

## Product Boundary

Project-Enki is foundational infrastructure. Independent products and research systems may consume its governed knowledge capabilities without becoming Project-Enki modules.

Current downstream or adjacent efforts retain their own bounded contexts, authority, state, lifecycle, and product rationale. Shared infrastructure does not imply shared product identity.

The architectural separation rules are defined in:

- `architecture/enki/project-enki-identity-and-separation-invariants.md`

The authoritative identity contract is:

- `contracts/project-enki-identity-v1.json`

Current product/system references MUST use **Project-Enki**. Historical names and shorthand may remain in historical source material for provenance, but they do not override current identity.

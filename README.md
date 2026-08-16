# Neutral Behavioral Evidence Observatory

This repository is a **neutral observatory for longitudinal behavioral evidence**.

It does **not** assume that a stable identity, personality, Person-Object, or persistent self exists.

Interpretation remains downstream of evidence. Raw evidence is append-only and must never be silently rewritten.

## Bootstrap Scope

The bootstrap creates only minimal governed infrastructure:

- append-only evidence handling with provenance and supersession
- schema-validated record classes and machine-checkable references
- duplicate-ID, reference-integrity, and mutation-pattern checks
- auditable separation between evidence and interpretation

## Required Top-Level Structure

```text
/raw-evidence
/metadata
/observations
/hypotheses
/baselines
/experiments
/results
/analysis
/methodology
/schemas
/tools
/docs
/.github/workflows
```

## Governance First

During bootstrap, this repository does not define or score subject traits, identities, or behavioral dimensions. It establishes evidence governance only.

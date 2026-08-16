# ADR-0002: Separate Evidence from Interpretation

- **Status:** Accepted
- **Date:** 2026-08-16

## Context

Conflating evidence with interpretation risks turning model output into assumed truth.

## Decision

Maintain strict separation between record classes:

1. `evidence` captures observed/source material and provenance.
2. `observation` references evidence without collapsing uncertainty.
3. `hypothesis` references observations/evidence as testable explanations.
4. `experiment` references hypotheses or competing explanations.
5. `result` references experiments and stores outcomes.
6. `analysis` references results and does not overwrite them.

## Consequences

- Interpretive claims remain downstream of evidence.
- Contradictory observations or results can coexist.
- Validation tooling can enforce reference integrity across classes.

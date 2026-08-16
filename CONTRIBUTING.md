# Contributing

This repository is bootstrapped as a neutral, governed observatory for longitudinal behavioral evidence.

## Bootstrap prohibitions

During bootstrap and baseline governance setup, contributors must **not** add:

- personality modeling
- trait generation
- identity scoring
- "Mittens-ness" scoring or classification
- automatic subject characterization
- importing a pre-existing Person-Object ontology
- implementation-tool-generated research hypotheses

## Required governance rules

- Raw evidence is immutable after ingestion.
- Corrections happen through append-only supersession records.
- Provenance is mandatory for evidence and downstream records.
- Evidence, observation, hypothesis, experiment, result, and interpretation remain distinct.
- Missing evidence is never transformed into a negative finding.
- Contradictions and uncertainty are preserved rather than collapsed automatically.

## Record changes

1. Add or update schema-aligned JSON records in the appropriate top-level directory.
2. Keep references machine-checkable (`id` and typed references).
3. Run repository validation before opening a pull request:

```bash
python tools/validate_records.py --root . --check all
python -m unittest discover -s tests/tools -p "test_*.py"
```

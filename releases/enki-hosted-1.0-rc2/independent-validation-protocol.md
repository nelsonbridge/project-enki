# Sprint 45 Independent Validation Protocol (Zero-Cost)

This protocol defines independent validation for Issue #137 while preserving RC2 architecture authority and the `$0` external-services boundary.

## Required role separation

1. **Implementer** configures the control and prepares reproducible test steps.
2. **Independent reviewer** executes or witnesses execution of validation steps, verifies evidence integrity, and records pass/fail.
3. One person cannot fill both roles for the same control.

## Required tooling profile (zero cost)

- OWASP ZAP baseline scan for HTTP attack-surface regression checks.
- Manual abuse-case execution for identity, tenancy, key, secret, and boundary controls.
- Repository-local/CI command logs and immutable artifact hashes.

## Execution protocol

1. Confirm architecture baseline remains `CF-NEON-R2` via `releases/enki-hosted-1.0-rc2/architecture-lock.json`.
2. Confirm environment classification is production-equivalent hosted free-tier with budget fixed at `$0`.
3. Confirm synthetic or anonymized data only; no real customer data.
4. Confirm secret redaction policy for all logs and reports before testing begins.
5. Execute control checklist item(s) from `production-control-checklist.md`.
6. Run OWASP ZAP baseline where HTTP interfaces are in scope and attach report artifacts.
7. Execute manual abuse cases:
   - forged/expired/revoked/wrong-audience identity tokens,
   - cross-tenant data access attempts,
   - key-rotation and key-revocation misuse attempts,
   - secret exposure probes in logs and error paths,
   - unauthorized network/lateral access attempts.
8. Record evidence using `production-control-evidence-template.json` and validate against `production-control-evidence.schema.json`.
9. Independent reviewer records final pass/fail/partial decision and remediation actions.

## Pass/fail rules

- **PASS**: control behavior and denial paths are validated, evidence is reproducible, and reviewer is independent.
- **PARTIAL**: some required denial/rotation/revocation/failure scenarios are missing or inconclusive.
- **FAIL**: control behavior is broken, evidence cannot be reproduced, reviewer independence is violated, or prohibited data/secret handling occurred.

## Non-negotiable prohibitions

- Do not use real customer data.
- Do not store or publish secret plaintext in evidence artifacts.
- Do not mark unresolved controls as validated.
- Do not claim architecture changes; RC2 lock remains authoritative.

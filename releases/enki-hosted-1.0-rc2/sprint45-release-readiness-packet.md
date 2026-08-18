# Sprint 45 Release Readiness Packet (RC2)

## Authority and operating boundary

- Architecture authority remains `CF-NEON-R2` (`releases/enki-hosted-1.0-rc2/architecture-lock.json`).
- Sprint 45 remains fail-closed by default and cannot self-promote.
- All control validation evidence must remain under `$0.00` external-services cost.

## Release gate checklist

- [ ] All seven Sprint 45 control evidence files exist in `releases/enki-hosted-1.0-rc2/evidence/sprint45/`.
- [ ] Every evidence file validates against `production-control-evidence.schema.json`.
- [ ] Zero-cost validator passes (`scripts/validate_sprint45_zero_cost.py`).
- [ ] Acceptance-gate validator passes fail-closed checks (`scripts/validate_sprint45_acceptance_gates.py`).
- [ ] Independent reviewer identity is present and distinct from implementer for each control.
- [ ] Hosted credential-bound artifacts and hashes are attached for each control.

## Known risks and mitigations

1. **Risk:** Hosted credentials unavailable.  
   **Mitigation:** Use `sprint45-external-handoff-checklist.md` and `scripts/sprint45_independent_reviewer_bundle.ps1` to execute immediately when credentials are available.
2. **Risk:** Non-zero provider cost introduced accidentally.  
   **Mitigation:** Enforced by schema + zero-cost validator; any non-zero cost is a fail condition.
3. **Risk:** Self-attestation without independence.  
   **Mitigation:** Acceptance-gate validator rejects implementer as reviewer and maintains fail-closed PARTIAL.

## Go / no-go criteria under $0 constraints

**GO only if all are true:**
1. All seven controls are independently attested `PASS`.
2. Every evidence record reports `total_observed_cost_usd = 0` and provider checks at `0`.
3. RC2 architecture lock remains `CF-NEON-R2` unchanged.
4. No real customer data or secret plaintext appears in evidence artifacts.

**NO-GO if any are true:**
1. Any control is `PARTIAL` or `FAIL`.
2. Any independent reviewer field is pending/missing or equals implementer.
3. Any observed cost is greater than `0`.
4. Any architecture drift or secret/plaintext policy violation is detected.

## Minimal human actions still required

1. Provide hosted free-tier credentials and execution authority for reviewer runs.
2. Run `scripts/sprint45_independent_reviewer_bundle.ps1` with real hosted endpoint + synthetic tokens.
3. Update all seven evidence JSON files with independent reviewer identity and final control attestations.
4. Attach provider cost-proof artifacts showing exact `$0.00` observed cost.

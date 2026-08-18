# Sprint 45 Production-Control Checklist

Use this checklist to execute and independently validate the seven controls in production-equivalent hosted free-tier conditions.

## Global controls (apply to every item)

- [ ] RC2 architecture lock `CF-NEON-R2` is the tested baseline.
- [ ] Environment is hosted and production-equivalent, but governed under `$0` free-tier constraints.
- [ ] No real customer data is present in test datasets, requests, storage, or evidence.
- [ ] No secret plaintext appears in output artifacts; all secret values are redacted or reference-only.
- [ ] Implementer and independent reviewer identities are distinct and recorded.

## Control checks

### 1) Cloud IAM and least privilege
- [ ] Deny-by-default policy is demonstrable.
- [ ] Least-privilege roles are mapped to required actions only.
- [ ] Unauthorized mutation attempts are denied and captured as evidence.

### 2) Production identity federation controls
- [ ] Forged token is denied.
- [ ] Expired token is denied.
- [ ] Revoked principal/token is denied.
- [ ] Wrong audience token is denied.

### 3) Tenant isolation (database)
- [ ] Row-level isolation policy is enabled and testable.
- [ ] Cross-tenant query attempts are denied.
- [ ] Policy bypass paths are exercised and denied.

### 4) Key management (per-tenant rotation/revocation)
- [ ] Per-tenant key custody boundaries are documented.
- [ ] Rotation procedure executes without cross-tenant impact.
- [ ] Revocation invalidates prior access as expected.

### 5) Secrets handling
- [ ] Secrets are bound from governed secret stores or scoped runtime bindings.
- [ ] Secrets are never committed in repository content.
- [ ] Rotation and revocation are executed and evidenced.
- [ ] Log and artifact review confirms no secret plaintext leakage.

### 6) Network boundaries
- [ ] Public ingress boundaries are explicit and minimal.
- [ ] Service-to-service paths are explicitly constrained.
- [ ] Unauthorized lateral movement attempts are denied and logged.

### 7) Incident and failure exercises
- [ ] Authentication-control failure scenario is executed.
- [ ] Data-isolation failure scenario is executed.
- [ ] Secret-exposure response drill is executed.
- [ ] Recovery and remediation actions are captured with owner and due date.

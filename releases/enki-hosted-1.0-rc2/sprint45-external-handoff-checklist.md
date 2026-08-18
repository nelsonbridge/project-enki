# Sprint 45 External Handoff Checklist (Minimal, Credential-Bound Steps)

Use this checklist only for steps that require hosted credentials/access or independent human reviewer execution.

## Gate state (fail-closed)

Sprint 45 remains **PARTIAL** and fail-closed until all seven control evidence records contain:

1. Hosted credential-bound execution artifacts,
2. Independent reviewer identity (not the implementer),
3. Final PASS/FAIL/PARTIAL attestation based on executed results.

Automation helpers:
- `scripts/sprint45_independent_reviewer_bundle.ps1`
- `scripts/validate_sprint45_zero_cost.py`
- `scripts/validate_sprint45_acceptance_gates.py`

## Preconditions

1. RC2 authority remains unchanged:
   - `architecture_id` must stay `CF-NEON-R2` in `releases/enki-hosted-1.0-rc2/architecture-lock.json`.
2. Budget remains strict zero:
   - free-tier only, no paid plan enablement, no spend authorization.
3. Data/secret safety:
   - no real customer data,
   - no plaintext secrets in logs, screenshots, or evidence files.
4. Cost attestation:
   - every evidence JSON must report `cost_attestation.total_observed_cost_usd = 0`,
   - all `provider_checks[].observed_cost_usd = 0`.

## Exact command set

### A) Validate evidence file shape (local)

```powershell
uv run --with jsonschema python -c "import json,glob; from jsonschema import validate; s=json.load(open('releases/enki-hosted-1.0-rc2/production-control-evidence.schema.json','r',encoding='utf-8')); files=glob.glob('releases/enki-hosted-1.0-rc2/evidence/sprint45/*.json'); [validate(instance=json.load(open(f,'r',encoding='utf-8')), schema=s) for f in files]; print(f'validated {len(files)} files')"
```

Expected output: `validated 7 files`
Acceptance threshold: all 7 evidence files validate with zero schema errors.

### A.1) Reviewer execution order (concise)

Run these in order:

```powershell
# 1) Schema validation for all 7 evidence files
uv run --with jsonschema python -c "import json,glob; from jsonschema import validate; s=json.load(open('releases/enki-hosted-1.0-rc2/production-control-evidence.schema.json','r',encoding='utf-8')); files=glob.glob('releases/enki-hosted-1.0-rc2/evidence/sprint45/*.json'); [validate(instance=json.load(open(f,'r',encoding='utf-8')), schema=s) for f in files]; print(f'validated {len(files)} files')"

# 2) Enforce zero-cost attestation invariants
uv run python scripts/validate_sprint45_zero_cost.py

# 3) OWASP ZAP baseline (hosted endpoint)
docker run --rm -t ghcr.io/zaproxy/zaproxy:stable zap-baseline.py -t https://<hosted-test-endpoint> -r zap-baseline-report.html -J zap-baseline-report.json

# 4) Identity denial-path abuse cases
curl -i -H "Authorization: Bearer <forged_token>" https://<hosted-test-endpoint>/api/<protected-route>
curl -i -H "Authorization: Bearer <expired_token>" https://<hosted-test-endpoint>/api/<protected-route>
curl -i -H "Authorization: Bearer <revoked_token>" https://<hosted-test-endpoint>/api/<protected-route>
curl -i -H "Authorization: Bearer <wrong_audience_token>" https://<hosted-test-endpoint>/api/<protected-route>

# 5) Execute tenant isolation, key/secret lifecycle, network boundary, and incident drills per checklist
# 6) Hash artifacts and update each evidence JSON with reviewer identity + final attestation
Get-FileHash raw-evidence\\sprint45\\*.log -Algorithm SHA256
```

### B) Run OWASP ZAP baseline on hosted endpoint (independent reviewer executes)

```powershell
docker run --rm -t ghcr.io/zaproxy/zaproxy:stable zap-baseline.py -t https://<hosted-test-endpoint> -r zap-baseline-report.html -J zap-baseline-report.json
```

Expected output: completed baseline scan with generated HTML/JSON reports.
Acceptance threshold: high-risk findings resolved or explicitly remediated before marking PASS.

### B.1) Capture provider cost proof immediately after hosted run

```powershell
# Save provider-exported cost proof into raw evidence (dashboard export or API result),
# then hash the files and update cost_attestation.provider_checks[].evidence_location.
Get-FileHash raw-evidence\\sprint45\\billing\\* -Algorithm SHA256
```

Expected output: SHA256 hashes for provider cost-proof artifacts.
Acceptance threshold: all provider checks show observed cost exactly `0.00 USD`.

### C) Execute identity denial abuse cases (hosted; independent reviewer)

```powershell
# Examples (replace with actual endpoint and generated synthetic tokens)
curl -i -H "Authorization: Bearer <forged_token>" https://<hosted-test-endpoint>/api/<protected-route>
curl -i -H "Authorization: Bearer <expired_token>" https://<hosted-test-endpoint>/api/<protected-route>
curl -i -H "Authorization: Bearer <revoked_token>" https://<hosted-test-endpoint>/api/<protected-route>
curl -i -H "Authorization: Bearer <wrong_audience_token>" https://<hosted-test-endpoint>/api/<protected-route>
```

Expected output: denial responses for all invalid tokens.
Acceptance threshold: all invalid token paths deny access and are logged without secret leakage.

### D) Execute tenant isolation abuse case (hosted; independent reviewer)

```powershell
# Use synthetic tenant principals only.
# Attempt tenant-A principal querying tenant-B scoped data through governed path.
```

Expected output: denied cross-tenant access.
Acceptance threshold: zero successful cross-tenant reads/writes.

### E) Execute key and secret lifecycle drills (hosted; independent reviewer)

```powershell
# Rotate tenant key, verify new decrypt path works and old key path is revoked.
# Rotate/revoke secret binding; verify old binding fails and no plaintext secret appears in logs.
```

Expected output: post-rotation success on approved path; revoked path denied.
Acceptance threshold: no cross-tenant impact, no plaintext secret leakage.

### F) Execute network boundary and incident/failure drills (hosted; independent reviewer)

```powershell
# Attempt unauthorized lateral/service path; verify denial.
# Run auth-failure, isolation-failure, and secret-exposure response drills.
```

Expected output: unauthorized paths denied; drill timeline and remediation captured.
Acceptance threshold: all required drills executed with owner+due-date remediation entries for any failures.

## Required evidence completion

For each control file in `releases/enki-hosted-1.0-rc2/evidence/sprint45/`:

1. Replace `independent_reviewer` placeholder with actual reviewer identity.
2. Add hosted execution artifact references and SHA-256 hashes.
3. Update status to PASS/FAIL/PARTIAL based on observed results.
4. Keep `external_services_budget_usd = 0`, `uses_real_customer_data = false`, `allows_secret_plaintext_in_artifacts = false`.
5. Keep `cost_attestation.total_observed_cost_usd = 0` and each `provider_checks[].observed_cost_usd = 0`; otherwise set result to `FAIL` and open remediation.

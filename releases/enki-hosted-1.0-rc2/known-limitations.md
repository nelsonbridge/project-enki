# Known Limitations

> Non-authoritative narrative supporting the hash-bound RC2 manifest.

## Hosted validation

- CF-NATIVE hosted TEST validation is blocked because provider TEST identity, credentials, and teardown authority are unavailable to the current execution surface.
- CF-NEON-R2 hosted TEST validation has not been executed.
- GCP-NEON-R2 hosted TEST validation has not been executed.
- Cross-finalist comparative evaluation has not been completed.
- No production hosting architecture has been selected.

## Cost and capacity

- Repository-local and CI TEST execution is validated under the `$0 external-services` boundary.
- Hosted quotas, latency, storage growth, egress, provider failure behavior, and teardown/reconstruction cost have not been measured end to end.
- Repository-local benchmarks are not production capacity guarantees.

## Production controls

The following controls have explicit validation contracts but remain unresolved as production controls:

1. Cloud IAM.
2. Production identity federation.
3. Managed-database row-level isolation.
4. Network segmentation.
5. Per-tenant production key management.
6. Production secrets management.
7. Independent penetration testing.

Internal TEST adversarial evidence does not substitute for independent validation execution or production-equivalent hosted control validation.

## Sprint 45 governed validation constraints

- Sprint 45 execution is restricted to production-equivalent hosted controls under governed `$0` free-tier constraints.
- Real customer data is prohibited in control-validation environments and evidence artifacts.
- Secret plaintext leakage is prohibited in logs, reports, screenshots, and retained evidence.
- Independent reviewer execution evidence is required; implementer self-certification is not accepted.

## Authority boundary

RC2 does not provide production certification, multitenancy accreditation, hosting selection, production approval, production credentials, production traffic authority, or permission to incur external-services cost.

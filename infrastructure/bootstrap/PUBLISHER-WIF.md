# Artifact Registry Publisher WIF Bootstrap

`publish.yml` uses a publisher-only Google Cloud identity. It must not reuse the Terraform deployer identity because the deployer trust policy is intentionally restricted to `terraform.yml` on `sandbox`.

## Required trust path

- GitHub repository: `nelsonbridge/project-enki`
- Event: `push`
- Ref: `refs/heads/sandbox`
- Workflow: `nelsonbridge/project-enki/.github/workflows/publish.yml@refs/heads/sandbox`
- WIF pool: `github-actions-pool`
- Publisher provider: `github-actions-publisher-oidc`
- Publisher service account: `artifact-registry-publisher@<GCP_PROJECT>.iam.gserviceaccount.com`
- Artifact Registry role: `roles/artifactregistry.writer`, scoped to the `enki-containers` repository

## Run once (safe to rerun)

Prerequisites: an authenticated GCP administrator with permission to manage Workload Identity Federation/service accounts and an existing `github-actions-pool`. If `gh` is installed and authenticated, the script also writes the GitHub Actions repository variables.

```bash
export GCP_PROJECT=enki-test
export GCP_REGION=us-central1
export GITHUB_REPO=nelsonbridge/project-enki
./infrastructure/bootstrap/bootstrap-gcp-publisher.sh
```

The script converges the provider condition, creates the service account if needed, applies the Workload Identity User binding, and grants Artifact Registry writer access only to `enki-containers`.

## GitHub Actions variables

`publish.yml` requires:

- `GCP_PROJECT`
- `GCP_REGION`
- `GCP_AR_WIF_PROVIDER`
- `GCP_AR_SA`

When `gh auth status` succeeds, the bootstrap script sets all four automatically. Otherwise it prints the exact values to add.

## Acceptance test

After the bootstrap completes, create a real push to `sandbox` that matches the `publish.yml` path trigger (or merge a change that does). The successful path is:

1. Governed validation passes.
2. `google-github-actions/auth@v2` exchanges the GitHub OIDC token through `github-actions-publisher-oidc`.
3. The publisher service account authenticates.
4. Docker pushes the image to `enki-containers`.

A `workflow_dispatch` run is not an authentication acceptance test for this identity because the provider condition requires `assertion.event_name == 'push'`.

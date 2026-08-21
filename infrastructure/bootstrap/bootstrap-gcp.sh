#!/usr/bin/env bash
# bootstrap-gcp.sh
#
# One-time bootstrap for Enki GCP infrastructure.
#
# Establishes the root of trust that Terraform itself cannot create before it
# has access:
#   1. Enable prerequisite GCP APIs
#   2. Create Terraform state bucket
#   3. Enable state bucket versioning
#   4. Create GitHub Workload Identity Pool
#   5. Create GitHub OIDC provider (deployer — for terraform.yml)
#   6. Create Terraform deployment service account
#   7. Bind the exact Enki GitHub repository to that service account
#   8. Grant minimum Terraform permissions to the service account
#   9. Create GitHub OIDC provider (publisher — for publish.yml)
#  10. Create Artifact Registry publisher service account
#  11. Bind the publisher identity to the publisher service account
#  12. Grant Artifact Registry write permission to the publisher service account
#
# Prerequisites
#   - gcloud CLI authenticated as a GCP project owner/admin
#   - The GCP project already exists and has billing attached
#
# Usage
#   export GCP_PROJECT=enki-test
#   export GITHUB_REPO=nelsonbridge/project-enki   # owner/repo
#   ./infrastructure/bootstrap/bootstrap-gcp.sh

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration — override via environment variables before running
# ---------------------------------------------------------------------------
GCP_PROJECT="${GCP_PROJECT:-enki-test}"
GCP_REGION="${GCP_REGION:-us-central1}"
GITHUB_REPO="${GITHUB_REPO:-nelsonbridge/project-enki}"

# Derived names — kept consistent so the script is idempotent
STATE_BUCKET="${GCP_PROJECT}-terraform-state"
WIF_POOL_ID="github-actions-pool"
# Deployer OIDC provider (used by terraform.yml)
WIF_PROVIDER_ID="github-actions-oidc"
# Publisher OIDC provider (used by publish.yml)
WIF_PUBLISHER_PROVIDER_ID="github-actions-publisher-oidc"
SA_NAME="terraform-deployer"
SA_EMAIL="${SA_NAME}@${GCP_PROJECT}.iam.gserviceaccount.com"
AR_SA_NAME="artifact-registry-publisher"
AR_SA_EMAIL="${AR_SA_NAME}@${GCP_PROJECT}.iam.gserviceaccount.com"

# GitHub OIDC issuer (fixed by GitHub)
GITHUB_OIDC_ISSUER="https://token.actions.githubusercontent.com"

# Deployer WIF trust constraints
# The OIDC provider attribute-condition is intentionally narrow:
#   - only tokens issued for this exact repository
#   - only push events (not PR, schedule, workflow_dispatch, etc.)
#   - only the protected sandbox branch
#   - only the terraform.yml workflow file on that branch
# This ensures that Copilot PRs and other branch workflows cannot obtain the
# deployer identity regardless of what steps they contain.
DEPLOY_BRANCH="refs/heads/sandbox"
DEPLOY_WORKFLOW="${GITHUB_REPO}/.github/workflows/terraform.yml@${DEPLOY_BRANCH}"

# Publisher WIF trust constraints
# Mirrors the deployer constraints but scoped to publish.yml.
# The publisher service account has Artifact Registry write access only —
# it cannot impersonate the terraform-deployer or administer infrastructure.
PUBLISH_WORKFLOW="${GITHUB_REPO}/.github/workflows/publish.yml@${DEPLOY_BRANCH}"
PUBLISHER_CONDITION="assertion.repository == '${GITHUB_REPO}' && assertion.event_name == 'push' && assertion.ref == '${DEPLOY_BRANCH}' && assertion.workflow_ref == '${PUBLISH_WORKFLOW}'"

DEPLOYER_ATTRIBUTE_MAPPING=(
  "google.subject=assertion.sub"
  # actor and repository_owner are not enforced in the condition but are mapped
  # here for audit trail purposes — they surface in GCP credential audit logs.
  "attribute.actor=assertion.actor"
  "attribute.repository=assertion.repository"
  "attribute.repository_owner=assertion.repository_owner"
  # ref, event_name, and workflow_ref are the enforced restriction claims.
  "attribute.ref=assertion.ref"
  "attribute.event_name=assertion.event_name"
  "attribute.workflow_ref=assertion.workflow_ref"
)
# Join with commas for the gcloud flag
DEPLOYER_ATTRIBUTE_MAPPING_STR=$(IFS=,; echo "${DEPLOYER_ATTRIBUTE_MAPPING[*]}")

DEPLOYER_CONDITION="assertion.repository == '${GITHUB_REPO}' && assertion.event_name == 'push' && assertion.ref == '${DEPLOY_BRANCH}' && assertion.workflow_ref == '${DEPLOY_WORKFLOW}'"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
log() { echo "[bootstrap] $*"; }

# ---------------------------------------------------------------------------
# 0. Target project
# ---------------------------------------------------------------------------
log "Targeting project: ${GCP_PROJECT}"
gcloud config set project "${GCP_PROJECT}"

# ---------------------------------------------------------------------------
# 1. Enable prerequisite GCP APIs
# ---------------------------------------------------------------------------
log "Step 1 — Enabling prerequisite APIs…"
REQUIRED_APIS=(
  "cloudresourcemanager.googleapis.com"
  "iam.googleapis.com"
  "iamcredentials.googleapis.com"
  "sts.googleapis.com"
  "storage.googleapis.com"
  "serviceusage.googleapis.com"
  "secretmanager.googleapis.com"
  "sqladmin.googleapis.com"
  "run.googleapis.com"
  "artifactregistry.googleapis.com"
  "monitoring.googleapis.com"
  "logging.googleapis.com"
  "compute.googleapis.com"
  "servicenetworking.googleapis.com"
)
gcloud services enable "${REQUIRED_APIS[@]}" --project="${GCP_PROJECT}"
log "APIs enabled."

# ---------------------------------------------------------------------------
# 2. Create Terraform state bucket
# ---------------------------------------------------------------------------
log "Step 2 — Ensuring Terraform state bucket exists: gs://${STATE_BUCKET}"
if ! gsutil ls -b "gs://${STATE_BUCKET}" &>/dev/null; then
  gsutil mb \
    -p "${GCP_PROJECT}" \
    -l "${GCP_REGION}" \
    -b on \
    "gs://${STATE_BUCKET}"
  log "Bucket created."
else
  log "Bucket already exists."
fi

# Always enforce security controls regardless of whether the bucket was just
# created or already existed — this makes reruns convergent, not merely
# non-destructive.
log "  Enforcing uniform bucket-level access…"
gsutil uniformbucketlevelaccess set on "gs://${STATE_BUCKET}"
log "  Enforcing public access prevention…"
gsutil pap set enforced "gs://${STATE_BUCKET}"

# ---------------------------------------------------------------------------
# 3. Enable state bucket versioning
# ---------------------------------------------------------------------------
log "Step 3 — Enabling versioning on gs://${STATE_BUCKET}…"
gsutil versioning set on "gs://${STATE_BUCKET}"
log "Versioning enabled."

# ---------------------------------------------------------------------------
# 4. Create GitHub Workload Identity Pool
# ---------------------------------------------------------------------------
log "Step 4 — Creating Workload Identity Pool: ${WIF_POOL_ID}…"
if ! gcloud iam workload-identity-pools describe "${WIF_POOL_ID}" \
     --location=global \
     --project="${GCP_PROJECT}" &>/dev/null; then
  gcloud iam workload-identity-pools create "${WIF_POOL_ID}" \
    --location=global \
    --project="${GCP_PROJECT}" \
    --display-name="GitHub Actions Pool" \
    --description="Workload Identity Pool for GitHub Actions CI/CD"
  log "Workload Identity Pool created."
else
  log "Workload Identity Pool already exists — skipping creation."
fi

# Retrieve the pool's full resource name for use in later steps
WIF_POOL_NAME=$(gcloud iam workload-identity-pools describe "${WIF_POOL_ID}" \
  --location=global \
  --project="${GCP_PROJECT}" \
  --format="value(name)")

# ---------------------------------------------------------------------------
# 5. Create GitHub OIDC provider inside the pool, or update to expected config
#
# The attribute-condition restricts the deployer identity to:
#   - this exact repository
#   - push events only (not pull_request, schedule, workflow_dispatch, etc.)
#   - refs/heads/sandbox only
#   - the terraform.yml workflow file on that branch
#
# On rerun, any existing provider is always updated to the expected mapping
# and condition, making the script convergent rather than merely non-destructive.
# ---------------------------------------------------------------------------
log "Step 5 — Configuring OIDC provider: ${WIF_PROVIDER_ID}…"
if ! gcloud iam workload-identity-pools providers describe "${WIF_PROVIDER_ID}" \
     --workload-identity-pool="${WIF_POOL_ID}" \
     --location=global \
     --project="${GCP_PROJECT}" &>/dev/null; then
  gcloud iam workload-identity-pools providers create-oidc "${WIF_PROVIDER_ID}" \
    --workload-identity-pool="${WIF_POOL_ID}" \
    --location=global \
    --project="${GCP_PROJECT}" \
    --issuer-uri="${GITHUB_OIDC_ISSUER}" \
    --attribute-mapping="${DEPLOYER_ATTRIBUTE_MAPPING_STR}" \
    --attribute-condition="${DEPLOYER_CONDITION}" \
    --display-name="GitHub Actions OIDC (deployer)"
  log "OIDC provider created."
else
  log "OIDC provider already exists — enforcing expected mapping and condition…"
  gcloud iam workload-identity-pools providers update-oidc "${WIF_PROVIDER_ID}" \
    --workload-identity-pool="${WIF_POOL_ID}" \
    --location=global \
    --project="${GCP_PROJECT}" \
    --issuer-uri="${GITHUB_OIDC_ISSUER}" \
    --attribute-mapping="${DEPLOYER_ATTRIBUTE_MAPPING_STR}" \
    --attribute-condition="${DEPLOYER_CONDITION}"
  log "OIDC provider configuration enforced."
fi

# ---------------------------------------------------------------------------
# 6. Create Terraform deployment service account
# ---------------------------------------------------------------------------
log "Step 6 — Creating service account: ${SA_EMAIL}…"
if ! gcloud iam service-accounts describe "${SA_EMAIL}" \
     --project="${GCP_PROJECT}" &>/dev/null; then
  gcloud iam service-accounts create "${SA_NAME}" \
    --project="${GCP_PROJECT}" \
    --display-name="Terraform Deployer" \
    --description="Service account used by GitHub Actions to run Terraform against ${GCP_PROJECT}"
  log "Service account created."
else
  log "Service account already exists — skipping creation."
fi

# ---------------------------------------------------------------------------
# 7. Bind the exact Enki GitHub repository to the service account
#    (attribute.repository == GITHUB_REPO, enforced by the provider condition
#    AND by the principalSet binding below — defence in depth)
# ---------------------------------------------------------------------------
log "Step 7 — Binding repository '${GITHUB_REPO}' → service account…"
gcloud iam service-accounts add-iam-policy-binding "${SA_EMAIL}" \
  --project="${GCP_PROJECT}" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/${WIF_POOL_NAME}/attribute.repository/${GITHUB_REPO}"
log "Binding applied."

# ---------------------------------------------------------------------------
# 8. Grant minimum Terraform permissions to the service account
#
# Role justification:
#   roles/editor is used here as a bootstrap grant because Terraform must be
#   able to create, update, and delete the full set of managed resources
#   (Cloud Run, Cloud SQL, Artifact Registry, Secret Manager, networking,
#   storage) whose exact shapes are not yet known at bootstrap time.
#   roles/iam.securityAdmin and roles/resourcemanager.projectIamAdmin are
#   added separately because roles/editor alone does not grant the ability
#   to write IAM policies, which Terraform needs for resource-level bindings.
#
#   IMPORTANT: Once the Terraform resource set is stable, replace roles/editor
#   with the minimum resource-specific roles actually required (e.g.
#   roles/run.developer, roles/cloudsql.client, etc.) and remove this comment.
#   This tightening should be treated as a follow-on security hardening task.
# ---------------------------------------------------------------------------
log "Step 8 — Granting Terraform permissions to ${SA_EMAIL}…"

TERRAFORM_ROLES=(
  # bootstrap broad grant: roles/editor covers Cloud Run, Cloud SQL, Artifact
  # Registry, Secret Manager, networking, and GCS.  Replace with resource-
  # specific roles once the Terraform resource set is stable (see the role
  # justification comment in Step 8 header above).
  "roles/editor"
  # roles/iam.securityAdmin and roles/resourcemanager.projectIamAdmin are the
  # only permissions NOT covered by roles/editor that Terraform needs to manage
  # resource-level and project-level IAM bindings.
  "roles/iam.securityAdmin"                # write IAM policies on individual resources
  "roles/resourcemanager.projectIamAdmin"  # write project-level IAM bindings
)

for ROLE in "${TERRAFORM_ROLES[@]}"; do
  gcloud projects add-iam-policy-binding "${GCP_PROJECT}" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="${ROLE}" \
    --condition=None
  log "  Granted ${ROLE}"
done

# Grant the service account the ability to create its own short-lived tokens.
# This is required for Workload Identity impersonation flows where the federated
# identity exchanges the OIDC token for a service account access token.
log "  Granting roles/iam.serviceAccountTokenCreator (self-binding for impersonation)…"
gcloud iam service-accounts add-iam-policy-binding "${SA_EMAIL}" \
  --project="${GCP_PROJECT}" \
  --role="roles/iam.serviceAccountTokenCreator" \
  --member="serviceAccount:${SA_EMAIL}"

log "Permissions granted."

# ---------------------------------------------------------------------------
# 9. Create GitHub OIDC provider (publisher — for publish.yml)
#
# A dedicated OIDC provider scoped exclusively to publish.yml is required
# because the deployer provider's attribute-condition explicitly restricts
# access to terraform.yml.  The publisher provider uses the same attribute
# mapping but a different condition that allows only the publish.yml workflow
# on the sandbox branch.  The two providers share the same WIF pool but grant
# access to separate, least-privilege service accounts.
# ---------------------------------------------------------------------------
log "Step 9 — Configuring publisher OIDC provider: ${WIF_PUBLISHER_PROVIDER_ID}…"
if ! gcloud iam workload-identity-pools providers describe "${WIF_PUBLISHER_PROVIDER_ID}" \
     --workload-identity-pool="${WIF_POOL_ID}" \
     --location=global \
     --project="${GCP_PROJECT}" &>/dev/null; then
  gcloud iam workload-identity-pools providers create-oidc "${WIF_PUBLISHER_PROVIDER_ID}" \
    --workload-identity-pool="${WIF_POOL_ID}" \
    --location=global \
    --project="${GCP_PROJECT}" \
    --issuer-uri="${GITHUB_OIDC_ISSUER}" \
    --attribute-mapping="${DEPLOYER_ATTRIBUTE_MAPPING_STR}" \
    --attribute-condition="${PUBLISHER_CONDITION}" \
    --display-name="GitHub Actions OIDC (publisher)"
  log "Publisher OIDC provider created."
else
  log "Publisher OIDC provider already exists — enforcing expected mapping and condition…"
  gcloud iam workload-identity-pools providers update-oidc "${WIF_PUBLISHER_PROVIDER_ID}" \
    --workload-identity-pool="${WIF_POOL_ID}" \
    --location=global \
    --project="${GCP_PROJECT}" \
    --issuer-uri="${GITHUB_OIDC_ISSUER}" \
    --attribute-mapping="${DEPLOYER_ATTRIBUTE_MAPPING_STR}" \
    --attribute-condition="${PUBLISHER_CONDITION}"
  log "Publisher OIDC provider configuration enforced."
fi

# ---------------------------------------------------------------------------
# 10. Create Artifact Registry publisher service account
# ---------------------------------------------------------------------------
log "Step 10 — Creating publisher service account: ${AR_SA_EMAIL}…"
if ! gcloud iam service-accounts describe "${AR_SA_EMAIL}" \
     --project="${GCP_PROJECT}" &>/dev/null; then
  gcloud iam service-accounts create "${AR_SA_NAME}" \
    --project="${GCP_PROJECT}" \
    --display-name="Artifact Registry Publisher" \
    --description="Service account used by GitHub Actions publish.yml to push container images to Artifact Registry"
  log "Publisher service account created."
else
  log "Publisher service account already exists — skipping creation."
fi

# ---------------------------------------------------------------------------
# 11. Bind the publisher identity to the publisher service account
#     Scopes the binding to the exact publish.yml workflow file using
#     attribute.workflow_ref (defence in depth: provider condition AND
#     principalSet both enforce workflow_ref, so terraform.yml tokens
#     cannot impersonate the publisher service account).
# ---------------------------------------------------------------------------
log "Step 11 — Binding repository '${GITHUB_REPO}' → publisher service account…"
WIF_PUBLISHER_PROVIDER_NAME=$(gcloud iam workload-identity-pools providers describe "${WIF_PUBLISHER_PROVIDER_ID}" \
  --workload-identity-pool="${WIF_POOL_ID}" \
  --location=global \
  --project="${GCP_PROJECT}" \
  --format="value(name)")

gcloud iam service-accounts add-iam-policy-binding "${AR_SA_EMAIL}" \
  --project="${GCP_PROJECT}" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/${WIF_POOL_NAME}/attribute.workflow_ref/${PUBLISH_WORKFLOW}"
log "Publisher binding applied."

# ---------------------------------------------------------------------------
# 12. Grant Artifact Registry write permission to the publisher service account
#
# roles/artifactregistry.writer is the minimum permission required to push
# container images to Artifact Registry.  It grants write access to the
# entire project's registries; Terraform may tighten this to a specific
# repository once the enki-containers registry exists.
# ---------------------------------------------------------------------------
log "Step 12 — Granting Artifact Registry write permission to ${AR_SA_EMAIL}…"
gcloud projects add-iam-policy-binding "${GCP_PROJECT}" \
  --member="serviceAccount:${AR_SA_EMAIL}" \
  --role="roles/artifactregistry.writer" \
  --condition=None
log "  Granted roles/artifactregistry.writer"

log "Publisher permissions granted."


WIF_PROVIDER_NAME=$(gcloud iam workload-identity-pools providers describe "${WIF_PROVIDER_ID}" \
  --workload-identity-pool="${WIF_POOL_ID}" \
  --location=global \
  --project="${GCP_PROJECT}" \
  --format="value(name)")

echo ""
echo "============================================================"
echo " Bootstrap complete. Add the following to your repository:"
echo "============================================================"
echo ""
echo " GitHub Actions Variables (Settings → Secrets and variables → Actions → Variables):"
echo "   GCP_PROJECT           = ${GCP_PROJECT}"
echo "   GCP_REGION            = ${GCP_REGION}"
echo "   GCP_WIF_PROVIDER      = ${WIF_PROVIDER_NAME}"
echo "   GCP_SERVICE_ACCOUNT   = ${SA_EMAIL}"
echo "   TF_STATE_BUCKET       = ${STATE_BUCKET}"
echo "   GCP_AR_WIF_PROVIDER   = ${WIF_PUBLISHER_PROVIDER_NAME}"
echo "   GCP_AR_SA             = ${AR_SA_EMAIL}"
echo ""
echo " No secrets are required — authentication uses keyless OIDC/WIF."
echo "============================================================"

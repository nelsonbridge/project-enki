#!/usr/bin/env bash
# bootstrap-gcp-publisher.sh
#
# One-time/convergent bootstrap for the Artifact Registry publisher identity.
# Creates a publisher-only GitHub OIDC provider and service account, grants
# writer access to the Enki Artifact Registry repository, and (when gh is
# authenticated) writes the required GitHub Actions repository variables.

set -euo pipefail

GCP_PROJECT="${GCP_PROJECT:-enki-test}"
GCP_REGION="${GCP_REGION:-us-central1}"
GITHUB_REPO="${GITHUB_REPO:-nelsonbridge/project-enki}"
WIF_POOL_ID="${WIF_POOL_ID:-github-actions-pool}"
PUBLISHER_PROVIDER_ID="${PUBLISHER_PROVIDER_ID:-github-actions-publisher-oidc}"
PUBLISHER_SA_NAME="${PUBLISHER_SA_NAME:-artifact-registry-publisher}"
AR_REPOSITORY="${AR_REPOSITORY:-enki-containers}"
PUBLISH_BRANCH="refs/heads/sandbox"
PUBLISH_WORKFLOW="${GITHUB_REPO}/.github/workflows/publish.yml@${PUBLISH_BRANCH}"
PUBLISHER_SA_EMAIL="${PUBLISHER_SA_NAME}@${GCP_PROJECT}.iam.gserviceaccount.com"
GITHUB_OIDC_ISSUER="https://token.actions.githubusercontent.com"

log() { echo "[publisher-bootstrap] $*"; }
fail() { echo "[publisher-bootstrap] ERROR: $*" >&2; exit 1; }

for bin in gcloud; do
  command -v "${bin}" >/dev/null 2>&1 || fail "${bin} is required"
done

log "Targeting GCP project ${GCP_PROJECT}"
gcloud config set project "${GCP_PROJECT}" >/dev/null

log "Checking Workload Identity Pool ${WIF_POOL_ID}"
gcloud iam workload-identity-pools describe "${WIF_POOL_ID}" \
  --location=global \
  --project="${GCP_PROJECT}" >/dev/null \
  || fail "Workload Identity Pool ${WIF_POOL_ID} does not exist; run the base GCP bootstrap first"

WIF_POOL_NAME=$(gcloud iam workload-identity-pools describe "${WIF_POOL_ID}" \
  --location=global \
  --project="${GCP_PROJECT}" \
  --format="value(name)")

ATTRIBUTE_MAPPING="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.ref=assertion.ref,attribute.event_name=assertion.event_name,attribute.workflow_ref=assertion.workflow_ref"
ATTRIBUTE_CONDITION="assertion.repository == '${GITHUB_REPO}' && assertion.event_name == 'push' && assertion.ref == '${PUBLISH_BRANCH}' && assertion.workflow_ref == '${PUBLISH_WORKFLOW}'"

log "Configuring publisher OIDC provider ${PUBLISHER_PROVIDER_ID}"
if gcloud iam workload-identity-pools providers describe "${PUBLISHER_PROVIDER_ID}" \
  --workload-identity-pool="${WIF_POOL_ID}" \
  --location=global \
  --project="${GCP_PROJECT}" >/dev/null 2>&1; then
  gcloud iam workload-identity-pools providers update-oidc "${PUBLISHER_PROVIDER_ID}" \
    --workload-identity-pool="${WIF_POOL_ID}" \
    --location=global \
    --project="${GCP_PROJECT}" \
    --issuer-uri="${GITHUB_OIDC_ISSUER}" \
    --attribute-mapping="${ATTRIBUTE_MAPPING}" \
    --attribute-condition="${ATTRIBUTE_CONDITION}" >/dev/null
else
  gcloud iam workload-identity-pools providers create-oidc "${PUBLISHER_PROVIDER_ID}" \
    --workload-identity-pool="${WIF_POOL_ID}" \
    --location=global \
    --project="${GCP_PROJECT}" \
    --issuer-uri="${GITHUB_OIDC_ISSUER}" \
    --attribute-mapping="${ATTRIBUTE_MAPPING}" \
    --attribute-condition="${ATTRIBUTE_CONDITION}" \
    --display-name="GitHub Actions OIDC (Artifact Registry publisher)" >/dev/null
fi

log "Ensuring publisher service account ${PUBLISHER_SA_EMAIL}"
if ! gcloud iam service-accounts describe "${PUBLISHER_SA_EMAIL}" \
  --project="${GCP_PROJECT}" >/dev/null 2>&1; then
  gcloud iam service-accounts create "${PUBLISHER_SA_NAME}" \
    --project="${GCP_PROJECT}" \
    --display-name="Artifact Registry Publisher" \
    --description="Publisher-only identity for project-enki publish.yml" >/dev/null
fi

log "Binding GitHub repository identity to publisher service account"
gcloud iam service-accounts add-iam-policy-binding "${PUBLISHER_SA_EMAIL}" \
  --project="${GCP_PROJECT}" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/${WIF_POOL_NAME}/attribute.repository/${GITHUB_REPO}" \
  --condition=None >/dev/null

log "Checking Artifact Registry repository ${AR_REPOSITORY}"
gcloud artifacts repositories describe "${AR_REPOSITORY}" \
  --location="${GCP_REGION}" \
  --project="${GCP_PROJECT}" >/dev/null \
  || fail "Artifact Registry repository ${AR_REPOSITORY} does not exist in ${GCP_REGION}"

log "Granting publisher writer access only to ${AR_REPOSITORY}"
gcloud artifacts repositories add-iam-policy-binding "${AR_REPOSITORY}" \
  --location="${GCP_REGION}" \
  --project="${GCP_PROJECT}" \
  --member="serviceAccount:${PUBLISHER_SA_EMAIL}" \
  --role="roles/artifactregistry.writer" \
  --condition=None >/dev/null

PUBLISHER_PROVIDER_NAME=$(gcloud iam workload-identity-pools providers describe "${PUBLISHER_PROVIDER_ID}" \
  --workload-identity-pool="${WIF_POOL_ID}" \
  --location=global \
  --project="${GCP_PROJECT}" \
  --format="value(name)")

if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  log "Writing GitHub Actions repository variables"
  gh variable set GCP_PROJECT --repo "${GITHUB_REPO}" --body "${GCP_PROJECT}"
  gh variable set GCP_REGION --repo "${GITHUB_REPO}" --body "${GCP_REGION}"
  gh variable set GCP_AR_WIF_PROVIDER --repo "${GITHUB_REPO}" --body "${PUBLISHER_PROVIDER_NAME}"
  gh variable set GCP_AR_SA --repo "${GITHUB_REPO}" --body "${PUBLISHER_SA_EMAIL}"
  log "GitHub Actions variables updated"
else
  log "gh is not installed/authenticated; set these repository variables manually:"
  echo "  GCP_PROJECT=${GCP_PROJECT}"
  echo "  GCP_REGION=${GCP_REGION}"
  echo "  GCP_AR_WIF_PROVIDER=${PUBLISHER_PROVIDER_NAME}"
  echo "  GCP_AR_SA=${PUBLISHER_SA_EMAIL}"
fi

cat <<EOF

Publisher bootstrap complete.
  Provider: ${PUBLISHER_PROVIDER_NAME}
  Service account: ${PUBLISHER_SA_EMAIL}
  Artifact Registry: ${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT}/${AR_REPOSITORY}
  Trust boundary: push + sandbox + publish.yml + ${GITHUB_REPO}
EOF

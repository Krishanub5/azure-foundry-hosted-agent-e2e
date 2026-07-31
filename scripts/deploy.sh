#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

set_environment "${1:-development}"
IMAGE_TAG="${2:-$(git -C "${REPO_ROOT}" rev-parse --short HEAD 2>/dev/null || date +%Y%m%d%H%M%S)}"

require_cmd terraform
require_cmd az
ensure_azure_subscription

FOUNDATION_PLAN="${DEPLOYMENT_DIR}/${DEPLOY_ENV}-foundation.tfplan"
terraform -chdir="${TF_DIR}" init
terraform -chdir="${TF_DIR}" fmt -check -recursive
terraform -chdir="${TF_DIR}" validate
terraform -chdir="${TF_DIR}" plan \
  -var-file="${TFVARS_FILE}" \
  -out="${FOUNDATION_PLAN}"
terraform -chdir="${TF_DIR}" apply "${FOUNDATION_PLAN}"

"${SCRIPT_DIR}/build-and-push.sh" "${DEPLOY_ENV}" "${IMAGE_TAG}"
"${SCRIPT_DIR}/deploy-agent.sh" "${DEPLOY_ENV}" "${IMAGE_TAG}"
"${SCRIPT_DIR}/post-deploy-rbac.sh" "${DEPLOY_ENV}"
"${SCRIPT_DIR}/deploy-ui.sh" "${DEPLOY_ENV}" "${IMAGE_TAG}"
"${SCRIPT_DIR}/ingest.sh" "${DEPLOY_ENV}" "${REPO_ROOT}/sample-data"
"${SCRIPT_DIR}/smoke-test.sh" "${DEPLOY_ENV}"

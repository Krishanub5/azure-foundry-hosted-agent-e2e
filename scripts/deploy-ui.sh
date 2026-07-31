#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

set_environment "${1:-development}"
IMAGE_TAG="${2:-$(cat "${DEPLOYMENT_DIR}/${DEPLOY_ENV}-image-tag" 2>/dev/null || echo local)}"

require_cmd terraform
ACR_LOGIN_SERVER="$(tf_raw acr_login_server)"
UI_IMAGE="${ACR_LOGIN_SERVER}/enterprise-knowledge-web:${IMAGE_TAG}"
PLAN_FILE="${DEPLOYMENT_DIR}/${DEPLOY_ENV}-ui.tfplan"

terraform -chdir="${TF_DIR}" plan \
  -var-file="${TFVARS_FILE}" \
  -var="ui_image=${UI_IMAGE}" \
  -out="${PLAN_FILE}"
terraform -chdir="${TF_DIR}" apply "${PLAN_FILE}"

tf_raw web_url

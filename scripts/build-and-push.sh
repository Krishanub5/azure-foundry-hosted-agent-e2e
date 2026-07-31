#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

set_environment "${1:-development}"
IMAGE_TAG="${2:-$(git -C "${REPO_ROOT}" rev-parse --short HEAD 2>/dev/null || echo local)}"

require_cmd az
require_cmd docker
require_cmd terraform
ensure_azure_subscription

ACR_NAME="$(tf_raw acr_name)"
ACR_LOGIN_SERVER="$(tf_raw acr_login_server)"

az acr login --name "${ACR_NAME}"

images=(agent web ingestion)
for image in "${images[@]}"; do
  image_uri="${ACR_LOGIN_SERVER}/enterprise-knowledge-${image}:${IMAGE_TAG}"
  echo "Building ${image_uri}"
  docker build \
    --platform linux/amd64 \
    --pull \
    --tag "${image_uri}" \
    "${REPO_ROOT}/apps/${image}"
  docker push "${image_uri}"
done

printf '%s\n' "${IMAGE_TAG}" > "${DEPLOYMENT_DIR}/${DEPLOY_ENV}-image-tag"
echo "Images pushed with tag ${IMAGE_TAG}"

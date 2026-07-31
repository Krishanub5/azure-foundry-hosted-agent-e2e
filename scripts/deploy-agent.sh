#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

set_environment "${1:-development}"
IMAGE_TAG="${2:-$(cat "${DEPLOYMENT_DIR}/${DEPLOY_ENV}-image-tag" 2>/dev/null || echo local)}"

require_cmd az
require_cmd terraform
require_cmd python3
ensure_azure_subscription

PROJECT_ENDPOINT="$(tf_raw foundry_project_endpoint)"
AGENT_NAME="$(tf_raw agent_name)"
ACR_LOGIN_SERVER="$(tf_raw acr_login_server)"
AGENT_IMAGE="${ACR_LOGIN_SERVER}/enterprise-knowledge-agent:${IMAGE_TAG}"
OUTPUT_FILE="${DEPLOYMENT_DIR}/${DEPLOY_ENV}-agent.json"

python3 "${SCRIPT_DIR}/deploy_agent.py" \
  --project-endpoint "${PROJECT_ENDPOINT}" \
  --agent-name "${AGENT_NAME}" \
  --image "${AGENT_IMAGE}" \
  --env "AZURE_AI_MODEL_DEPLOYMENT_NAME=$(tf_raw model_deployment_name)" \
  --env "EMBEDDING_DEPLOYMENT_NAME=$(tf_raw embedding_deployment_name)" \
  --env "SEARCH_ENDPOINT=$(tf_raw search_endpoint)" \
  --env "SEARCH_INDEX_NAME=$(tf_raw search_index_name)" \
  --env "APPLICATIONINSIGHTS_CONNECTION_STRING=$(tf_raw application_insights_connection_string)" \
  --output "${OUTPUT_FILE}"

echo "Hosted Agent deployment metadata: ${OUTPUT_FILE}"

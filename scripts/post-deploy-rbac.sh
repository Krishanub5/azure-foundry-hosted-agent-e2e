#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

set_environment "${1:-development}"
require_cmd az
require_cmd jq
require_cmd terraform
ensure_azure_subscription

PROJECT_ENDPOINT="$(tf_raw foundry_project_endpoint)"
AGENT_NAME="$(tf_raw agent_name)"
SEARCH_SCOPE="$(tf_raw search_service_id)"
AGENT_FILE="${DEPLOYMENT_DIR}/${DEPLOY_ENV}-agent.json"

if [[ -f "${AGENT_FILE}" ]]; then
  AGENT_IDENTITY="$(jq -r '.instance_identity_principal_id // empty' "${AGENT_FILE}")"
else
  AGENT_IDENTITY=""
fi

if [[ -z "${AGENT_IDENTITY}" ]]; then
  AGENT_IDENTITY="$(
    az rest \
      --method GET \
      --url "${PROJECT_ENDPOINT}/agents/${AGENT_NAME}?api-version=v1" \
      --resource "https://ai.azure.com" \
      --query "instance_identity.principal_id" \
      --output tsv
  )"
fi

if [[ -z "${AGENT_IDENTITY}" ]]; then
  echo "Could not resolve the Hosted Agent identity." >&2
  exit 1
fi

existing_count="$(
  az role assignment list \
    --assignee-object-id "${AGENT_IDENTITY}" \
    --scope "${SEARCH_SCOPE}" \
    --role "Search Index Data Reader" \
    --query "length(@)" \
    --output tsv
)"

if [[ "${existing_count}" == "0" ]]; then
  az role assignment create \
    --assignee-object-id "${AGENT_IDENTITY}" \
    --assignee-principal-type ServicePrincipal \
    --role "Search Index Data Reader" \
    --scope "${SEARCH_SCOPE}" \
    --output none
fi

echo "Hosted Agent identity ${AGENT_IDENTITY} can read the Azure AI Search index."

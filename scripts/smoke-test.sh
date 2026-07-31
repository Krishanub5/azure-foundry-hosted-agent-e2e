#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

set_environment "${1:-development}"
require_cmd az
require_cmd curl
require_cmd jq
require_cmd terraform
ensure_azure_subscription

AGENT_ENDPOINT="$(tf_raw hosted_agent_endpoint)"
TOKEN="$(az account get-access-token --resource "https://ai.azure.com" --query accessToken --output tsv)"

agent_response="$(
  curl --fail-with-body --silent --show-error \
    --request POST \
    --url "${AGENT_ENDPOINT}" \
    --header "Authorization: Bearer ${TOKEN}" \
    --header "Content-Type: application/json" \
    --data '{"input":"What does the sample knowledge document say the assistant must not invent?","stream":false,"store":true}'
)"

response_id="$(jq -r '.id // empty' <<< "${agent_response}")"
if [[ -z "${response_id}" ]]; then
  echo "Hosted Agent smoke test returned no response ID." >&2
  exit 1
fi
echo "Hosted Agent smoke test passed: ${response_id}"

WEB_URL="$(terraform -chdir="${TF_DIR}" output -raw web_url 2>/dev/null || true)"
if [[ -n "${WEB_URL}" && "${WEB_URL}" != "null" ]]; then
  curl --fail-with-body --silent --show-error "${WEB_URL}/healthz" | jq .
  echo "Web UI health check passed: ${WEB_URL}"
fi

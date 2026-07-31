#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

set_environment "${1:-development}"
require_cmd terraform
require_cmd jq

OUTPUT_FILE="${DEPLOYMENT_DIR}/${DEPLOY_ENV}.env"
tf_json deployment_environment |
  jq -r 'to_entries[] | "\(.key)=\(.value | @sh)"' > "${OUTPUT_FILE}"

chmod 600 "${OUTPUT_FILE}"
echo "${OUTPUT_FILE}"

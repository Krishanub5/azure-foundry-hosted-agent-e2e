#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

set_environment "${1:-development}"
SOURCE_PATH="${2:-${REPO_ROOT}/sample-data}"
require_cmd python3
require_cmd terraform

ENV_FILE="$("${SCRIPT_DIR}/export-env.sh" "${DEPLOY_ENV}")"
set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a

python3 "${REPO_ROOT}/apps/ingestion/ingest.py" --path "${SOURCE_PATH}"

#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TF_DIR="${REPO_ROOT}/infra/terraform"
DEPLOYMENT_DIR="${REPO_ROOT}/.deployment"

require_cmd() {
  local command_name="$1"
  if ! command -v "${command_name}" >/dev/null 2>&1; then
    echo "Required command not found: ${command_name}" >&2
    exit 1
  fi
}

set_environment() {
  DEPLOY_ENV="${1:-development}"
  TFVARS_FILE="${TFVARS_FILE_OVERRIDE:-${TF_DIR}/environments/${DEPLOY_ENV}.tfvars}"
  if [[ ! -f "${TFVARS_FILE}" ]]; then
    echo "Terraform values file not found: ${TFVARS_FILE}" >&2
    echo "Copy and edit the matching .tfvars.example first." >&2
    exit 1
  fi
  mkdir -p "${DEPLOYMENT_DIR}"
}

tf_raw() {
  terraform -chdir="${TF_DIR}" output -raw "$1"
}

tf_json() {
  terraform -chdir="${TF_DIR}" output -json "$1"
}

ensure_azure_subscription() {
  local expected_subscription
  expected_subscription="$(terraform -chdir="${TF_DIR}" console -var-file="${TFVARS_FILE}" <<< 'var.subscription_id' | tr -d '"')"
  local active_subscription
  active_subscription="$(az account show --query id --output tsv)"
  if [[ "${active_subscription}" != "${expected_subscription}" ]]; then
    echo "Azure CLI subscription ${active_subscription} does not match ${expected_subscription}." >&2
    echo "Run: az account set --subscription ${expected_subscription}" >&2
    exit 1
  fi
}

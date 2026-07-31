#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 4 ]]; then
  echo "Usage: $0 <subscription-id> <resource-group> <storage-account> <container>" >&2
  exit 1
fi

SUBSCRIPTION_ID="$1"
STATE_RESOURCE_GROUP="$2"
STATE_STORAGE_ACCOUNT="$3"
STATE_CONTAINER="$4"
STATE_LOCATION="${STATE_LOCATION:-southeastasia}"

command -v az >/dev/null 2>&1 || { echo "Azure CLI is required." >&2; exit 1; }
az account set --subscription "${SUBSCRIPTION_ID}"

az group create \
  --name "${STATE_RESOURCE_GROUP}" \
  --location "${STATE_LOCATION}" \
  --tags managed_by=bootstrap purpose=terraform-state \
  --output none

az storage account create \
  --name "${STATE_STORAGE_ACCOUNT}" \
  --resource-group "${STATE_RESOURCE_GROUP}" \
  --location "${STATE_LOCATION}" \
  --sku Standard_ZRS \
  --kind StorageV2 \
  --min-tls-version TLS1_2 \
  --allow-blob-public-access false \
  --output none

az storage container create \
  --name "${STATE_CONTAINER}" \
  --account-name "${STATE_STORAGE_ACCOUNT}" \
  --auth-mode login \
  --output none

echo "State storage is ready. Use Azure AD authentication for the Terraform backend."

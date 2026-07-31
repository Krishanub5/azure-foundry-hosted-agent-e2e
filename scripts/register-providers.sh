#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

require_cmd az

providers=(
  Microsoft.App
  Microsoft.Authorization
  Microsoft.CognitiveServices
  Microsoft.ContainerInstance
  Microsoft.ContainerRegistry
  Microsoft.DocumentDB
  Microsoft.Insights
  Microsoft.KeyVault
  Microsoft.MachineLearningServices
  Microsoft.Network
  Microsoft.OperationalInsights
  Microsoft.Search
  Microsoft.Storage
)

for provider in "${providers[@]}"; do
  echo "Registering ${provider}"
  az provider register --namespace "${provider}" --wait
done

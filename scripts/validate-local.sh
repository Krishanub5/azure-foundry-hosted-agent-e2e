#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
STRICT=false

if [[ "${1:-}" == "--all" ]]; then
  STRICT=true
elif [[ $# -ne 0 ]]; then
  echo "Usage: $0 [--all]" >&2
  exit 2
fi

cd "${REPO_ROOT}"

require_cmd() {
  local command_name="$1"
  if ! command -v "${command_name}" >/dev/null 2>&1; then
    echo "Required command not found: ${command_name}" >&2
    exit 1
  fi
}

optional_cmd() {
  local command_name="$1"
  if command -v "${command_name}" >/dev/null 2>&1; then
    return 0
  fi
  if [[ "${STRICT}" == "true" ]]; then
    echo "Full validation requires: ${command_name}" >&2
    exit 1
  fi
  echo "Skipping ${command_name}-based checks because it is not installed."
  return 1
}

require_cmd python3

echo "== Python compile, lint, formatting, and unit tests =="
python3 -m compileall -q apps scripts
python3 -m ruff check apps scripts tests
python3 -m ruff format --check apps scripts tests
python3 -m unittest discover -s tests -p 'test_*.py' -v

echo "== Shell syntax =="
for script in scripts/*.sh; do
  bash -n "${script}"
done

if optional_cmd shellcheck; then
  echo "== ShellCheck =="
  shellcheck scripts/*.sh
fi

if optional_cmd node; then
  echo "== Browser JavaScript syntax =="
  node --check apps/web/static/app.js
fi

if optional_cmd actionlint; then
  echo "== GitHub Actions syntax and expressions =="
  actionlint -no-color .github/workflows/*.yml
fi

if optional_cmd terraform; then
  echo "== Terraform format and provider validation =="
  terraform -chdir=infra/terraform fmt -check -recursive
  terraform -chdir=infra/terraform init -backend=false -input=false
  terraform -chdir=infra/terraform validate
fi

if optional_cmd docker; then
  echo "== Container builds =="
  docker build --tag enterprise-knowledge-agent:validation apps/agent
  docker build --tag enterprise-knowledge-web:validation apps/web
  docker build --tag enterprise-knowledge-ingestion:validation apps/ingestion
fi

echo "Validation completed successfully."

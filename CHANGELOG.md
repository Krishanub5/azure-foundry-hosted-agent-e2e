# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and releases follow semantic versioning where practical.

## [Unreleased]

### Added

- Public repository governance, contribution, security, and support guidance.
- Cross-version Python tests, Terraform validation, ShellCheck, and container-build
  jobs in GitHub Actions.
- Repository contract, settings, client, retrieval, ingestion, and deployment tests.
- Local fast and full validation commands.

### Fixed

- Existing Ruff violations that caused the original CI workflow to fail.
- The Makefile ingestion argument, which previously conflicted with the operating
  system `PATH` variable.
- Validation for malformed numeric configuration and whitespace-only chat messages.

## [1.0.0] - 2026-07-28

### Added

- Microsoft Foundry Hosted Agent with Responses protocol 2.0.
- Azure AI Search hybrid-vector RAG and document ingestion.
- FastAPI chat UI with Cosmos DB conversation storage.
- Terraform development and private-network deployment modes.
- Managed identities, RBAC, monitoring, deployment scripts, and GitHub OIDC workflow.

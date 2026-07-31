# Contributing

Thank you for improving this reference implementation.

## Before opening a change

1. Search existing issues and pull requests.
2. For a substantial architecture change, open a design issue first.
3. Never include customer data, credentials, internal hostnames, subscription IDs,
   tenant IDs, or screenshots containing sensitive information.

## Development setup

Use Python 3.12 or 3.13:

```bash
python3 -m venv .venv
source .venv/bin/activate
make setup-dev
make validate-local
```

Run the full toolchain when Terraform, Docker, Node.js, and ShellCheck are installed:

```bash
make validate-all
```

## Pull-request expectations

- Keep changes focused and explain the operational impact.
- Add or update tests for changed behavior.
- Update documentation and Terraform examples when interfaces change.
- Preserve managed-identity authentication and do not introduce stored secrets.
- Run `make lint`, `make test`, and `make validate-local`.
- Confirm that container images still run as a non-root user.

All pull requests run Python tests on supported versions, Ruff, ShellCheck,
Terraform validation, and three container builds.

## Commit guidance

Use concise imperative commit subjects, for example:

```text
Add retry policy to Hosted Agent client
```

By contributing, you agree that your contribution is licensed under the MIT
License in this repository.

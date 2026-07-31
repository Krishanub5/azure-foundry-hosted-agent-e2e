# Validation results

Validation date: **2026-07-28**

## Passed locally

| Check | Result |
| --- | --- |
| Python 3.12.13 dependency resolution and imports | Passed |
| Python 3.13.14 dependency resolution and imports | Passed |
| Python dependency vulnerability audit | No known vulnerabilities found |
| Unit and repository-contract tests | 53 passed |
| Branch-aware Python coverage | 71% |
| Ruff lint and format | Passed |
| Shell syntax | Passed |
| ShellCheck 0.11 | Passed |
| GitHub Actions syntax and expressions | Passed |
| Browser JavaScript syntax | Passed |
| YAML and HTML parsing | Passed |
| Terraform/HCL parse and canonical-format check | Passed |
| Local Markdown links | Passed |
| Secret-pattern scan | Passed |

## Enforced by GitHub Actions

Every pull request and push to `main` runs:

- Python 3.12 and 3.13 compilation, tests, coverage, imports, lint, and formatting;
- ShellCheck and Bash syntax validation;
- Terraform format, provider initialization, and `terraform validate`;
- independent Linux/AMD64 builds for the agent, web, and ingestion containers.

## Environment-dependent checks

The following checks require the repository owner’s infrastructure and therefore
cannot be certified by an offline test run:

- Azure subscription quota and selected model availability;
- provider-aware Terraform validation when Terraform cannot download providers;
- Docker image builds when a Docker daemon is unavailable;
- Azure RBAC propagation, private DNS, firewall, and route behavior;
- live Hosted Agent deployment and invocation;
- live RAG quality, latency, safety evaluation, and cost.

After an Azure deployment, run:

```bash
make smoke ENV=development
```

This invokes the Hosted Agent with the sample knowledge question and validates the
web application health endpoint when one is deployed.

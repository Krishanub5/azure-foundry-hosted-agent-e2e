# Testing and validation

## Validation levels

The project deliberately separates deterministic repository tests from checks that
need Azure credentials and deployed resources.

| Level | Command | What it proves |
| --- | --- | --- |
| Unit and contract | `make test` | Python logic, request contracts, parsing, settings, repository structure |
| Static quality | `make lint` | Ruff lint and formatting |
| Dependency audit | `make audit` | Known Python vulnerabilities reported by PyPI advisory data |
| Local available tools | `make validate-local` | Unit/static tests plus installed ShellCheck, Node.js, Terraform, and Docker checks |
| Full local toolchain | `make validate-all` | Requires every supported validation tool and fails if one is missing |
| Cloud smoke | `make smoke ENV=development` | Invokes the deployed agent and checks the web health endpoint |
| Pull-request CI | GitHub Actions | Python 3.12/3.13, ShellCheck, Terraform, and all container builds |

## Developer setup

```bash
python3 -m venv .venv
source .venv/bin/activate
make setup-dev
make validate-local
```

For a coverage report:

```bash
make coverage
```

## Full validation prerequisites

- Python 3.12 or 3.13
- Node.js
- actionlint
- ShellCheck
- Terraform 1.8 or later
- Docker with Linux container support

Run:

```bash
make validate-all
```

Terraform initialization downloads providers and creates `.terraform.lock.hcl`.
Commit the lock file when publishing a stable release so future runs use the same
provider selections.

## What cannot be proven offline

Static validation cannot prove:

- subscription quota and model availability in a selected region;
- tenant RBAC propagation and policy behavior;
- private DNS and firewall reachability;
- Hosted Agent control-plane preview behavior;
- live model quality, grounding, latency, or cost.

Those require an Azure deployment. After deployment, ingest the sample document and
run:

```bash
make smoke ENV=development
```

For enterprise mode, run the deployment workflow from a self-hosted runner with
private DNS and network access.

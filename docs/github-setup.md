# Publish and configure the GitHub repository

## Create the repository

From the extracted project directory:

```bash
git init
git add .
git commit -m "Publish Microsoft Foundry Hosted Agent reference solution"
git branch -M main
git remote add origin https://github.com/<owner>/<repository>.git
git push -u origin main
```

Review the staged files before committing:

```bash
git status
git diff --cached
```

## Recommended repository settings

1. Enable GitHub Discussions.
2. Enable private vulnerability reporting.
3. Enable Dependabot alerts and security updates.
4. Enable secret scanning and push protection where available.
5. Protect `main` and require the `Python`, `Shell`, `Terraform`, and `Containers`
   workflow jobs.
6. Require at least one approval and resolution of review conversations.
7. Prevent force pushes and branch deletion.

## Deployment environments

Create protected GitHub Environments named `development` and `enterprise`.

Configure these environment variables:

| Variable | Purpose |
| --- | --- |
| `AZURE_CLIENT_ID` | Federated deployment application client ID |
| `AZURE_CLIENT_OBJECT_ID` | Deployment service principal object ID |
| `AZURE_TENANT_ID` | Microsoft Entra tenant ID |
| `AZURE_SUBSCRIPTION_ID` | Target subscription |
| `AZURE_LOCATION` | Deployment region |
| `PROJECT_NAME` | Short resource-name prefix |
| `TF_STATE_RESOURCE_GROUP` | Terraform state resource group |
| `TF_STATE_STORAGE_ACCOUNT` | Terraform state storage account |
| `TF_STATE_CONTAINER` | Terraform state container |
| `DEPLOY_RUNNER` | Optional self-hosted runner label for private deployments |
| `FIREWALL_PRIVATE_IP` | Optional existing hub firewall private IP |

The workflow uses GitHub OIDC. Do not create a client secret.

## Before the first deployment

1. Bootstrap the remote state account with `scripts/bootstrap-state.sh`.
2. Create the GitHub OIDC federated credential in Microsoft Entra ID.
3. Grant the deployment principal the roles documented in `README.md`.
4. Confirm model availability and quota in the selected region.
5. Run the CI workflow successfully.
6. Run the deployment workflow first against `development`.

Never commit `.tfvars`, `.env`, Terraform state, deployment output, or Azure tokens.

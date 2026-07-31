# Deployment guide

## 1. Confirm platform and governance prerequisites

Before creating cost-bearing resources:

1. Select the exact Azure subscription and region.
2. Confirm `gpt-5.4-mini` and `text-embedding-3-large` quota. If unavailable, change
   the model name, version, SKU, and capacity in the environment `.tfvars`.
3. Confirm that the intended data classification permits the chosen deployment type
   and region.
4. Confirm the deployment identity has Contributor, role-assignment permission,
   Foundry Account Owner, and Foundry Project Manager as applicable.
5. For private mode, validate that the VNet address space is RFC1918, nonoverlapping,
   and that the runner can resolve the required private DNS zones.

Register providers:

```bash
./scripts/register-providers.sh
```

## 2. Configure Terraform state

For a local lab, Terraform's local backend works without extra configuration.

For team/CI use, create the remote-state account:

```bash
./scripts/bootstrap-state.sh \
  "<subscription-id>" \
  "rg-terraform-state" \
  "<globally-unique-storage-name>" \
  "tfstate"
```

Then copy `infra/terraform/backend.tf.example` to `infra/terraform/backend.tf` and
initialize:

```bash
terraform -chdir=infra/terraform init \
  -backend-config="resource_group_name=rg-terraform-state" \
  -backend-config="storage_account_name=<state-storage>" \
  -backend-config="container_name=tfstate" \
  -backend-config="key=foundry-agent-development.tfstate" \
  -backend-config="use_azuread_auth=true"
```

Use state locking, protected branches/environments, and narrowly scoped state access.
Terraform state contains resource metadata and the Application Insights connection
string, so it must not be public.

## 3. Configure an environment

Development:

```bash
cp infra/terraform/environments/development.tfvars.example \
   infra/terraform/environments/development.tfvars
```

Private enterprise:

```bash
cp infra/terraform/environments/enterprise.tfvars.example \
   infra/terraform/environments/enterprise.tfvars
```

Edit all placeholder identifiers and tags. In private mode:

- The Foundry subnet is dedicated and delegated to `Microsoft.App/environments`.
- The ACI subnet is dedicated and delegated to
  `Microsoft.ContainerInstance/containerGroups`.
- The private-endpoint subnet has private endpoint policies disabled.
- If an existing firewall IP is set, ensure the firewall allows Foundry deployment,
  Entra ID, Azure Container Registry, Azure Monitor, and any approved external tool
  endpoints. Do not perform TLS interception on Entra/Foundry control traffic.
- For private ACR support, use a project created after June 25, 2026. This template
  creates a new project, so a fresh deployment meets that platform requirement.

## 4. Provision the foundation

```bash
make init ENV=development
make fmt
make validate
make plan ENV=development
make apply ENV=development
```

The plan creates:

- resource group, VNet, subnets, and baseline NSGs;
- optional private endpoints and DNS;
- Storage, Cosmos, Search, and ACR;
- Log Analytics and Application Insights;
- Foundry account, project, model deployments, connections, and capability host;
- project/web identities and their static RBAC assignments.

No ACI resource is created until `ui_image` is non-empty.

The account capability host is created explicitly in public development mode.
Private mode relies on the platform-created account host produced by
`networkInjections.scenario = "agent"`; declaring a second host would return a
conflict. The project capability host is always managed by Terraform.

## 5. Build immutable images

```bash
python -m pip install -r scripts/requirements.txt
make images ENV=development TAG=1.0.0
```

Use a Git commit SHA or release version as the tag. Do not deploy `latest`.

## 6. Deploy the Hosted Agent

```bash
make deploy-agent ENV=development TAG=1.0.0
make agent-rbac ENV=development
```

This sequence:

1. creates a new Hosted Agent version using the current Foundry v1 REST API;
2. waits for `active`;
3. routes 100% of the endpoint to the new version;
4. retrieves `instance_identity.principal_id`;
5. grants Search Index Data Reader at the Search service scope.

The previous agent version remains available for rollback until explicitly deleted.

## 7. Deploy the ACI UI

```bash
make deploy-ui ENV=development TAG=1.0.0
```

Development mode returns a public HTTP endpoint. Do not expose that endpoint with
sensitive data. Private mode returns an RFC1918 IP; publish it only through the
organization's approved TLS/authenticated ingress.

## 8. Ingest knowledge

Install ingestion dependencies:

```bash
python -m pip install -r apps/ingestion/requirements.txt
```

Run:

```bash
make ingest ENV=development PATH=sample-data
```

The operator needs:

- Storage Blob Data Contributor on the source Storage account;
- Search Service Contributor and Search Index Data Contributor on Search;
- model inference permission on the Foundry project.

When `deployer_principal_id` is set, Terraform assigns these data roles together
with AcrPush and Foundry Project Manager to that deployment principal.

In private mode, run ingestion from the workload VNet or an approved connected
network. A GitHub-hosted runner cannot reach private endpoints.

## 9. Validate

```bash
make smoke ENV=development
```

Then verify:

- agent version is active;
- Hosted Agent identity has only the intended Search read role;
- the sample query returns a citation to `welcome.md`;
- Cosmos receives a conversation item after using the UI;
- Search, Cosmos, Storage, ACR, and Foundry show public access disabled in private mode;
- `nslookup` from the VNet resolves every service to a private IP.

The Hosted Agent endpoint is service managed and can remain publicly addressable
in the current preview. Confirm that unauthenticated calls fail and that only the
ACI identity has Foundry Agent Consumer.

## GitHub OIDC

The deploy workflow expects protected GitHub Environment variables:

| Variable | Purpose |
| --- | --- |
| `AZURE_CLIENT_ID` | Federated application client ID |
| `AZURE_CLIENT_OBJECT_ID` | Service principal object ID for Terraform RBAC |
| `AZURE_TENANT_ID` | Entra tenant |
| `AZURE_SUBSCRIPTION_ID` | Workload subscription |
| `AZURE_LOCATION` | Region |
| `PROJECT_NAME` | Workload prefix |
| `TF_STATE_RESOURCE_GROUP` | Remote-state resource group |
| `TF_STATE_STORAGE_ACCOUNT` | Remote-state account |
| `TF_STATE_CONTAINER` | Remote-state blob container |
| `DEPLOY_RUNNER` | `ubuntu-latest` or private self-hosted runner label |
| `FIREWALL_PRIVATE_IP` | Optional hub firewall IP |

Configure a federated credential restricted to the intended repository and GitHub
Environment. No Azure client secret is required.

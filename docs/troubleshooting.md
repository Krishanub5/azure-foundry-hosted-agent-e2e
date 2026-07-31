# Troubleshooting

## Model deployment fails

Symptoms include quota errors, an unsupported model version, or an unavailable SKU.

1. Confirm that Hosted Agents and both selected models are available in the target
   region.
2. Check subscription quota for the deployment SKU.
3. Update the model name, version, SKU, and capacity in the `.tfvars` file.
4. Run `terraform plan` again before applying.

The example values are current reference defaults, not a guarantee that every
subscription has access.

## Hosted Agent image cannot be pulled

Check:

- the image was built for `linux/amd64`;
- the project identity has `AcrPull`;
- Azure AD authentication as the ACR ARM policy is enabled;
- private DNS resolves the registry from the Foundry injected subnet;
- the project creation date supports a private registry.

Current Microsoft guidance states that projects created after 25 June 2026 support
a network-secured private ACR. Older projects may need a reachable public registry
endpoint. See the
[Hosted Agents documentation](https://learn.microsoft.com/azure/foundry/agents/concepts/hosted-agents).

## Agent returns authorization errors

Role assignments can take several minutes to propagate.

1. Run `scripts/post-deploy-rbac.sh <environment>`.
2. Confirm the agent identity shown in `.deployment/<environment>-agent.json`.
3. List role assignments at the Search service scope.
4. Confirm that the caller has Foundry Agent Consumer on the project.
5. Retry after RBAC propagation.

Do not solve a data-plane authorization failure by adding Owner at subscription
scope.

## Ingestion receives Search or Storage 403

The calling user or deployment identity needs:

- Storage Blob Data Contributor on the Storage account;
- Search Service Contributor on the Search service;
- Search Index Data Contributor on the Search service;
- model-inference access through the Foundry project.

For private mode, the ingestion runner must also resolve and reach the private
endpoints.

## Private web UI is unreachable

Enterprise mode creates a private ACI address. It is not directly reachable from
the public internet.

Use an approved path such as:

- a peered VNet;
- corporate connectivity through ExpressRoute or VPN;
- an existing internal Application Gateway/WAF;
- a controlled jump host for initial testing.

Confirm that the ACI subnet NSG permits TCP 8080 from the intended source.

## Hosted Agent endpoint still resolves publicly

This can be expected with the current Hosted Agent preview even when the Foundry
account and dependencies use private endpoints. Calls still require a Microsoft
Entra token. Do not treat the managed endpoint as a guaranteed private-only ingress
boundary without validating the current platform behavior.

## Terraform reports a missing backend

For a local functional test, an implicit local backend is acceptable. For shared
environments:

```bash
cp infra/terraform/backend.tf.example infra/terraform/backend.tf
terraform -chdir=infra/terraform init \
  -backend-config="resource_group_name=<state-rg>" \
  -backend-config="storage_account_name=<state-account>" \
  -backend-config="container_name=<state-container>" \
  -backend-config="key=foundry-agent.tfstate" \
  -backend-config="use_azuread_auth=true"
```

Never commit the generated `backend.tf` or Terraform state.

## `make ingest` uses the wrong document directory

Use `SOURCE`, not the operating-system `PATH` variable:

```bash
make ingest ENV=development SOURCE=sample-data
```

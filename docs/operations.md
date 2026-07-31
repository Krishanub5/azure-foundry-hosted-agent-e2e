# Operations runbook

## Health signals

| Component | Signal |
| --- | --- |
| Web tier | `GET /healthz` and `GET /readyz` |
| Hosted Agent | Agent version status `active`, invocation latency/errors |
| Search | Throttling, latency, document count, failed indexing |
| Cosmos | RU consumption, throttled requests, availability |
| Foundry model | token rate, quota errors, latency, content-filter outcomes |
| ACR/ACI | image pull, restart count, container events |

Suggested initial SLOs for an internal pilot:

- 99.5% successful chat requests per month;
- p95 end-to-end response time below 20 seconds for ordinary RAG questions;
- less than 1% ungrounded claims in the reviewed evaluation set;
- 100% citation validity for claims that cite a source.

Adjust these after measuring actual documents, model behavior, and traffic.

## Common failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Agent deployment remains `creating` | image pull, package, quota, or subnet egress issue | Stream Hosted Agent logs and verify ACR pull plus firewall rules |
| Agent returns 403 from Search | instance identity lacks Search Index Data Reader | Re-run `post-deploy-rbac.sh` and check scope |
| Web returns 403 from Foundry | ACI identity lacks Foundry Agent Consumer | Check project-scoped role and token audience |
| Web returns 404/424 from agent | endpoint routing/version not active | Inspect agent details and route to an active version |
| Ingestion cannot resolve service | runner is outside private DNS/VNet | Run from connected/self-hosted runner |
| Cosmos 403 | ACI identity lacks SQL data-plane role | Check Cosmos SQL role assignment and propagation |
| Retrieval has no results | index empty, wrong index name, or embeddings mismatch | Run ingestion and compare model/vector dimensions |
| Stale answers | old source chunks remain | Re-ingest the same blob path or delete obsolete source records |

## Inspect the Hosted Agent

```bash
ACCOUNT_NAME="$(terraform -chdir=infra/terraform output -raw foundry_account_name)"
PROJECT_NAME="$(terraform -chdir=infra/terraform output -raw foundry_project_name)"
AGENT_NAME="$(terraform -chdir=infra/terraform output -raw agent_name)"
BASE_URL="https://${ACCOUNT_NAME}.services.ai.azure.com/api/projects/${PROJECT_NAME}"

az rest \
  --method GET \
  --url "${BASE_URL}/agents/${AGENT_NAME}?api-version=v1" \
  --resource "https://ai.azure.com"
```

## Roll back

Hosted Agent versions are immutable. To roll back:

1. identify the last known-good active version;
2. patch the agent endpoint's FixedRatio selector to that version at 100%;
3. run the smoke and evaluation suites;
4. leave the failed version for investigation, then delete it under change control.

The `PATCH /agents/{name}` payload is documented in the Microsoft Hosted Agent
lifecycle documentation and mirrored in `scripts/deploy_agent.py`.

For the web UI, redeploy the previous immutable ACR tag using:

```bash
terraform -chdir=infra/terraform apply \
  -var-file=environments/development.tfvars \
  -var="ui_image=<acr>/enterprise-knowledge-web:<previous-tag>"
```

## Backup and recovery

- Storage versioning and seven-day soft delete are enabled.
- Cosmos conversations are operational history, not a system of record; configure
  backup mode and retention from your recovery requirements.
- Export Search source metadata/index schema and retain source documents so the
  index can be rebuilt.
- Keep agent source, system prompt, infrastructure, and deployment metadata in
  version control.
- Test reconstruction in a separate environment.

## Scaling

Scale in this order:

1. inspect model quota and throttling;
2. add Search replicas for query load and partitions for index size;
3. raise Cosmos throughput or use autoscale;
4. move the web image from single-instance ACI to a multi-replica platform;
5. tune retrieval `top_k`, chunk size, and embedding batches;
6. load-test the complete path with realistic prompts.

Do not increase every service blindly; Foundry/model latency is often the dominant
factor.

## Change management

Every release should record:

- Git commit and image digests;
- Terraform plan approval;
- model name/version/SKU/capacity;
- system-prompt hash;
- Search schema and ingestion manifest;
- agent version and instance identity;
- evaluation results and rollback version.

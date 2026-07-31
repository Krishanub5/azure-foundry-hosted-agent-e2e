# Cost guidance

Azure prices and model rates vary by region and change over time, so this repository
does not hard-code a monthly estimate. Use the Azure pricing calculator with the
exact subscription offer, region, and expected usage.

## Main cost drivers

| Service | Primary driver | Cost-control lever |
| --- | --- | --- |
| Foundry model | input/output tokens and deployment type | smaller model, prompt/context limits, caching, quota alerts |
| Embeddings | indexed tokens | deduplication, incremental ingestion, chunk tuning |
| Azure AI Search | SKU, replicas, partitions | one replica for nonproduction; scheduled environments |
| Cosmos DB | provisioned/autoscale RU/s and storage | TTL, autoscale sizing, compact conversation documents |
| Storage | capacity, operations, replication | lifecycle policy, LRS for lab, delete obsolete versions |
| ACR | SKU and storage | Basic in public dev; retention cleanup |
| ACI | vCPU/memory running time | smallest tested size, shut down idle lab UI |
| Private networking | Premium ACR, private endpoints, DNS | share central DNS; budget per endpoint |
| Azure Firewall | fixed hourly plus data | reuse landing-zone firewall; do not create per workload |
| Log Analytics | ingestion and retention | sampling, content capture off, retention by policy |

Hosted Agent compute is provisioned around activity and is deprovisioned after an
idle period according to the current platform documentation, but model calls, data
services, registry, private networking, and monitoring still incur charges.

Standard Setup has a material Cosmos DB floor. Foundry requires at least 3,000 RU/s
of account capacity and can provision three to five 1,000-RU/s agent containers per
project; this sample also provisions a separate 400-RU/s UI-history database. The
Terraform account intentionally leaves the total throughput cap unrestricted so
capability-host provisioning is not blocked. Set an approved account limit only
after sizing every project and the Responses API containers it will create.

## Environment recommendations

- **Development:** public endpoints with Entra/RBAC, Basic ACR, one Search replica,
  30-day logs, LRS Storage, small model capacity.
- **Test/UAT:** private mode if network behavior is under test; load only a
  representative document set.
- **Production:** private mode, measured Search/Cosmos capacity, production retention,
  budget alerts, and zone/region design based on SLO.

## Budget controls

Create budgets and alerts at resource-group/subscription scope for 50%, 75%, 90%, and
100% of the approved monthly amount. Add separate dashboards for:

- model token usage and throttling;
- Search replicas/partitions;
- Cosmos RU and throttles;
- Log Analytics daily ingestion;
- orphaned ACR images and private endpoints;
- nonproduction resources running outside approved hours.

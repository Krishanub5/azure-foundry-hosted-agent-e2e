locals {
  normalized_project = lower(replace(var.project_name, "/[^a-zA-Z0-9-]/", ""))
  prefix             = substr("${local.normalized_project}-${var.environment}", 0, 30)
  compact_prefix     = substr(replace("${local.normalized_project}${var.environment}", "-", ""), 0, 15)
  suffix             = random_string.suffix.result

  resource_group_name = var.resource_group_name != "" ? var.resource_group_name : "rg-${local.prefix}-${local.suffix}"
  vnet_name           = "vnet-${local.prefix}-${local.suffix}"
  foundry_name        = substr("${local.compact_prefix}ai${local.suffix}", 0, 60)
  foundry_project     = substr("${local.prefix}-project", 0, 63)
  storage_name        = substr("${local.compact_prefix}st${local.suffix}", 0, 24)
  cosmos_name         = substr("${local.prefix}-cosmos-${local.suffix}", 0, 44)
  search_name         = substr("${local.prefix}-search-${local.suffix}", 0, 60)
  acr_name            = substr("${local.compact_prefix}acr${local.suffix}", 0, 50)
  identity_name       = "id-${local.prefix}-web-${local.suffix}"
  log_name            = "log-${local.prefix}-${local.suffix}"
  app_insights_name   = "appi-${local.prefix}-${local.suffix}"
  container_group     = "aci-${local.prefix}-web-${local.suffix}"
  ui_dns_label        = substr("${local.prefix}-web-${local.suffix}", 0, 63)

  foundry_project_endpoint = "https://${local.foundry_name}.services.ai.azure.com/api/projects/${local.foundry_project}"
  hosted_agent_endpoint = join("", [
    local.foundry_project_endpoint,
    "/agents/",
    var.agent_name,
    "/endpoint/protocols/openai/responses?api-version=v1"
  ])

  has_firewall_ip        = try(length(trimspace(var.existing_firewall_private_ip)) > 0, false)
  has_deployer_principal = try(length(trimspace(var.deployer_principal_id)) > 0, false)

  standard_tags = merge(
    {
      application = var.project_name
      environment = var.environment
      managed_by  = "terraform"
      workload    = "microsoft-foundry-hosted-agent"
    },
    var.tags
  )

  private_dns_zones = toset([
    "privatelink.azurecr.io",
    "privatelink.blob.core.windows.net",
    "privatelink.cognitiveservices.azure.com",
    "privatelink.documents.azure.com",
    "privatelink.openai.azure.com",
    "privatelink.search.windows.net",
    "privatelink.services.ai.azure.com",
  ])

  foundry_base_properties = {
    allowProjectManagement = true
    customSubDomainName    = local.foundry_name
    disableLocalAuth       = true
  }

  foundry_network_properties = var.enable_private_networking ? {
    publicNetworkAccess = "Disabled"
    networkAcls = {
      defaultAction = "Allow"
    }
    networkInjections = [
      {
        scenario                   = "agent"
        subnetArmId                = azurerm_subnet.agent.id
        useMicrosoftManagedNetwork = false
      }
    ]
    } : {
    publicNetworkAccess = "Enabled"
  }

  foundry_agent_consumer_role_id  = "/subscriptions/${var.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/eed3b665-ab3a-47b6-8f48-c9382fb1dad6"
  foundry_user_role_id            = "/subscriptions/${var.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/53ca6127-db72-4b80-b1b0-d745d6d5456d"
  foundry_project_manager_role_id = "/subscriptions/${var.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/eadc314b-1a2d-4efa-be10-5d325db5065e"

  project_internal_id_compact = replace(
    azapi_resource.project.output.properties.internalId,
    "-",
    ""
  )
  project_workspace_id_guid = join("-", [
    substr(local.project_internal_id_compact, 0, 8),
    substr(local.project_internal_id_compact, 8, 4),
    substr(local.project_internal_id_compact, 12, 4),
    substr(local.project_internal_id_compact, 16, 4),
    substr(local.project_internal_id_compact, 20, 12),
  ])
}

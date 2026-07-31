resource "azapi_resource" "foundry" {
  type      = "Microsoft.CognitiveServices/accounts@2025-06-01"
  name      = local.foundry_name
  parent_id = azurerm_resource_group.main.id
  location  = azurerm_resource_group.main.location
  tags      = local.standard_tags

  schema_validation_enabled = false
  body = {
    kind = "AIServices"
    sku = {
      name = "S0"
    }
    identity = {
      type = "SystemAssigned"
    }
    properties = merge(
      local.foundry_base_properties,
      local.foundry_network_properties
    )
  }

  response_export_values = [
    "identity.principalId",
    "properties.endpoint",
  ]

  depends_on = [
    azurerm_subnet_network_security_group_association.agent,
    azurerm_subnet_route_table_association.agent,
  ]
}

resource "azurerm_cognitive_deployment" "chat" {
  name                 = var.model_deployment_name
  cognitive_account_id = azapi_resource.foundry.id

  model {
    format  = "OpenAI"
    name    = var.model_name
    version = var.model_version
  }

  sku {
    name     = var.model_sku_name
    capacity = var.model_capacity
  }
}

resource "azurerm_cognitive_deployment" "embedding" {
  name                 = var.embedding_deployment_name
  cognitive_account_id = azapi_resource.foundry.id

  model {
    format  = "OpenAI"
    name    = var.embedding_model_name
    version = var.embedding_model_version
  }

  sku {
    name     = "GlobalStandard"
    capacity = var.embedding_capacity
  }
}

resource "azapi_resource" "project" {
  type      = "Microsoft.CognitiveServices/accounts/projects@2025-06-01"
  name      = local.foundry_project
  parent_id = azapi_resource.foundry.id
  location  = azurerm_resource_group.main.location

  schema_validation_enabled = false
  body = {
    sku = {
      name = "S0"
    }
    identity = {
      type = "SystemAssigned"
    }
    properties = {
      displayName = var.project_name
      description = "Enterprise knowledge Hosted Agent project managed by Terraform."
    }
  }

  response_export_values = [
    "identity.principalId",
    "properties.internalId",
  ]

  depends_on = [
    azurerm_cognitive_deployment.chat,
    azurerm_cognitive_deployment.embedding,
    azurerm_private_endpoint.storage_blob,
    azurerm_private_endpoint.cosmos,
    azurerm_private_endpoint.search,
    azurerm_private_endpoint.foundry,
    azurerm_private_endpoint.acr,
  ]
}

resource "time_sleep" "project_identity" {
  create_duration = "20s"
  depends_on      = [azapi_resource.project]
}

resource "azapi_resource" "connection_storage" {
  type      = "Microsoft.CognitiveServices/accounts/projects/connections@2025-06-01"
  name      = azurerm_storage_account.main.name
  parent_id = azapi_resource.project.id

  schema_validation_enabled = false
  body = {
    name = azurerm_storage_account.main.name
    properties = {
      category = "AzureStorageAccount"
      target   = azurerm_storage_account.main.primary_blob_endpoint
      authType = "AAD"
      metadata = {
        ApiType    = "Azure"
        ResourceId = azurerm_storage_account.main.id
        location   = var.location
      }
    }
  }
}

resource "azapi_resource" "connection_cosmos" {
  type      = "Microsoft.CognitiveServices/accounts/projects/connections@2025-06-01"
  name      = azurerm_cosmosdb_account.main.name
  parent_id = azapi_resource.project.id

  schema_validation_enabled = false
  body = {
    name = azurerm_cosmosdb_account.main.name
    properties = {
      category = "CosmosDb"
      target   = azurerm_cosmosdb_account.main.endpoint
      authType = "AAD"
      metadata = {
        ApiType    = "Azure"
        ResourceId = azurerm_cosmosdb_account.main.id
        location   = var.location
      }
    }
  }
}

resource "azapi_resource" "connection_search" {
  type      = "Microsoft.CognitiveServices/accounts/projects/connections@2025-06-01"
  name      = azapi_resource.search.name
  parent_id = azapi_resource.project.id

  schema_validation_enabled = false
  body = {
    name = azapi_resource.search.name
    properties = {
      category = "CognitiveSearch"
      target   = "https://${azapi_resource.search.name}.search.windows.net"
      authType = "AAD"
      metadata = {
        ApiType    = "Azure"
        ApiVersion = "2025-05-01-preview"
        ResourceId = azapi_resource.search.id
        location   = var.location
      }
    }
  }
}

resource "azurerm_role_assignment" "project_storage_blob_contributor" {
  scope                            = azurerm_storage_account.main.id
  role_definition_name             = "Storage Blob Data Contributor"
  principal_id                     = azapi_resource.project.output.identity.principalId
  principal_type                   = "ServicePrincipal"
  skip_service_principal_aad_check = true
  depends_on                       = [time_sleep.project_identity]
}

resource "azurerm_role_assignment" "project_cosmos_operator" {
  scope                            = azurerm_cosmosdb_account.main.id
  role_definition_name             = "Cosmos DB Operator"
  principal_id                     = azapi_resource.project.output.identity.principalId
  principal_type                   = "ServicePrincipal"
  skip_service_principal_aad_check = true
  depends_on                       = [time_sleep.project_identity]
}

resource "azurerm_role_assignment" "project_search_index_contributor" {
  scope                            = azapi_resource.search.id
  role_definition_name             = "Search Index Data Contributor"
  principal_id                     = azapi_resource.project.output.identity.principalId
  principal_type                   = "ServicePrincipal"
  skip_service_principal_aad_check = true
  depends_on                       = [time_sleep.project_identity]
}

resource "azurerm_role_assignment" "project_search_service_contributor" {
  scope                            = azapi_resource.search.id
  role_definition_name             = "Search Service Contributor"
  principal_id                     = azapi_resource.project.output.identity.principalId
  principal_type                   = "ServicePrincipal"
  skip_service_principal_aad_check = true
  depends_on                       = [time_sleep.project_identity]
}

resource "azurerm_role_assignment" "project_acr_pull" {
  scope                            = azurerm_container_registry.main.id
  role_definition_name             = "AcrPull"
  principal_id                     = azapi_resource.project.output.identity.principalId
  principal_type                   = "ServicePrincipal"
  skip_service_principal_aad_check = true
  depends_on                       = [time_sleep.project_identity]
}

resource "azurerm_role_assignment" "project_foundry_user" {
  scope                            = azapi_resource.project.id
  role_definition_id               = local.foundry_user_role_id
  principal_id                     = azapi_resource.project.output.identity.principalId
  principal_type                   = "ServicePrincipal"
  skip_service_principal_aad_check = true
  depends_on                       = [time_sleep.project_identity]
}

resource "time_sleep" "project_rbac" {
  create_duration = "60s"
  depends_on = [
    azurerm_role_assignment.project_storage_blob_contributor,
    azurerm_role_assignment.project_cosmos_operator,
    azurerm_role_assignment.project_search_index_contributor,
    azurerm_role_assignment.project_search_service_contributor,
    azurerm_role_assignment.project_acr_pull,
    azurerm_role_assignment.project_foundry_user,
    azurerm_role_assignment.deployer_acr_push,
    azurerm_role_assignment.deployer_foundry_project_manager,
    azurerm_role_assignment.deployer_storage_blob_contributor,
    azurerm_role_assignment.deployer_search_service_contributor,
    azurerm_role_assignment.deployer_search_index_contributor,
  ]
}

resource "azapi_resource" "account_capability_host" {
  count = var.enable_private_networking ? 0 : 1

  type      = "Microsoft.CognitiveServices/accounts/capabilityHosts@2025-06-01"
  name      = "caphost-agents"
  parent_id = azapi_resource.foundry.id

  schema_validation_enabled = false
  body = {
    properties = {
      capabilityHostKind = "Agents"
    }
  }

  depends_on = [azapi_resource.project]
}

resource "azapi_resource" "project_capability_host" {
  type      = "Microsoft.CognitiveServices/accounts/projects/capabilityHosts@2025-06-01"
  name      = "caphost-agents"
  parent_id = azapi_resource.project.id

  schema_validation_enabled = false
  body = {
    properties = {
      capabilityHostKind       = "Agents"
      vectorStoreConnections   = [azapi_resource.search.name]
      storageConnections       = [azurerm_storage_account.main.name]
      threadStorageConnections = [azurerm_cosmosdb_account.main.name]
    }
  }

  depends_on = [
    azapi_resource.connection_storage,
    azapi_resource.connection_cosmos,
    azapi_resource.connection_search,
    azapi_resource.account_capability_host,
    time_sleep.project_rbac,
  ]
}

resource "azurerm_role_assignment" "project_storage_blob_owner" {
  scope                            = azurerm_storage_account.main.id
  role_definition_name             = "Storage Blob Data Owner"
  principal_id                     = azapi_resource.project.output.identity.principalId
  principal_type                   = "ServicePrincipal"
  skip_service_principal_aad_check = true
  condition_version                = "2.0"
  condition                        = <<-EOT
    (
      (
        !(ActionMatches{'Microsoft.Storage/storageAccounts/blobServices/containers/blobs/tags/read'})
        AND !(ActionMatches{'Microsoft.Storage/storageAccounts/blobServices/containers/blobs/filter/action'})
        AND !(ActionMatches{'Microsoft.Storage/storageAccounts/blobServices/containers/blobs/tags/write'})
      )
      OR
      (
        @Resource[Microsoft.Storage/storageAccounts/blobServices/containers:name] StringStartsWithIgnoreCase '${local.project_workspace_id_guid}'
        AND @Resource[Microsoft.Storage/storageAccounts/blobServices/containers:name] StringLikeIgnoreCase '*-azureml-agent'
      )
    )
  EOT

  depends_on = [azapi_resource.project_capability_host]
}

resource "azurerm_cosmosdb_sql_role_assignment" "project_data_contributor" {
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.main.name
  role_definition_id  = "${azurerm_cosmosdb_account.main.id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002"
  principal_id        = azapi_resource.project.output.identity.principalId
  scope               = "${azurerm_cosmosdb_account.main.id}/dbs/enterprise_memory"
  depends_on = [
    azapi_resource.project_capability_host,
    azurerm_role_assignment.project_storage_blob_owner,
  ]
}

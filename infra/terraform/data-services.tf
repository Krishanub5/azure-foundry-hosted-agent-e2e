resource "azurerm_storage_account" "main" {
  name                              = local.storage_name
  resource_group_name               = azurerm_resource_group.main.name
  location                          = azurerm_resource_group.main.location
  account_kind                      = "StorageV2"
  account_tier                      = "Standard"
  account_replication_type          = var.storage_replication_type
  min_tls_version                   = "TLS1_2"
  shared_access_key_enabled         = false
  public_network_access_enabled     = !var.enable_private_networking
  allow_nested_items_to_be_public   = false
  infrastructure_encryption_enabled = var.environment == "prod"
  tags                              = local.standard_tags

  blob_properties {
    versioning_enabled = true
    delete_retention_policy {
      days = 7
    }
    container_delete_retention_policy {
      days = 7
    }
  }

  network_rules {
    default_action = var.enable_private_networking ? "Deny" : "Allow"
    bypass         = ["AzureServices"]
  }
}

resource "azapi_resource" "documents_container" {
  type      = "Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01"
  name      = "documents"
  parent_id = "${azurerm_storage_account.main.id}/blobServices/default"
  body = {
    properties = {
      publicAccess = "None"
    }
  }
}

resource "azurerm_cosmosdb_account" "main" {
  name                             = local.cosmos_name
  location                         = azurerm_resource_group.main.location
  resource_group_name              = azurerm_resource_group.main.name
  offer_type                       = "Standard"
  kind                             = "GlobalDocumentDB"
  local_authentication_disabled    = true
  public_network_access_enabled    = !var.enable_private_networking
  minimal_tls_version              = "Tls12"
  automatic_failover_enabled       = false
  multiple_write_locations_enabled = false
  tags                             = local.standard_tags

  consistency_policy {
    consistency_level = "Session"
  }

  geo_location {
    location          = azurerm_resource_group.main.location
    failover_priority = 0
    zone_redundant    = var.environment == "prod"
  }
}

resource "azurerm_cosmosdb_sql_database" "assistant" {
  name                = "assistant"
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.main.name
  throughput          = 400
}

resource "azurerm_cosmosdb_sql_container" "conversations" {
  name                  = "conversations"
  resource_group_name   = azurerm_resource_group.main.name
  account_name          = azurerm_cosmosdb_account.main.name
  database_name         = azurerm_cosmosdb_sql_database.assistant.name
  partition_key_paths   = ["/id"]
  partition_key_version = 2
  default_ttl           = var.conversation_ttl_seconds

  indexing_policy {
    indexing_mode = "consistent"
    included_path {
      path = "/*"
    }
    excluded_path {
      path = "/messages/*"
    }
  }
}

resource "azapi_resource" "search" {
  type      = "Microsoft.Search/searchServices@2025-05-01"
  name      = local.search_name
  parent_id = azurerm_resource_group.main.id
  location  = azurerm_resource_group.main.location
  tags      = local.standard_tags

  body = {
    sku = {
      name = var.search_sku
    }
    identity = {
      type = "SystemAssigned"
    }
    properties = {
      replicaCount        = var.environment == "prod" ? 2 : 1
      partitionCount      = 1
      hostingMode         = "Default"
      semanticSearch      = "disabled"
      disableLocalAuth    = true
      publicNetworkAccess = var.enable_private_networking ? "Disabled" : "Enabled"
      networkRuleSet = {
        bypass = "None"
      }
      authOptions = {
        aadOrApiKey = {
          aadAuthFailureMode = "http401WithBearerChallenge"
        }
      }
    }
  }
}

resource "azurerm_container_registry" "main" {
  name                                         = local.acr_name
  resource_group_name                          = azurerm_resource_group.main.name
  location                                     = azurerm_resource_group.main.location
  sku                                          = var.enable_private_networking ? "Premium" : "Basic"
  admin_enabled                                = false
  public_network_access_enabled                = !var.enable_private_networking
  zone_redundancy_enabled                      = var.enable_private_networking && var.environment == "prod"
  anonymous_pull_enabled                       = false
  data_endpoint_enabled                        = var.enable_private_networking
  role_assignment_mode                         = "LegacyRegistryPermissions"
  azuread_authentication_as_arm_policy_enabled = true
  tags                                         = local.standard_tags
}

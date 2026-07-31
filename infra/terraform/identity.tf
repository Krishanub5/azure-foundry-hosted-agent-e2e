resource "azurerm_user_assigned_identity" "web" {
  name                = local.identity_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tags                = local.standard_tags
}

resource "azurerm_role_assignment" "web_acr_pull" {
  scope                            = azurerm_container_registry.main.id
  role_definition_name             = "AcrPull"
  principal_id                     = azurerm_user_assigned_identity.web.principal_id
  principal_type                   = "ServicePrincipal"
  skip_service_principal_aad_check = true
}

resource "azurerm_role_assignment" "web_foundry_consumer" {
  scope                            = azapi_resource.project.id
  role_definition_id               = local.foundry_agent_consumer_role_id
  principal_id                     = azurerm_user_assigned_identity.web.principal_id
  principal_type                   = "ServicePrincipal"
  skip_service_principal_aad_check = true
}

resource "azurerm_cosmosdb_sql_role_assignment" "web_data_contributor" {
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.main.name
  role_definition_id  = "${azurerm_cosmosdb_account.main.id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002"
  principal_id        = azurerm_user_assigned_identity.web.principal_id
  scope               = "${azurerm_cosmosdb_account.main.id}/dbs/${azurerm_cosmosdb_sql_database.assistant.name}"
}

resource "azurerm_role_assignment" "deployer_acr_push" {
  count = local.has_deployer_principal ? 1 : 0

  scope                            = azurerm_container_registry.main.id
  role_definition_name             = "AcrPush"
  principal_id                     = var.deployer_principal_id
  principal_type                   = var.deployer_principal_type
  skip_service_principal_aad_check = var.deployer_principal_type == "ServicePrincipal"
}

resource "azurerm_role_assignment" "deployer_foundry_project_manager" {
  count = local.has_deployer_principal ? 1 : 0

  scope                            = azapi_resource.project.id
  role_definition_id               = local.foundry_project_manager_role_id
  principal_id                     = var.deployer_principal_id
  principal_type                   = var.deployer_principal_type
  skip_service_principal_aad_check = var.deployer_principal_type == "ServicePrincipal"
}

resource "azurerm_role_assignment" "deployer_storage_blob_contributor" {
  count = local.has_deployer_principal ? 1 : 0

  scope                            = azurerm_storage_account.main.id
  role_definition_name             = "Storage Blob Data Contributor"
  principal_id                     = var.deployer_principal_id
  principal_type                   = var.deployer_principal_type
  skip_service_principal_aad_check = var.deployer_principal_type == "ServicePrincipal"
}

resource "azurerm_role_assignment" "deployer_search_service_contributor" {
  count = local.has_deployer_principal ? 1 : 0

  scope                            = azapi_resource.search.id
  role_definition_name             = "Search Service Contributor"
  principal_id                     = var.deployer_principal_id
  principal_type                   = var.deployer_principal_type
  skip_service_principal_aad_check = var.deployer_principal_type == "ServicePrincipal"
}

resource "azurerm_role_assignment" "deployer_search_index_contributor" {
  count = local.has_deployer_principal ? 1 : 0

  scope                            = azapi_resource.search.id
  role_definition_name             = "Search Index Data Contributor"
  principal_id                     = var.deployer_principal_id
  principal_type                   = var.deployer_principal_type
  skip_service_principal_aad_check = var.deployer_principal_type == "ServicePrincipal"
}

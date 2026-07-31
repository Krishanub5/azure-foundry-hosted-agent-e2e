output "resource_group_name" {
  value = azurerm_resource_group.main.name
}

output "location" {
  value = azurerm_resource_group.main.location
}

output "foundry_account_name" {
  value = azapi_resource.foundry.name
}

output "foundry_account_id" {
  value = azapi_resource.foundry.id
}

output "foundry_project_name" {
  value = azapi_resource.project.name
}

output "foundry_project_id" {
  value = azapi_resource.project.id
}

output "foundry_project_endpoint" {
  value = local.foundry_project_endpoint
}

output "agent_name" {
  value = var.agent_name
}

output "hosted_agent_endpoint" {
  value = local.hosted_agent_endpoint
}

output "model_deployment_name" {
  value = azurerm_cognitive_deployment.chat.name
}

output "embedding_deployment_name" {
  value = azurerm_cognitive_deployment.embedding.name
}

output "vector_dimensions" {
  value = var.vector_dimensions
}

output "search_endpoint" {
  value = "https://${azapi_resource.search.name}.search.windows.net"
}

output "search_service_id" {
  value = azapi_resource.search.id
}

output "search_index_name" {
  value = var.search_index_name
}

output "storage_account_id" {
  value = azurerm_storage_account.main.id
}

output "storage_blob_endpoint" {
  value = azurerm_storage_account.main.primary_blob_endpoint
}

output "storage_container_name" {
  value = azapi_resource.documents_container.name
}

output "cosmos_account_id" {
  value = azurerm_cosmosdb_account.main.id
}

output "cosmos_endpoint" {
  value = azurerm_cosmosdb_account.main.endpoint
}

output "cosmos_database_name" {
  value = azurerm_cosmosdb_sql_database.assistant.name
}

output "cosmos_container_name" {
  value = azurerm_cosmosdb_sql_container.conversations.name
}

output "acr_name" {
  value = azurerm_container_registry.main.name
}

output "acr_id" {
  value = azurerm_container_registry.main.id
}

output "acr_login_server" {
  value = azurerm_container_registry.main.login_server
}

output "web_managed_identity_client_id" {
  value = azurerm_user_assigned_identity.web.client_id
}

output "application_insights_connection_string" {
  value     = azurerm_application_insights.main.connection_string
  sensitive = true
}

output "web_url" {
  value = var.ui_image == "" ? null : (
    var.enable_private_networking
    ? "http://${azurerm_container_group.web[0].ip_address}:8080"
    : "http://${azurerm_container_group.web[0].fqdn}:8080"
  )
}

output "deployment_environment" {
  value = {
    FOUNDRY_PROJECT_ENDPOINT              = local.foundry_project_endpoint
    AZURE_AI_MODEL_DEPLOYMENT_NAME        = azurerm_cognitive_deployment.chat.name
    EMBEDDING_DEPLOYMENT_NAME             = azurerm_cognitive_deployment.embedding.name
    SEARCH_ENDPOINT                       = "https://${azapi_resource.search.name}.search.windows.net"
    SEARCH_INDEX_NAME                     = var.search_index_name
    STORAGE_BLOB_ENDPOINT                 = azurerm_storage_account.main.primary_blob_endpoint
    STORAGE_CONTAINER_NAME                = azapi_resource.documents_container.name
    VECTOR_DIMENSIONS                     = tostring(var.vector_dimensions)
    AGENT_NAME                            = var.agent_name
    AGENT_ENDPOINT                        = local.hosted_agent_endpoint
    COSMOS_ENDPOINT                       = azurerm_cosmosdb_account.main.endpoint
    COSMOS_DATABASE_NAME                  = azurerm_cosmosdb_sql_database.assistant.name
    COSMOS_CONTAINER_NAME                 = azurerm_cosmosdb_sql_container.conversations.name
    AZURE_CLIENT_ID                       = azurerm_user_assigned_identity.web.client_id
    APPLICATIONINSIGHTS_CONNECTION_STRING = var.enable_telemetry ? azurerm_application_insights.main.connection_string : ""
  }
  sensitive = true
}

resource "azurerm_container_group" "web" {
  count = var.ui_image == "" ? 0 : 1

  name                = local.container_group
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  ip_address_type     = var.enable_private_networking ? "Private" : "Public"
  dns_name_label      = var.enable_private_networking ? null : local.ui_dns_label
  os_type             = "Linux"
  restart_policy      = "Always"
  subnet_ids          = var.enable_private_networking ? [azurerm_subnet.aci.id] : null
  tags                = local.standard_tags

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.web.id]
  }

  image_registry_credential {
    server                    = azurerm_container_registry.main.login_server
    user_assigned_identity_id = azurerm_user_assigned_identity.web.id
  }

  container {
    name   = "web"
    image  = var.ui_image
    cpu    = var.ui_cpu
    memory = var.ui_memory_gb

    ports {
      port     = 8080
      protocol = "TCP"
    }

    environment_variables = {
      AGENT_ENDPOINT                        = local.hosted_agent_endpoint
      APPLICATIONINSIGHTS_CONNECTION_STRING = var.enable_telemetry ? azurerm_application_insights.main.connection_string : ""
      AZURE_CLIENT_ID                       = azurerm_user_assigned_identity.web.client_id
      COSMOS_CONTAINER_NAME                 = azurerm_cosmosdb_sql_container.conversations.name
      COSMOS_DATABASE_NAME                  = azurerm_cosmosdb_sql_database.assistant.name
      COSMOS_ENDPOINT                       = azurerm_cosmosdb_account.main.endpoint
      UI_TITLE                              = var.ui_title
      LOG_LEVEL                             = "INFO"
    }
  }

  depends_on = [
    azurerm_role_assignment.web_acr_pull,
    azurerm_role_assignment.web_foundry_consumer,
    azurerm_cosmosdb_sql_role_assignment.web_data_contributor,
    azurerm_private_endpoint.acr,
    azurerm_private_endpoint.cosmos,
    azurerm_private_endpoint.foundry,
    azurerm_subnet_network_security_group_association.aci,
    azurerm_subnet_route_table_association.aci,
  ]
}

resource "azurerm_log_analytics_workspace" "main" {
  name                = local.log_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = var.log_retention_days
  tags                = local.standard_tags
}

resource "azurerm_application_insights" "main" {
  name                       = local.app_insights_name
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  workspace_id               = azurerm_log_analytics_workspace.main.id
  application_type           = "web"
  retention_in_days          = var.log_retention_days
  internet_ingestion_enabled = true
  internet_query_enabled     = true
  tags                       = local.standard_tags
}

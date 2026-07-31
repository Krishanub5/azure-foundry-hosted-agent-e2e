resource "random_string" "suffix" {
  length  = 5
  lower   = true
  numeric = true
  special = false
  upper   = false
}

resource "azurerm_resource_group" "main" {
  name     = local.resource_group_name
  location = var.location
  tags     = local.standard_tags
}

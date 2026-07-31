provider "azurerm" {
  subscription_id     = var.subscription_id
  storage_use_azuread = true

  features {
    cognitive_account {
      purge_soft_delete_on_destroy = false
    }
    resource_group {
      prevent_deletion_if_contains_resources = true
    }
  }
}

provider "azapi" {
  subscription_id = var.subscription_id
}

data "azurerm_client_config" "current" {}

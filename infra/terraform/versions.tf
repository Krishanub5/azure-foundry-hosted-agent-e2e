terraform {
  required_version = ">= 1.8.0"

  required_providers {
    azapi = {
      source  = "Azure/azapi"
      version = ">= 2.4.0, < 3.0.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 4.81.0, < 5.0.0"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.7.0, < 4.0.0"
    }
    time = {
      source  = "hashicorp/time"
      version = ">= 0.13.0, < 1.0.0"
    }
  }
}

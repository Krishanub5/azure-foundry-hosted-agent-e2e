resource "azurerm_virtual_network" "main" {
  name                = local.vnet_name
  address_space       = var.vnet_address_space
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tags                = local.standard_tags
}

resource "azurerm_subnet" "agent" {
  name                 = "snet-foundry-agents"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = var.agent_subnet_prefixes

  delegation {
    name = "foundry-agent-service"
    service_delegation {
      name    = "Microsoft.App/environments"
      actions = ["Microsoft.Network/virtualNetworks/subnets/join/action"]
    }
  }
}

resource "azurerm_subnet" "private_endpoints" {
  name                              = "snet-private-endpoints"
  resource_group_name               = azurerm_resource_group.main.name
  virtual_network_name              = azurerm_virtual_network.main.name
  address_prefixes                  = var.private_endpoint_subnet_prefixes
  private_endpoint_network_policies = "Disabled"
}

resource "azurerm_subnet" "aci" {
  name                 = "snet-container-instances"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = var.aci_subnet_prefixes

  delegation {
    name = "container-instances"
    service_delegation {
      name    = "Microsoft.ContainerInstance/containerGroups"
      actions = ["Microsoft.Network/virtualNetworks/subnets/action"]
    }
  }
}

resource "azurerm_network_security_group" "agent" {
  name                = "nsg-${local.prefix}-agents-${local.suffix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tags                = local.standard_tags
}

resource "azurerm_network_security_group" "aci" {
  name                = "nsg-${local.prefix}-aci-${local.suffix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tags                = local.standard_tags

  security_rule {
    name                       = "AllowWebFromVirtualNetwork"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "8080"
    source_address_prefix      = "VirtualNetwork"
    destination_address_prefix = "*"
  }
}

resource "azurerm_subnet_network_security_group_association" "agent" {
  subnet_id                 = azurerm_subnet.agent.id
  network_security_group_id = azurerm_network_security_group.agent.id
}

resource "azurerm_subnet_network_security_group_association" "aci" {
  subnet_id                 = azurerm_subnet.aci.id
  network_security_group_id = azurerm_network_security_group.aci.id
}

resource "azurerm_route_table" "firewall" {
  count = local.has_firewall_ip ? 1 : 0

  name                          = "rt-${local.prefix}-egress-${local.suffix}"
  location                      = azurerm_resource_group.main.location
  resource_group_name           = azurerm_resource_group.main.name
  bgp_route_propagation_enabled = true
  tags                          = local.standard_tags

  route {
    name                   = "default-to-hub-firewall"
    address_prefix         = "0.0.0.0/0"
    next_hop_type          = "VirtualAppliance"
    next_hop_in_ip_address = var.existing_firewall_private_ip
  }
}

resource "azurerm_subnet_route_table_association" "agent" {
  count = local.has_firewall_ip ? 1 : 0

  subnet_id      = azurerm_subnet.agent.id
  route_table_id = azurerm_route_table.firewall[0].id
}

resource "azurerm_subnet_route_table_association" "aci" {
  count = local.has_firewall_ip ? 1 : 0

  subnet_id      = azurerm_subnet.aci.id
  route_table_id = azurerm_route_table.firewall[0].id
}

resource "azurerm_private_dns_zone" "main" {
  for_each = var.enable_private_networking ? local.private_dns_zones : toset([])

  name                = each.value
  resource_group_name = azurerm_resource_group.main.name
  tags                = local.standard_tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "main" {
  for_each = azurerm_private_dns_zone.main

  name                  = "link-${local.vnet_name}"
  resource_group_name   = azurerm_resource_group.main.name
  private_dns_zone_name = each.value.name
  virtual_network_id    = azurerm_virtual_network.main.id
  registration_enabled  = false
  tags                  = local.standard_tags
}

resource "azurerm_private_endpoint" "storage_blob" {
  count = var.enable_private_networking ? 1 : 0

  name                = "pep-${local.storage_name}-blob"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  subnet_id           = azurerm_subnet.private_endpoints.id
  tags                = local.standard_tags

  private_service_connection {
    name                           = "psc-${local.storage_name}-blob"
    private_connection_resource_id = azurerm_storage_account.main.id
    subresource_names              = ["blob"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "storage-blob"
    private_dns_zone_ids = [azurerm_private_dns_zone.main["privatelink.blob.core.windows.net"].id]
  }
}

resource "azurerm_private_endpoint" "cosmos" {
  count = var.enable_private_networking ? 1 : 0

  name                = "pep-${local.cosmos_name}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  subnet_id           = azurerm_subnet.private_endpoints.id
  tags                = local.standard_tags

  private_service_connection {
    name                           = "psc-${local.cosmos_name}"
    private_connection_resource_id = azurerm_cosmosdb_account.main.id
    subresource_names              = ["Sql"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "cosmos-sql"
    private_dns_zone_ids = [azurerm_private_dns_zone.main["privatelink.documents.azure.com"].id]
  }
}

resource "azurerm_private_endpoint" "search" {
  count = var.enable_private_networking ? 1 : 0

  name                = "pep-${local.search_name}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  subnet_id           = azurerm_subnet.private_endpoints.id
  tags                = local.standard_tags

  private_service_connection {
    name                           = "psc-${local.search_name}"
    private_connection_resource_id = azapi_resource.search.id
    subresource_names              = ["searchService"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "search"
    private_dns_zone_ids = [azurerm_private_dns_zone.main["privatelink.search.windows.net"].id]
  }
}

resource "azurerm_private_endpoint" "foundry" {
  count = var.enable_private_networking ? 1 : 0

  name                = "pep-${local.foundry_name}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  subnet_id           = azurerm_subnet.private_endpoints.id
  tags                = local.standard_tags

  private_service_connection {
    name                           = "psc-${local.foundry_name}"
    private_connection_resource_id = azapi_resource.foundry.id
    subresource_names              = ["account"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name = "foundry"
    private_dns_zone_ids = [
      azurerm_private_dns_zone.main["privatelink.cognitiveservices.azure.com"].id,
      azurerm_private_dns_zone.main["privatelink.openai.azure.com"].id,
      azurerm_private_dns_zone.main["privatelink.services.ai.azure.com"].id,
    ]
  }
}

resource "azurerm_private_endpoint" "acr" {
  count = var.enable_private_networking ? 1 : 0

  name                = "pep-${local.acr_name}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  subnet_id           = azurerm_subnet.private_endpoints.id
  tags                = local.standard_tags

  private_service_connection {
    name                           = "psc-${local.acr_name}"
    private_connection_resource_id = azurerm_container_registry.main.id
    subresource_names              = ["registry"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "acr"
    private_dns_zone_ids = [azurerm_private_dns_zone.main["privatelink.azurecr.io"].id]
  }
}

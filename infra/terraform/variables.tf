variable "subscription_id" {
  description = "Azure subscription ID for all workload resources."
  type        = string
}

variable "location" {
  description = "Azure region. Foundry and its injected VNet must use the same region."
  type        = string
  default     = "southeastasia"
}

variable "project_name" {
  description = "Short workload name used in generated Azure resource names."
  type        = string
  default     = "foundry-agent"
}

variable "environment" {
  description = "Deployment environment."
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "test", "uat", "prod"], var.environment)
    error_message = "environment must be dev, test, uat, or prod."
  }
}

variable "resource_group_name" {
  description = "Optional fixed resource-group name. Empty creates a generated name."
  type        = string
  default     = ""
}

variable "tags" {
  description = "Additional Azure tags."
  type        = map(string)
  default     = {}
}

variable "enable_private_networking" {
  description = "Enable Foundry VNet injection, private endpoints, and a private ACI UI."
  type        = bool
  default     = false
}

variable "vnet_address_space" {
  description = "Address space for the workload VNet."
  type        = list(string)
  default     = ["172.20.0.0/16"]
}

variable "agent_subnet_prefixes" {
  description = "Dedicated Foundry Agent Service subnet. /24 is recommended."
  type        = list(string)
  default     = ["172.20.0.0/24"]
}

variable "private_endpoint_subnet_prefixes" {
  description = "Subnet for workload private endpoints."
  type        = list(string)
  default     = ["172.20.1.0/24"]
}

variable "aci_subnet_prefixes" {
  description = "Dedicated subnet for the private Azure Container Instance UI."
  type        = list(string)
  default     = ["172.20.2.0/24"]
}

variable "existing_firewall_private_ip" {
  description = "Optional existing hub Azure Firewall IP used for 0/0 workload UDRs."
  type        = string
  default     = null
  nullable    = true
}

variable "model_deployment_name" {
  description = "Name exposed to the Hosted Agent for chat/reasoning."
  type        = string
  default     = "gpt-5.4-mini"
}

variable "model_name" {
  description = "Foundry model catalog name."
  type        = string
  default     = "gpt-5.4-mini"
}

variable "model_version" {
  description = "Foundry model version."
  type        = string
  default     = "2026-03-17"
}

variable "model_sku_name" {
  description = "Azure model deployment SKU."
  type        = string
  default     = "GlobalStandard"
}

variable "model_capacity" {
  description = "Model deployment capacity in provider-defined units."
  type        = number
  default     = 10
}

variable "embedding_deployment_name" {
  description = "Embedding deployment name used by ingestion and runtime retrieval."
  type        = string
  default     = "text-embedding-3-large"
}

variable "embedding_model_name" {
  description = "Embedding model catalog name."
  type        = string
  default     = "text-embedding-3-large"
}

variable "embedding_model_version" {
  description = "Embedding model version."
  type        = string
  default     = "1"
}

variable "embedding_capacity" {
  description = "Embedding deployment capacity."
  type        = number
  default     = 10
}

variable "vector_dimensions" {
  description = "Embedding vector dimensions. text-embedding-3-large defaults to 3072."
  type        = number
  default     = 3072
}

variable "agent_name" {
  description = "Stable Hosted Agent name."
  type        = string
  default     = "enterprise-knowledge-agent"
}

variable "search_index_name" {
  description = "Azure AI Search index created by the ingestion job."
  type        = string
  default     = "enterprise-knowledge"
}

variable "search_sku" {
  description = "Azure AI Search SKU."
  type        = string
  default     = "standard"
}

variable "storage_replication_type" {
  description = "Storage replication type."
  type        = string
  default     = "LRS"
}

variable "conversation_ttl_seconds" {
  description = "Cosmos conversation retention in seconds. -1 retains indefinitely."
  type        = number
  default     = 7776000
}

variable "log_retention_days" {
  description = "Log Analytics retention."
  type        = number
  default     = 30
}

variable "enable_telemetry" {
  description = "Configure Application Insights for the agent and UI."
  type        = bool
  default     = true
}

variable "ui_image" {
  description = "Full ACR URI for the web UI image. Empty defers ACI creation."
  type        = string
  default     = ""
}

variable "ui_cpu" {
  description = "ACI UI vCPU allocation."
  type        = number
  default     = 1
}

variable "ui_memory_gb" {
  description = "ACI UI memory allocation in GiB."
  type        = number
  default     = 2
}

variable "ui_title" {
  description = "Web UI title."
  type        = string
  default     = "Enterprise Knowledge Assistant"
}

variable "deployer_principal_id" {
  description = "Optional CI/CD principal object ID for image push, Hosted Agent deployment, and sample ingestion."
  type        = string
  default     = null
  nullable    = true
}

variable "deployer_principal_type" {
  description = "Azure principal type for deployer_principal_id."
  type        = string
  default     = "ServicePrincipal"

  validation {
    condition = contains(
      ["ServicePrincipal", "User", "Group", "ForeignGroup", "Device"],
      var.deployer_principal_type
    )
    error_message = "Unsupported Azure principal type."
  }
}

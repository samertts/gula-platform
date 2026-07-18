variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "name_prefix" {
  description = "Resource name prefix"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "subnet_ids" {
  description = "Private subnet IDs for EKS"
  type        = list(string)
}

variable "cluster_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.29"
}

variable "cluster_log_types" {
  description = "EKS control plane log types"
  type        = list(string)
  default     = ["api", "audit", "authenticator", "controllerManager", "scheduler"]
}

variable "node_group_config" {
  description = "Node group size configuration"
  type = object({
    system_min_size     = number
    system_max_size     = number
    system_desired_size = number
    app_min_size        = number
    app_max_size        = number
    app_desired_size    = number
    spot_min_size       = number
    spot_max_size       = number
    spot_desired_size   = number
  })
}

variable "instance_types" {
  description = "Instance types by node group"
  type = object({
    system     = string
    application = string
    spot       = string
  })
  default = {
    system     = "t3.medium"
    application = "m5.large"
    spot       = "c5.large"
  }
}

variable "cluster_autoscaler_enabled" {
  description = "Deploy cluster-autoscaler"
  type        = bool
  default     = true
}

variable "node_termination_handler_enabled" {
  description = "Deploy AWS node termination handler"
  type        = bool
  default     = true
}

variable "kms_key_arn" {
  description = "KMS key ARN for encryption"
  type        = string
  default     = ""
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}

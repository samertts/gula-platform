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

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs for RabbitMQ deployment"
  type        = list(string)
}

variable "security_group_ids" {
  description = "Security group IDs to attach to RabbitMQ broker"
  type        = list(string)
  default     = []
}

variable "instance_type" {
  description = "RabbitMQ broker instance type"
  type        = string
  default     = "mq.m6g.large"
}

variable "engine_version" {
  description = "RabbitMQ engine version"
  type        = string
  default     = "3.12"
}

variable "deployment_mode" {
  description = "RabbitMQ deployment mode (SINGLE_INSTANCE, CLUSTER_MULTI_AZ)"
  type        = string
  default     = "CLUSTER_MULTI_AZ"
}

variable "app_user_name" {
  description = "Application user name for RabbitMQ"
  type        = string
  default     = "gula_app"
}

variable "app_user_password" {
  description = "Application user password for RabbitMQ"
  type        = string
  sensitive   = true
}

variable "maintenance_window_day" {
  description = "Maintenance window day of week"
  type        = string
  default     = "SUNDAY"
}

variable "maintenance_window_time" {
  description = "Maintenance window time of day (HH:MM)"
  type        = string
  default     = "04:00"
}

variable "kms_key_arn" {
  description = "KMS key ARN for encryption"
  type        = string
  default     = ""
}

variable "prevent_destroy" {
  description = "Prevent destroy lifecycle on RabbitMQ broker"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}

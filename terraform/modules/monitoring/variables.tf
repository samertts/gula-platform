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
  default     = ""
}

variable "subnet_ids" {
  description = "Subnet IDs for monitoring resources"
  type        = list(string)
  default     = []
}

variable "eks_cluster_name" {
  description = "EKS cluster name for Prometheus target discovery"
  type        = string
  default     = ""
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

variable "monitoring_retention_days" {
  description = "Metrics retention in days"
  type        = number
  default     = 90
}

variable "enable_prometheus" {
  description = "Enable Amazon Managed Prometheus"
  type        = bool
  default     = true
}

variable "enable_grafana" {
  description = "Enable Grafana workspace"
  type        = bool
  default     = true
}

variable "enable_alertmanager" {
  description = "Enable managed Alertmanager"
  type        = bool
  default     = true
}

variable "enable_thanos" {
  description = "Enable Thanos for long-term storage"
  type        = bool
  default     = false
}

variable "grafana_admin_users" {
  description = "Grafana admin user emails"
  type        = list(string)
  default     = []
}

variable "grafana_editor_users" {
  description = "Grafana editor user emails"
  type        = list(string)
  default     = []
}

variable "grafana_viewer_users" {
  description = "Grafana viewer user emails"
  type        = list(string)
  default     = []
}

variable "amp_workspace_alias" {
  description = "Alias for AMP workspace"
  type        = string
  default     = ""
}

variable "notification_email" {
  description = "Email for SNS alert notifications"
  type        = string
  default     = ""
}

variable "pagerduty_integration_key" {
  description = "PagerDuty integration key"
  type        = string
  default     = ""
  sensitive   = true
}

variable "slack_webhook_url" {
  description = "Slack webhook URL"
  type        = string
  default     = ""
  sensitive   = true
}

variable "cpu_alarm_threshold" {
  description = "CPU alarm threshold percentage"
  type        = number
  default     = 80
}

variable "memory_alarm_threshold" {
  description = "Memory alarm threshold percentage"
  type        = number
  default     = 80
}

variable "disk_alarm_threshold" {
  description = "Disk alarm threshold percentage"
  type        = number
  default     = 80
}

variable "enable_dashboard" {
  description = "Enable CloudWatch dashboard"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "name_prefix" {
  description = "Resource name prefix"
  type        = string
}

variable "vault_name" {
  description = "Backup vault name"
  type        = string
  default     = ""
}

variable "kms_key_arn" {
  description = "KMS key ARN for backup encryption"
  type        = string
  default     = ""
}

variable "enable_backup" {
  description = "Enable AWS Backup"
  type        = bool
  default     = true
}

variable "enable_cross_region_backup" {
  description = "Enable cross-region backup copy"
  type        = bool
  default     = false
}

variable "cross_region_destination" {
  description = "Destination region for cross-region backup copy"
  type        = string
  default     = ""
}

variable "daily_backup_enabled" {
  description = "Enable daily backup plan"
  type        = bool
  default     = true
}

variable "daily_backup_time" {
  description = "Daily backup time in UTC (cron)"
  type        = string
  default     = "cron(0 3 * * ? *)"
}

variable "daily_cold_storage_after" {
  description = "Days after which to transition to cold storage (daily)"
  type        = number
  default     = 30
}

variable "daily_delete_after" {
  description = "Days after which to delete daily backups"
  type        = number
  default     = 35
}

variable "weekly_backup_enabled" {
  description = "Enable weekly backup plan"
  type        = bool
  default     = true
}

variable "weekly_backup_time" {
  description = "Weekly backup time in UTC (cron)"
  type        = string
  default     = "cron(0 4 ? * SUN *)"
}

variable "weekly_cold_storage_after" {
  description = "Days after which to transition to cold storage (weekly)"
  type        = number
  default     = 90
}

variable "weekly_delete_after" {
  description = "Days after which to delete weekly backups"
  type        = number
  default     = 120
}

variable "monthly_backup_enabled" {
  description = "Enable monthly backup plan"
  type        = bool
  default     = true
}

variable "monthly_backup_time" {
  description = "Monthly backup time in UTC (cron)"
  type        = string
  default     = "cron(0 5 1 * ? *)"
}

variable "monthly_cold_storage_after" {
  description = "Days after which to transition to cold storage (monthly)"
  type        = number
  default     = 180
}

variable "monthly_delete_after" {
  description = "Days after which to delete monthly backups"
  type        = number
  default     = 365
}

variable "resource_selections" {
  description = "Resources to back up by tag or ARN"
  type = list(object({
    selection_name = string
    resources      = list(string)
    tags           = map(string)
    not_resources  = list(string)
  }))
  default = [
    {
      selection_name = "all-resources"
      resources      = ["*"]
      tags           = {}
      not_resources  = []
    }
  ]
}

variable "notification_events" {
  description = "Backup events to notify on"
  type        = list(string)
  default     = ["BACKUP_JOB_COMPLETED", "RESTORE_JOB_COMPLETED", "BACKUP_JOB_FAILED", "RESTORE_JOB_FAILED"]
}

variable "notification_email" {
  description = "Email for backup notifications"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}

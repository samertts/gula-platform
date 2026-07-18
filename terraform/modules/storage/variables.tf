variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "name_prefix" {
  description = "Resource name prefix"
  type        = string
}

variable "kms_key_arn" {
  description = "KMS key ARN for S3 encryption"
  type        = string
  default     = ""
}

variable "force_destroy" {
  description = "Allow force destroy of buckets"
  type        = bool
  default     = false
}

variable "versioning_enabled" {
  description = "Enable S3 versioning"
  type        = bool
  default     = true
}

variable "enable_lifecycle_transitions" {
  description = "Enable S3 lifecycle transitions to IA/Glacier"
  type        = bool
  default     = true
}

variable "ia_transition_days" {
  description = "Days before transition to STANDARD_IA"
  type        = number
  default     = 30
}

variable "glacier_transition_days" {
  description = "Days before transition to GLACIER"
  type        = number
  default     = 90
}

variable "noncurrent_version_expiration_days" {
  description = "Days before noncurrent versions expire"
  type        = number
  default     = 90
}

variable "enforce_ssl" {
  description = "Enforce SSL on bucket policies"
  type        = bool
  default     = true
}

variable "public_read_access" {
  description = "Enable public read on public bucket"
  type        = bool
  default     = true
}

variable "log_expiration_days" {
  description = "Log bucket expiration in days"
  type        = number
  default     = 30
}

variable "backup_expiration_days" {
  description = "Backup bucket expiration in days"
  type        = number
  default     = 365
}

variable "enable_log_delivery_policy" {
  description = "Enable ALB/CloudFront log delivery policy"
  type        = bool
  default     = true
}

variable "replication_enabled" {
  description = "Enable cross-region replication"
  type        = bool
  default     = false
}

variable "replication_region" {
  description = "Destination region for replication"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}

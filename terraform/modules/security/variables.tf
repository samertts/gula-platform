variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "name_prefix" {
  description = "Resource name prefix"
  type        = string
}

variable "kms_deletion_window_in_days" {
  description = "KMS key deletion window in days"
  type        = number
  default     = 30
}

variable "enable_waf" {
  description = "Enable WAF web ACL"
  type        = bool
  default     = true
}

variable "waf_scope" {
  description = "WAF scope (REGIONAL or CLOUDFRONT)"
  type        = string
  default     = "REGIONAL"
}

variable "enable_waf_managed_rules" {
  description = "Enable AWS managed WAF rule groups"
  type        = bool
  default     = true
}

variable "rate_limit" {
  description = "Rate limit per 5-minute window"
  type        = number
  default     = 2000
}

variable "allowed_ip_set" {
  description = "List of allowed IPs for WAF IP set"
  type        = list(string)
  default     = []
}

variable "blocked_ip_set" {
  description = "List of blocked IPs for WAF IP set"
  type        = list(string)
  default     = []
}

variable "terraform_role_principals" {
  description = "List of IAM principals allowed to assume Terraform state role"
  type        = list(string)
  default     = []
}

variable "enable_guardduty" {
  description = "Enable GuardDuty"
  type        = bool
  default     = true
}

variable "enable_security_hub" {
  description = "Enable Security Hub"
  type        = bool
  default     = true
}

variable "security_hub_enable_default_standards" {
  description = "Enable Security Hub default standards"
  type        = bool
  default     = true
}

variable "enable_config" {
  description = "Enable AWS Config"
  type        = bool
  default     = true
}

variable "config_delivery_bucket" {
  description = "S3 bucket for AWS Config delivery"
  type        = string
  default     = ""
}

variable "enable_cloudtrail" {
  description = "Enable CloudTrail"
  type        = bool
  default     = true
}

variable "cloudtrail_bucket" {
  description = "S3 bucket for CloudTrail logs"
  type        = string
  default     = ""
}

variable "waf_logging_bucket" {
  description = "S3 bucket for WAF logs"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "name_prefix" {
  description = "Resource name prefix"
  type        = string
}

variable "domain_name" {
  description = "Primary domain name (e.g., gula.iq)"
  type        = string
}

variable "create_public_zone" {
  description = "Create public Route53 zone"
  type        = bool
  default     = true
}

variable "create_private_zone" {
  description = "Create private Route53 zone"
  type        = bool
  default     = false
}

variable "vpc_id" {
  description = "VPC ID for private zone association"
  type        = string
  default     = ""
}

variable "alb_dns_name" {
  description = "ALB DNS name for A/AAAA records"
  type        = string
  default     = ""
}

variable "alb_zone_id" {
  description = "ALB Route53 zone ID"
  type        = string
  default     = ""
}

variable "cdn_domain_name" {
  description = "CloudFront domain name"
  type        = string
  default     = ""
}

variable "cdn_hosted_zone_id" {
  description = "CloudFront hosted zone ID"
  type        = string
  default     = ""
}

variable "subdomain_records" {
  description = "Additional subdomain A/AAAA records (ALB alias)"
  type = map(object({
    type    = string
    ttl     = number
    records = list(string)
  }))
  default = {}
}

variable "txt_records" {
  description = "TXT records for domain verification"
  type = map(object({
    records = list(string)
    ttl     = number
  }))
  default = {}
}

variable "mx_records" {
  description = "MX records"
  type = list(object({
    preference = number
    hostname   = string
    ttl        = number
  }))
  default = []
}

variable "cname_records" {
  description = "CNAME records"
  type = map(object({
    target = string
    ttl    = number
  }))
  default = {}
}

variable "health_checks" {
  description = "Route53 health checks"
  type = map(object({
    fqdn              = string
    port              = number
    type              = string
    resource_path     = string
    failure_threshold = number
    request_interval  = number
  }))
  default = {}
}

variable "enable_failover" {
  description = "Enable DNS failover routing"
  type        = bool
  default     = false
}

variable "primary_alb_dns_name" {
  description = "Primary ALB DNS for failover"
  type        = string
  default     = ""
}

variable "primary_alb_zone_id" {
  description = "Primary ALB zone ID for failover"
  type        = string
  default     = ""
}

variable "secondary_alb_dns_name" {
  description = "Secondary (DR) ALB DNS for failover"
  type        = string
  default     = ""
}

variable "secondary_alb_zone_id" {
  description = "Secondary (DR) ALB zone ID for failover"
  type        = string
  default     = ""
}

variable "primary_health_check_id" {
  description = "Health check ID for primary failover"
  type        = string
  default     = ""
}

variable "enable_latency_routing" {
  description = "Enable latency-based routing"
  type        = bool
  default     = false
}

variable "latency_records" {
  description = "Latency-based routing records"
  type = map(object({
    region     = string
    dns_name   = string
    zone_id    = string
    evaluate_target_health = bool
  }))
  default = {}
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}

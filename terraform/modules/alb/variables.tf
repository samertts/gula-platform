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

variable "vpc_cidr_blocks" {
  description = "VPC CIDR blocks for egress restriction"
  type        = list(string)
  default     = ["10.0.0.0/8"]
}

variable "subnet_ids" {
  description = "Subnet IDs for ALB (public for internet-facing, private for internal)"
  type        = list(string)
}

variable "internal" {
  description = "Whether the ALB is internal"
  type        = bool
  default     = false
}

variable "deletion_protection" {
  description = "Enable ALB deletion protection"
  type        = bool
  default     = false
}

variable "idle_timeout" {
  description = "ALB idle timeout in seconds"
  type        = number
  default     = 60
}

variable "enable_http2" {
  description = "Enable HTTP/2"
  type        = bool
  default     = true
}

variable "certificate_arn" {
  description = "ACM certificate ARN for HTTPS listener"
  type        = string
  default     = ""
}

variable "security_group_ids" {
  description = "Security group IDs for ALB"
  type        = list(string)
  default     = []
}

variable "access_logs_bucket" {
  description = "S3 bucket for ALB access logs"
  type        = string
  default     = ""
}

variable "access_logs_prefix" {
  description = "S3 key prefix for ALB access logs"
  type        = string
  default     = "alb-logs"
}

variable "target_group_port" {
  description = "Target group port"
  type        = number
  default     = 8000
}

variable "target_group_protocol" {
  description = "Target group protocol (HTTP, HTTPS)"
  type        = string
  default     = "HTTP"
}

variable "health_check_path" {
  description = "Health check path"
  type        = string
  default     = "/health/ready"
}

variable "health_check_port" {
  description = "Health check port"
  type        = string
  default     = "traffic-port"
}

variable "health_check_matcher" {
  description = "HTTP success codes for health check"
  type        = string
  default     = "200"
}

variable "deregistration_delay" {
  description = "Deregistration delay in seconds"
  type        = number
  default     = 300
}

variable "drop_invalid_header_fields" {
  description = "Drop invalid HTTP header fields"
  type        = bool
  default     = true
}

variable "preserve_host_header" {
  description = "Preserve the Host header"
  type        = bool
  default     = false
}

variable "waf_arn" {
  description = "WAF web ACL ARN to associate with ALB"
  type        = string
  default     = ""
}

variable "additional_target_groups" {
  description = "Additional target groups for alternate ports"
  type = map(object({
    port              = number
    protocol          = string
    health_check_path = string
    health_check_matcher = string
    priority          = number
    host_header       = string
    path_pattern      = string
  }))
  default = {}
}

variable "ssl_policy" {
  description = "SSL policy for HTTPS listeners"
  type        = string
  default     = "ELBSecurityPolicy-TLS13-1-2-2021-06"
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}

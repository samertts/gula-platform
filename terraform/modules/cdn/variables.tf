variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "name_prefix" {
  description = "Resource name prefix"
  type        = string
}

variable "aliases" {
  description = "CNAME aliases for CloudFront"
  type        = list(string)
  default     = []
}

variable "acm_certificate_arn" {
  description = "ACM certificate ARN in us-east-1"
  type        = string
  default     = ""
}

variable "alb_origin_domain" {
  description = "ALB DNS name for the CDN origin"
  type        = string
  default     = ""
}

variable "alb_origin_http_port" {
  description = "ALB origin HTTP port"
  type        = number
  default     = 80
}

variable "alb_origin_https_port" {
  description = "ALB origin HTTPS port"
  type        = number
  default     = 443
}

variable "s3_origin_bucket_name" {
  description = "S3 bucket for static assets origin"
  type        = string
  default     = ""
}

variable "s3_origin_path" {
  description = "S3 origin path prefix"
  type        = string
  default     = ""
}

variable "default_root_object" {
  description = "Default root object for CloudFront"
  type        = string
  default     = "index.html"
}

variable "price_class" {
  description = "CloudFront price class (PriceClass_100, PriceClass_200, PriceClass_All)"
  type        = string
  default     = "PriceClass_100"
}

variable "geo_restriction_type" {
  description = "Geo restriction type (none, whitelist, blacklist)"
  type        = string
  default     = "none"
}

variable "geo_restriction_locations" {
  description = "Country codes for geo restriction"
  type        = list(string)
  default     = []
}

variable "waf_arn" {
  description = "WAF web ACL ARN (must be in us-east-1 for CloudFront)"
  type        = string
  default     = ""
}

variable "log_bucket_name" {
  description = "S3 bucket for CloudFront logs"
  type        = string
  default     = ""
}

variable "log_prefix" {
  description = "S3 prefix for CloudFront logs"
  type        = string
  default     = "cdn-logs/"
}

variable "enable_real_time_logs" {
  description = "Enable real-time logs via Kinesis"
  type        = bool
  default     = false
}

variable "forward_cookies" {
  description = "Cookie forwarding behavior (none, whitelist, all)"
  type        = string
  default     = "none"
}

variable "forward_query_string" {
  description = "Forward query strings to origin"
  type        = bool
  default     = true
}

variable "minimum_protocol_version" {
  description = "Minimum SSL/TLS protocol version"
  type        = string
  default     = "TLSv1.2_2021"
}

variable "lambda_edge_security_headers_arn" {
  description = "ARN of Lambda@Edge for security headers (must be in us-east-1)"
  type        = string
  default     = ""
}

variable "custom_error_responses" {
  description = "Custom error response configurations"
  type = map(object({
    error_code         = number
    response_page_path = string
    response_code      = string
    ttl                = number
  }))
  default = {
    "403" = {
      error_code         = 403
      response_page_path = "/index.html"
      response_code      = "200"
      ttl                = 60
    }
    "404" = {
      error_code         = 404
      response_page_path = "/index.html"
      response_code      = "200"
      ttl                = 60
    }
  }
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}

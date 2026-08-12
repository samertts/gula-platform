variable "environment" {
  description = "Deployment environment (dev, staging, pilot, prod, dr)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "pilot", "prod", "dr"], var.environment)
    error_message = "Environment must be one of: dev, staging, pilot, prod, dr."
  }
}

variable "aws_region" {
  description = "Primary AWS region"
  type        = string
  default     = "eu-west-1"
}

variable "aws_dr_region" {
  description = "Disaster Recovery AWS region"
  type        = string
  default     = "eu-central-1"
}

variable "aws_assume_role_arn" {
  description = "ARN of IAM role to assume for Terraform operations"
  type        = string
  default     = ""
}

variable "project_name" {
  description = "Project name for resource naming and tagging"
  type        = string
  default     = "gula"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones to deploy across"
  type        = list(string)
  default     = ["eu-west-1a", "eu-west-1b", "eu-west-1c"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.11.0/24", "10.0.12.0/24"]
}

variable "database_subnet_cidrs" {
  description = "CIDR blocks for database subnets"
  type        = list(string)
  default     = ["10.0.20.0/24", "10.0.21.0/24", "10.0.22.0/24"]
}

variable "elasticache_subnet_cidrs" {
  description = "CIDR blocks for ElastiCache subnets"
  type        = list(string)
  default     = ["10.0.30.0/24", "10.0.31.0/24", "10.0.32.0/24"]
}

variable "domain_name" {
  description = "Primary domain name (e.g., gula.iq)"
  type        = string
}

variable "subdomain" {
  description = "Environment subdomain prefix (e.g., api.dev.gula.iq)"
  type        = string
  default     = ""
}

variable "instance_types" {
  description = "EC2 instance types by purpose"
  type = object({
    general     = string
    compute     = string
    memory      = string
    database    = string
    cache       = string
    kubernetes  = string
  })
  default = {
    general    = "t3.medium"
    compute    = "c6i.xlarge"
    memory     = "r6i.xlarge"
    database   = "db.r6g.large"
    cache      = "cache.r6g.large"
    kubernetes = "t3.medium"
  }
}

variable "node_group_config" {
  description = "EKS node group configuration"
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
  default = {
    system_min_size     = 1
    system_max_size     = 3
    system_desired_size = 1
    app_min_size        = 1
    app_max_size        = 10
    app_desired_size    = 2
    spot_min_size       = 0
    spot_max_size       = 20
    spot_desired_size   = 2
  }
}

variable "db_instance_class" {
  description = "RDS instance class for PostgreSQL"
  type        = string
  default     = "db.r6g.large"
}

variable "db_allocated_storage" {
  description = "Allocated storage for PostgreSQL (GB)"
  type        = number
  default     = 100
}

variable "db_max_allocated_storage" {
  description = "Maximum autoscaling storage for PostgreSQL (GB)"
  type        = number
  default     = 500
}

variable "db_multi_az" {
  description = "Enable Multi-AZ for PostgreSQL"
  type        = bool
  default     = false
}

variable "db_backup_retention_period" {
  description = "Backup retention period in days"
  type        = number
  default     = 7
}

variable "db_deletion_protection" {
  description = "Enable deletion protection on database"
  type        = bool
  default     = true
}

variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.r6g.large"
}

variable "redis_num_cache_nodes" {
  description = "Number of Redis cache nodes"
  type        = number
  default     = 2
}

variable "redis_replicas_per_node_group" {
  description = "Replicas per Redis shard"
  type        = number
  default     = 1
}

variable "redis_shard_count" {
  description = "Number of Redis shards"
  type        = number
  default     = 1
}

variable "rabbitmq_instance_type" {
  description = "RabbitMQ EC2 instance type"
  type        = string
  default     = "m6i.large"
}

variable "rabbitmq_cluster_size" {
  description = "Number of RabbitMQ nodes"
  type        = number
  default     = 3
}

variable "eks_cluster_version" {
  description = "Kubernetes version for EKS"
  type        = string
  default     = "1.29"
}

variable "eks_cluster_log_types" {
  description = "List of EKS control plane log types"
  type        = list(string)
  default     = ["api", "audit", "authenticator", "controllerManager", "scheduler"]
}

variable "acm_certificate_arn" {
  description = "ARN of ACM certificate for HTTPS"
  type        = string
  default     = ""
}

variable "enable_waf" {
  description = "Enable AWS WAF on ALB and CDN"
  type        = bool
  default     = true
}

variable "enable_cdn" {
  description = "Enable CDN distribution"
  type        = bool
  default     = false
}

variable "enable_backup_cross_region" {
  description = "Enable cross-region backup replication"
  type        = bool
  default     = false
}

variable "enable_dr" {
  description = "Enable DR region infrastructure"
  type        = bool
  default     = false
}

variable "monitoring_retention_days" {
  description = "Metrics retention period in days"
  type        = number
  default     = 90
}

variable "log_retention_days" {
  description = "CloudWatch log retention period in days"
  type        = number
  default     = 30
}

variable "tags" {
  description = "Additional tags for all resources"
  type        = map(string)
  default     = {}
}

variable "s3_bucket_name_prefix" {
  description = "Prefix for S3 bucket names"
  type        = string
  default     = "gula"
}

variable "kms_deletion_window_in_days" {
  description = "KMS key deletion window in days"
  type        = number
  default     = 30
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnets"
  type        = bool
  default     = true
}

variable "single_nat_gateway" {
  description = "Use a single NAT Gateway instead of one per AZ"
  type        = bool
  default     = false
}

variable "enable_vpc_endpoints" {
  description = "Enable VPC endpoints for S3, DynamoDB, ECR, etc."
  type        = bool
  default     = true
}

variable "enable_flow_logs" {
  description = "Enable VPC flow logs"
  type        = bool
  default     = true
}

variable "cluster_autoscaler_enabled" {
  description = "Deploy cluster-autoscaler for EKS"
  type        = bool
  default     = true
}

variable "node_termination_handler_enabled" {
  description = "Deploy AWS node termination handler"
  type        = bool
  default     = true
}

variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access the ALB"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "allowed_ssh_cidr_blocks" {
  description = "CIDR blocks allowed SSH access"
  type        = list(string)
  default     = []
}

variable "pagerduty_integration_key" {
  description = "PagerDuty integration key for alerts"
  type        = string
  default     = ""
  sensitive   = true
}

variable "slack_webhook_url" {
  description = "Slack webhook URL for alert notifications"
  type        = string
  default     = ""
  sensitive   = true
}

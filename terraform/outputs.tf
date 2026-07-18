output "environment" {
  description = "Current deployment environment"
  value       = local.environment
}

output "vpc_id" {
  description = "VPC ID"
  value       = module.networking.vpc_id
}

output "vpc_cidr" {
  description = "VPC CIDR block"
  value       = module.networking.vpc_cidr
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = module.networking.private_subnet_ids
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = module.networking.public_subnet_ids
}

output "database_subnet_ids" {
  description = "Database subnet IDs"
  value       = module.networking.database_subnet_ids
}

output "elasticache_subnet_ids" {
  description = "ElastiCache subnet IDs"
  value       = module.networking.elasticache_subnet_ids
}

output "eks_cluster_name" {
  description = "EKS cluster name"
  value       = module.kubernetes.cluster_name
}

output "eks_cluster_endpoint" {
  description = "EKS cluster API endpoint"
  value       = module.kubernetes.cluster_endpoint
}

output "postgres_endpoint" {
  description = "PostgreSQL cluster endpoint"
  value       = module.postgres.endpoint
}

output "postgres_reader_endpoint" {
  description = "PostgreSQL reader endpoint (read replicas)"
  value       = module.postgres.reader_endpoint
}

output "redis_endpoint" {
  description = "Redis cluster endpoint"
  value       = module.redis.endpoint
}

output "redis_primary_endpoint" {
  description = "Redis primary endpoint"
  value       = module.redis.primary_endpoint
}

output "alb_dns_name" {
  description = "ALB DNS name"
  value       = module.alb.dns_name
}

output "alb_zone_id" {
  description = "ALB Route53 zone ID"
  value       = module.alb.zone_id
}

output "cdn_domain_name" {
  description = "CDN distribution domain name"
  value       = module.cdn.domain_name
}

output "cdn_distribution_id" {
  description = "CDN distribution ID"
  value       = module.cdn.distribution_id
}

output "route53_zone_id" {
  description = "Route53 zone ID"
  value       = module.dns.zone_id
}

output "route53_nameservers" {
  description = "Route53 zone nameservers"
  value       = module.dns.nameservers
}

output "monitoring_workspace_url" {
  description = "Grafana workspace URL"
  value       = module.monitoring.grafana_url
}

output "monitoring_prometheus_endpoint" {
  description = "Prometheus remote write endpoint"
  value       = module.monitoring.prometheus_endpoint
}

output "backup_vault_arn" {
  description = "Backup vault ARN"
  value       = module.backup.vault_arn
}

output "storage_private_bucket" {
  description = "Private storage bucket name"
  value       = module.storage.private_bucket_name
}

output "storage_public_bucket" {
  description = "Public storage bucket name"
  value       = module.storage.public_bucket_name
}

output "storage_logs_bucket" {
  description = "Logs bucket name"
  value       = module.storage.logs_bucket_name
}

output "kms_key_arn" {
  description = "KMS key ARN for general encryption"
  value       = module.security.kms_key_arn
}

output "kms_key_id" {
  description = "KMS key ID for general encryption"
  value       = module.security.kms_key_id
}

output "waf_arn" {
  description = "WAF web ACL ARN"
  value       = module.security.waf_arn
}

output "vpc_endpoints" {
  description = "Map of VPC endpoint IDs"
  value       = module.networking.vpc_endpoints
}

output "security_group_ids" {
  description = "Map of security group IDs"
  value = {
    vpc_default   = module.networking.default_security_group_id
    app           = module.networking.app_security_group_id
    database      = module.networking.database_security_group_id
    cache         = module.networking.cache_security_group_id
    alb           = module.networking.alb_security_group_id
  }
}

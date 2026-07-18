locals {
  environment = var.environment

  global_tags = merge({
    Project          = var.project_name
    Environment      = local.environment
    ManagedBy        = "terraform"
    Repository       = "https://github.com/samertts/gula-platform"
    CostCenter       = "gula-platform-${local.environment}"
    DataClassification = local.environment == "prod" ? "PHI" : "internal"
    SecurityZone     = local.environment == "prod" ? "production" : "non-production"
  }, var.tags)

  name_prefix = "${var.project_name}-${local.environment}"

  az_count = local.environment == "dev" ? 1 : local.environment == "staging" || local.environment == "pilot" ? 2 : 3
  azs      = slice(var.availability_zones, 0, local.az_count)

  is_production = local.environment == "prod"

  # Environment-specific CIDR adjustments
  vpc_cidr = var.vpc_cidr

  public_subnet_cidrs  = slice(var.public_subnet_cidrs, 0, local.az_count)
  private_subnet_cidrs = slice(var.private_subnet_cidrs, 0, local.az_count)
  database_subnet_cidrs = slice(var.database_subnet_cidrs, 0, local.az_count)
  elasticache_subnet_cidrs = slice(var.elasticache_subnet_cidrs, 0, local.az_count)

  # Subdomain for DNS records
  full_subdomain = var.subdomain != "" ? "${var.subdomain}.${var.domain_name}" : var.domain_name

  # S3 bucket naming
  s3_bucket_prefix = "${var.s3_bucket_name_prefix}-${local.environment}"

  # Backup retention
  backup_retention = local.environment == "prod" ? 35 : local.environment == "staging" || local.environment == "pilot" ? 14 : 7

  # Instance sizing by environment
  db_instance_class = local.environment == "prod" ? "db.r6g.xlarge" : local.environment == "staging" || local.environment == "pilot" ? "db.r6g.large" : "db.t3.medium"
  redis_node_type   = local.environment == "prod" ? "cache.r6g.xlarge" : local.environment == "staging" || local.environment == "pilot" ? "cache.r6g.large" : "cache.t3.medium"

  # Multi-AZ for high-availability environments
  db_multi_az          = local.is_production
  redis_multi_az       = local.is_production
  db_deletion_protection = local.is_production
}

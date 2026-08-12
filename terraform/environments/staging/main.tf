data "aws_caller_identity" "current" {}

locals {
  environment = "staging"
  name_prefix = "gula-staging"
}

module "networking" {
  source = "../../modules/networking"

  environment          = local.environment
  name_prefix          = local.name_prefix
  vpc_cidr             = "10.1.0.0/16"
  availability_zones   = slice(var.availability_zones, 0, 2)
  public_subnet_cidrs  = slice(var.public_subnet_cidrs, 0, 2)
  private_subnet_cidrs = slice(var.private_subnet_cidrs, 0, 2)
  database_subnet_cidrs  = slice(var.database_subnet_cidrs, 0, 2)
  elasticache_subnet_cidrs = slice(var.elasticache_subnet_cidrs, 0, 2)
  enable_nat_gateway   = true
  single_nat_gateway   = true
  enable_vpc_endpoints = true
  enable_flow_logs     = true
  log_retention_days   = 30
  tags                 = local.tags
}

module "security" {
  source = "../../modules/security"

  environment         = local.environment
  name_prefix         = local.name_prefix
  enable_waf          = true
  enable_guardduty    = true
  enable_security_hub = true
  enable_config       = true
  enable_cloudtrail   = true
  cloudtrail_bucket   = module.storage.logs_bucket_name
  config_delivery_bucket = module.storage.logs_bucket_name
  waf_logging_bucket  = module.storage.logs_bucket_name
  tags                = local.tags
}

module "storage" {
  source = "../../modules/storage"

  environment   = local.environment
  name_prefix   = local.name_prefix
  kms_key_arn   = module.security.kms_key_arn
  force_destroy = false
  log_expiration_days = 90
  backup_expiration_days = 90
  tags          = local.tags
}

module "postgres" {
  source = "../../modules/postgres"

  environment            = local.environment
  name_prefix            = local.name_prefix
  vpc_id                 = module.networking.vpc_id
  subnet_ids             = module.networking.database_subnet_ids
  database_subnet_group_name = module.networking.database_subnet_group_name
  security_group_ids     = [module.networking.database_security_group_id]
  instance_class         = "db.r6g.large"
  allocated_storage      = 100
  max_allocated_storage  = 500
  multi_az               = false
  backup_retention_period = 14
  deletion_protection    = true
  skip_final_snapshot    = false
  kms_key_arn            = module.security.kms_key_arn
  tags                   = local.tags
}

module "redis" {
  source = "../../modules/redis"

  environment        = local.environment
  name_prefix        = local.name_prefix
  subnet_group_name  = module.networking.elasticache_subnet_group_name
  security_group_ids = [module.networking.cache_security_group_id]
  node_type          = "cache.r6g.large"
  num_cache_nodes    = 2
  multi_az           = false
  cluster_mode_enabled = false
  kms_key_arn        = module.security.kms_key_arn
  tags               = local.tags
}

module "rabbitmq" {
  source = "../../modules/rabbitmq"

  environment   = local.environment
  name_prefix   = local.name_prefix
  vpc_id        = module.networking.vpc_id
  vpc_cidr      = "10.1.0.0/16"
  subnet_ids    = module.networking.private_subnet_ids
  instance_type = "mq.m5.large"
  deployment_mode = "CLUSTER_MULTI_AZ"
  app_user_password = var.rabbitmq_app_password
  kms_key_arn   = module.security.kms_key_arn
  prevent_destroy = true
  tags          = local.tags
}

module "kubernetes" {
  source = "../../modules/kubernetes"

  environment           = local.environment
  name_prefix           = local.name_prefix
  vpc_id                = module.networking.vpc_id
  subnet_ids            = module.networking.private_subnet_ids
  cluster_version       = "1.29"
  instance_types = {
    system      = "t3.large"
    application = "t3.large"
    spot        = "t3.large"
  }
  node_group_config = {
    system_min_size     = 1
    system_max_size     = 3
    system_desired_size = 1
    app_min_size        = 1
    app_max_size        = 5
    app_desired_size    = 2
    spot_min_size       = 0
    spot_max_size       = 5
    spot_desired_size   = 1
  }
  cluster_autoscaler_enabled    = true
  node_termination_handler_enabled = true
  kms_key_arn                   = module.security.kms_key_arn
  log_retention_days            = 30
  tags                          = local.tags
}

module "alb" {
  source = "../../modules/alb"

  environment     = local.environment
  name_prefix     = local.name_prefix
  vpc_id          = module.networking.vpc_id
  subnet_ids      = module.networking.public_subnet_ids
  internal        = false
  deletion_protection = true
  certificate_arn = var.acm_certificate_arn
  access_logs_bucket = module.storage.logs_bucket_name
  target_group_port = 8000
  health_check_path = "/health/ready"
  waf_arn         = module.security.waf_arn
  tags            = local.tags
}

module "cdn" {
  source = "../../modules/cdn"

  environment           = local.environment
  name_prefix           = local.name_prefix
  aliases               = ["staging.${var.domain_name}"]
  acm_certificate_arn   = var.acm_certificate_arn
  alb_origin_domain     = module.alb.dns_name
  s3_origin_bucket_name = module.storage.public_bucket_name
  price_class           = "PriceClass_100"
  waf_arn               = module.security.waf_arn
  log_bucket_name       = module.storage.logs_bucket_name
  tags                  = local.tags
}

module "dns" {
  source = "../../modules/dns"

  environment    = local.environment
  name_prefix    = local.name_prefix
  domain_name    = var.domain_name
  create_public_zone = true
  alb_dns_name   = module.alb.dns_name
  alb_zone_id    = module.alb.zone_id
  cdn_domain_name = module.cdn.domain_name
  cdn_hosted_zone_id = module.cdn.hosted_zone_id
  subdomain_records = {
    "api.staging" = { type = "A", ttl = 300, records = [] }
  }
  tags           = local.tags
}

module "monitoring" {
  source = "../../modules/monitoring"

  environment           = local.environment
  name_prefix           = local.name_prefix
  kms_key_arn           = module.security.kms_key_arn
  log_retention_days    = 30
  monitoring_retention_days = 30
  enable_prometheus     = true
  enable_grafana        = true
  enable_alertmanager   = true
  notification_email    = var.notification_email
  eks_cluster_name      = module.kubernetes.cluster_name
  tags                  = local.tags
}

module "backup" {
  source = "../../modules/backup"

  environment   = local.environment
  name_prefix   = local.name_prefix
  kms_key_arn   = module.security.kms_key_arn
  enable_backup = true
  daily_delete_after     = 14
  weekly_delete_after    = 60
  monthly_delete_after   = 180
  notification_email     = var.notification_email
  tags          = local.tags
}

locals {
  tags = merge({
    Environment = local.environment
    ManagedBy   = "terraform"
    Project     = "gula"
  }, var.tags)
}

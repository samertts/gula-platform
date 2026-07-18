data "aws_caller_identity" "current" {}

locals {
  environment = "prod"
  name_prefix = "gula-prod"
}

module "networking" {
  source = "../../modules/networking"

  environment          = local.environment
  name_prefix          = local.name_prefix
  vpc_cidr             = "10.3.0.0/16"
  availability_zones   = slice(var.availability_zones, 0, 3)
  public_subnet_cidrs  = slice(var.public_subnet_cidrs, 0, 3)
  private_subnet_cidrs = slice(var.private_subnet_cidrs, 0, 3)
  database_subnet_cidrs  = slice(var.database_subnet_cidrs, 0, 3)
  elasticache_subnet_cidrs = slice(var.elasticache_subnet_cidrs, 0, 3)
  enable_nat_gateway   = true
  single_nat_gateway   = false
  enable_vpc_endpoints = true
  enable_flow_logs     = true
  log_retention_days   = 90
  tags                 = local.tags
}

module "security" {
  source = "../../modules/security"

  environment         = local.environment
  name_prefix         = local.name_prefix
  enable_waf          = true
  waf_scope           = "REGIONAL"
  enable_guardduty    = true
  enable_security_hub = true
  enable_config       = true
  enable_cloudtrail   = true
  cloudtrail_bucket   = module.storage.logs_bucket_name
  config_delivery_bucket = module.storage.logs_bucket_name
  waf_logging_bucket  = module.storage.logs_bucket_name
  rate_limit          = 5000
  tags                = local.tags
}

module "storage" {
  source = "../../modules/storage"

  environment   = local.environment
  name_prefix   = local.name_prefix
  kms_key_arn   = module.security.kms_s3_key_arn
  force_destroy = false
  versioning_enabled     = true
  enable_lifecycle_transitions = true
  replication_enabled    = true
  replication_region     = var.aws_dr_region
  log_expiration_days    = 365
  backup_expiration_days = 365
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
  instance_class         = "db.r6g.xlarge"
  allocated_storage      = 500
  max_allocated_storage  = 2000
  multi_az               = true
  backup_retention_period = 35
  deletion_protection    = true
  skip_final_snapshot    = false
  kms_key_arn            = module.security.kms_rds_key_arn
  enable_read_replica    = true
  read_replica_region    = var.aws_dr_region
  tags                   = local.tags
}

module "redis" {
  source = "../../modules/redis"

  environment        = local.environment
  name_prefix        = local.name_prefix
  subnet_group_name  = module.networking.elasticache_subnet_group_name
  security_group_ids = [module.networking.cache_security_group_id]
  node_type          = "cache.r6g.xlarge"
  num_cache_nodes    = 3
  multi_az           = true
  cluster_mode_enabled = true
  shard_count        = 2
  replicas_per_node_group = 2
  kms_key_arn        = module.security.kms_key_arn
  tags               = local.tags
}

module "rabbitmq" {
  source = "../../modules/rabbitmq"

  environment   = local.environment
  name_prefix   = local.name_prefix
  vpc_id        = module.networking.vpc_id
  vpc_cidr      = "10.3.0.0/16"
  subnet_ids    = module.networking.private_subnet_ids
  instance_type = "mq.m5.xlarge"
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
    system      = "m5.xlarge"
    application = "m5.xlarge"
    spot        = "c5.xlarge"
  }
  node_group_config = {
    system_min_size     = 2
    system_max_size     = 5
    system_desired_size = 3
    app_min_size        = 3
    app_max_size        = 20
    app_desired_size    = 5
    spot_min_size       = 2
    spot_max_size       = 20
    spot_desired_size   = 5
  }
  cluster_autoscaler_enabled    = true
  node_termination_handler_enabled = true
  kms_key_arn                   = module.security.kms_key_arn
  log_retention_days            = 90
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
  idle_timeout    = 120
  ssl_policy      = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  tags            = local.tags
}

module "cdn" {
  source = "../../modules/cdn"

  environment           = local.environment
  name_prefix           = local.name_prefix
  aliases               = ["www.${var.domain_name}", var.domain_name]
  acm_certificate_arn   = var.acm_certificate_arn
  alb_origin_domain     = module.alb.dns_name
  s3_origin_bucket_name = module.storage.public_bucket_name
  price_class           = "PriceClass_All"
  waf_arn               = module.security.waf_arn
  log_bucket_name       = module.storage.logs_bucket_name
  geo_restriction_type  = "none"
  minimum_protocol_version = "TLSv1.2_2021"
  tags                  = local.tags
}

module "dns" {
  source = "../../modules/dns"

  environment    = local.environment
  name_prefix    = local.name_prefix
  domain_name    = var.domain_name
  create_public_zone = true
  create_private_zone = true
  vpc_id         = module.networking.vpc_id
  alb_dns_name   = module.alb.dns_name
  alb_zone_id    = module.alb.zone_id
  cdn_domain_name = module.cdn.domain_name
  cdn_hosted_zone_id = module.cdn.hosted_zone_id
  subdomain_records = {
    "api"     = { type = "A", ttl = 300, records = [] }
    "app"     = { type = "A", ttl = 300, records = [] }
    "admin"   = { type = "A", ttl = 300, records = [] }
  }
  txt_records = {
    "_dmarc"            = { records = ["v=DMARC1; p=quarantine; sp=quarantine; rua=mailto:dmarc@gula.iq; ruf=mailto:dmarc@gula.iq"], ttl = 3600 }
    "_spf.google.com"   = { records = ["v=spf1 include:_spf.google.com ~all"], ttl = 3600 }
    "google._domainkey" = { records = ["v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQ"], ttl = 3600 }
  }
  health_checks = {
    "api-health" = {
      fqdn              = "api.${var.domain_name}"
      port              = 443
      type              = "HTTPS"
      resource_path     = "/health/ready"
      failure_threshold = 3
      request_interval  = 30
    }
  }
  tags           = local.tags
}

module "monitoring" {
  source = "../../modules/monitoring"

  environment           = local.environment
  name_prefix           = local.name_prefix
  vpc_id                = module.networking.vpc_id
  subnet_ids            = module.networking.private_subnet_ids
  kms_key_arn           = module.security.kms_key_arn
  log_retention_days    = 90
  monitoring_retention_days = 90
  enable_prometheus     = true
  enable_grafana        = true
  enable_alertmanager   = true
  enable_thanos         = true
  notification_email    = var.notification_email
  pagerduty_integration_key = var.pagerduty_integration_key
  slack_webhook_url     = var.slack_webhook_url
  cpu_alarm_threshold   = 75
  memory_alarm_threshold = 75
  disk_alarm_threshold  = 80
  eks_cluster_name      = module.kubernetes.cluster_name
  tags                  = local.tags
}

module "backup" {
  source = "../../modules/backup"

  environment   = local.environment
  name_prefix   = local.name_prefix
  kms_key_arn   = module.security.kms_key_arn
  enable_backup = true
  enable_cross_region_backup = true
  cross_region_destination   = var.aws_dr_region
  daily_delete_after     = 35
  weekly_delete_after    = 120
  monthly_delete_after   = 365
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

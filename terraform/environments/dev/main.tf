data "aws_caller_identity" "current" {}

locals {
  environment = "dev"
  name_prefix = "gula-dev"
}

module "networking" {
  source = "../../modules/networking"

  environment          = local.environment
  name_prefix          = local.name_prefix
  vpc_cidr             = "10.0.0.0/16"
  availability_zones   = slice(var.availability_zones, 0, 1)
  public_subnet_cidrs  = slice(var.public_subnet_cidrs, 0, 1)
  private_subnet_cidrs = slice(var.private_subnet_cidrs, 0, 1)
  database_subnet_cidrs  = slice(var.database_subnet_cidrs, 0, 1)
  elasticache_subnet_cidrs = slice(var.elasticache_subnet_cidrs, 0, 1)
  enable_nat_gateway   = true
  single_nat_gateway   = true
  enable_vpc_endpoints = false
  enable_flow_logs     = false
  log_retention_days   = 14
  tags                 = local.tags
}

module "security" {
  source = "../../modules/security"

  environment         = local.environment
  name_prefix         = local.name_prefix
  enable_waf          = true
  enable_guardduty    = false
  enable_security_hub = false
  enable_config       = false
  enable_cloudtrail   = false
  kms_deletion_window_in_days = 7
  tags                = local.tags
}

module "storage" {
  source = "../../modules/storage"

  environment   = local.environment
  name_prefix   = local.name_prefix
  kms_key_arn   = module.security.kms_key_arn
  force_destroy = true
  log_expiration_days = 14
  backup_expiration_days = 30
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
  instance_class         = "db.t3.medium"
  allocated_storage      = 20
  max_allocated_storage  = 100
  multi_az               = false
  backup_retention_period = 7
  deletion_protection    = false
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
  node_type          = "cache.t3.medium"
  num_cache_nodes    = 1
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
  vpc_cidr      = "10.0.0.0/16"
  subnet_ids    = module.networking.private_subnet_ids
  instance_type = "mq.m5.large"
  deployment_mode = "SINGLE_INSTANCE"
  app_user_password = var.rabbitmq_app_password
  kms_key_arn   = module.security.kms_key_arn
  prevent_destroy = false
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
    system      = "t3.medium"
    application = "t3.medium"
    spot        = "t3.medium"
  }
  node_group_config = {
    system_min_size     = 1
    system_max_size     = 1
    system_desired_size = 1
    app_min_size        = 1
    app_max_size        = 3
    app_desired_size    = 1
    spot_min_size       = 0
    spot_max_size       = 0
    spot_desired_size   = 0
  }
  cluster_autoscaler_enabled    = false
  node_termination_handler_enabled = false
  kms_key_arn                   = module.security.kms_key_arn
  log_retention_days            = 14
  tags                          = local.tags
}

module "alb" {
  source = "../../modules/alb"

  environment     = local.environment
  name_prefix     = local.name_prefix
  vpc_id          = module.networking.vpc_id
  subnet_ids      = module.networking.public_subnet_ids
  internal        = false
  deletion_protection = false
  certificate_arn = ""
  access_logs_bucket = ""
  target_group_port = 8000
  health_check_path = "/health/ready"
  waf_arn         = module.security.waf_arn
  tags            = local.tags
}

locals {
  tags = merge({
    Environment = local.environment
    ManagedBy   = "terraform"
    Project     = "gula"
  }, var.tags)
}

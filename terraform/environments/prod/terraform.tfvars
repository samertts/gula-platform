environment      = "prod"
aws_region       = "eu-west-1"
aws_dr_region    = "eu-central-1"
project_name     = "gula"
domain_name      = "gula.iq"
subdomain        = "api"

availability_zones = ["eu-west-1a", "eu-west-1b", "eu-west-1c"]

public_subnet_cidrs  = ["10.3.1.0/24", "10.3.2.0/24", "10.3.3.0/24"]
private_subnet_cidrs = ["10.3.10.0/24", "10.3.11.0/24", "10.3.12.0/24"]
database_subnet_cidrs  = ["10.3.20.0/24", "10.3.21.0/24", "10.3.22.0/24"]
elasticache_subnet_cidrs = ["10.3.30.0/24", "10.3.31.0/24", "10.3.32.0/24"]

instance_types = {
  general    = "m5.xlarge"
  compute    = "c6i.2xlarge"
  memory     = "r6i.2xlarge"
  database   = "db.r6g.xlarge"
  cache      = "cache.r6g.xlarge"
  kubernetes = "m5.xlarge"
}

db_instance_class        = "db.r6g.xlarge"
db_allocated_storage     = 500
db_max_allocated_storage = 2000
db_multi_az              = true
db_backup_retention_period = 35
db_deletion_protection   = true

redis_node_type          = "cache.r6g.xlarge"
redis_num_cache_nodes    = 3
redis_replicas_per_node_group = 2
redis_shard_count        = 2

eks_cluster_version = "1.29"

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

enable_waf        = true
enable_cdn        = true
enable_dr         = true
enable_backup_cross_region = true

enable_nat_gateway = true
single_nat_gateway = false
enable_vpc_endpoints = true
enable_flow_logs     = true

monitoring_retention_days = 90
log_retention_days        = 90

cluster_autoscaler_enabled    = true
node_termination_handler_enabled = true

tags = {
  Environment = "prod"
  CostCenter  = "gula-platform-prod"
}

# These must be provided via -var-file or environment (sensitive)
# acm_certificate_arn     = "arn:aws:acm:us-east-1:...:certificate/..."
# notification_email      = "ops@gula.iq"
# rabbitmq_app_password   = "..."
# pagerduty_integration_key = "..."
# slack_webhook_url       = "..."

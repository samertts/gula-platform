environment      = "staging"
aws_region       = "eu-west-1"
project_name     = "gula"
domain_name      = "gula.iq"
subdomain        = "api.staging"

availability_zones = ["eu-west-1a", "eu-west-1b"]

public_subnet_cidrs  = ["10.1.1.0/24", "10.1.2.0/24"]
private_subnet_cidrs = ["10.1.10.0/24", "10.1.11.0/24"]
database_subnet_cidrs  = ["10.1.20.0/24", "10.1.21.0/24"]
elasticache_subnet_cidrs = ["10.1.30.0/24", "10.1.31.0/24"]

instance_types = {
  general    = "t3.large"
  compute    = "c6i.xlarge"
  memory     = "r6i.xlarge"
  database   = "db.r6g.large"
  cache      = "cache.r6g.large"
  kubernetes = "t3.large"
}

db_instance_class        = "db.r6g.large"
db_allocated_storage     = 100
db_max_allocated_storage = 500
db_multi_az              = false
db_backup_retention_period = 14
db_deletion_protection   = true

redis_node_type          = "cache.r6g.large"
redis_num_cache_nodes    = 2
redis_replicas_per_node_group = 1
redis_shard_count        = 1

eks_cluster_version = "1.29"

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

enable_waf        = true
enable_cdn        = true
enable_dr         = false
enable_backup_cross_region = false

enable_nat_gateway = true
single_nat_gateway = true
enable_vpc_endpoints = true
enable_flow_logs     = true

monitoring_retention_days = 30
log_retention_days        = 30

cluster_autoscaler_enabled    = true
node_termination_handler_enabled = true

tags = {
  Environment = "staging"
  CostCenter  = "gula-platform-staging"
}

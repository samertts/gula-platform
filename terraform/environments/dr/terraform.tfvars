environment      = "dr"
aws_region       = "eu-central-1"
aws_dr_region    = "eu-central-1"
project_name     = "gula"
domain_name      = "gula.iq"
subdomain        = "dr-api"

availability_zones = ["eu-central-1a", "eu-central-1b"]

public_subnet_cidrs  = ["10.4.1.0/24", "10.4.2.0/24"]
private_subnet_cidrs = ["10.4.10.0/24", "10.4.11.0/24"]
database_subnet_cidrs  = ["10.4.20.0/24", "10.4.21.0/24"]
elasticache_subnet_cidrs = ["10.4.30.0/24", "10.4.31.0/24"]

instance_types = {
  general    = "m5.xlarge"
  compute    = "c6i.xlarge"
  memory     = "r6i.xlarge"
  database   = "db.r6g.xlarge"
  cache      = "cache.r6g.large"
  kubernetes = "m5.xlarge"
}

db_instance_class        = "db.r6g.xlarge"
db_allocated_storage     = 500
db_max_allocated_storage = 2000
db_multi_az              = false
db_backup_retention_period = 7
db_deletion_protection   = true

redis_node_type          = "cache.r6g.large"
redis_num_cache_nodes    = 2

eks_cluster_version = "1.29"

node_group_config = {
  system_min_size     = 1
  system_max_size     = 3
  system_desired_size = 1
  app_min_size        = 1
  app_max_size        = 10
  app_desired_size    = 2
  spot_min_size       = 0
  spot_max_size       = 10
  spot_desired_size   = 1
}

enable_waf        = true
enable_cdn        = false
enable_dr         = false
enable_backup_cross_region = false

enable_nat_gateway = true
single_nat_gateway = true
enable_vpc_endpoints = true
enable_flow_logs     = true

monitoring_retention_days = 30
log_retention_days        = 90

cluster_autoscaler_enabled    = true
node_termination_handler_enabled = true

tags = {
  Environment = "dr"
  CostCenter  = "gula-platform-dr"
  DRFor       = "prod"
}

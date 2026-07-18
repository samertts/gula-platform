environment      = "dev"
aws_region       = "eu-west-1"
project_name     = "gula"
domain_name      = "gula.iq"
subdomain        = "api.dev"

availability_zones = ["eu-west-1a"]

public_subnet_cidrs  = ["10.0.1.0/24"]
private_subnet_cidrs = ["10.0.10.0/24"]
database_subnet_cidrs  = ["10.0.20.0/24"]
elasticache_subnet_cidrs = ["10.0.30.0/24"]

instance_types = {
  general    = "t3.medium"
  compute    = "t3.medium"
  memory     = "t3.medium"
  database   = "db.t3.medium"
  cache      = "cache.t3.medium"
  kubernetes = "t3.medium"
}

db_instance_class        = "db.t3.medium"
db_allocated_storage     = 20
db_max_allocated_storage = 100
db_multi_az              = false
db_backup_retention_period = 7
db_deletion_protection   = false

redis_node_type          = "cache.t3.medium"
redis_num_cache_nodes    = 1

eks_cluster_version = "1.29"

enable_waf        = true
enable_cdn        = false
enable_dr         = false
enable_backup_cross_region = false

enable_nat_gateway = true
single_nat_gateway = true
enable_vpc_endpoints = false
enable_flow_logs     = false

monitoring_retention_days = 14
log_retention_days        = 14

cluster_autoscaler_enabled    = false
node_termination_handler_enabled = false

tags = {
  Environment = "dev"
  CostCenter  = "gula-platform-dev"
}

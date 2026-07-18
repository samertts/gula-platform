output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.this.id
}

output "vpc_cidr" {
  description = "VPC CIDR block"
  value       = aws_vpc.this.cidr_block
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "database_subnet_ids" {
  description = "Database subnet IDs"
  value       = aws_subnet.database[*].id
}

output "database_subnet_group_name" {
  description = "Database subnet group name"
  value       = aws_db_subnet_group.this.name
}

output "elasticache_subnet_ids" {
  description = "ElastiCache subnet IDs"
  value       = aws_subnet.elasticache[*].id
}

output "elasticache_subnet_group_name" {
  description = "ElastiCache subnet group name"
  value       = aws_elasticache_subnet_group.this.name
}

output "default_security_group_id" {
  description = "VPC default security group ID"
  value       = aws_vpc.this.default_security_group_id
}

output "app_security_group_id" {
  description = "Application security group ID"
  value       = aws_security_group.app.id
}

output "database_security_group_id" {
  description = "Database security group ID"
  value       = aws_security_group.database.id
}

output "cache_security_group_id" {
  description = "Cache security group ID"
  value       = aws_security_group.cache.id
}

output "alb_security_group_id" {
  description = "ALB security group ID"
  value       = aws_security_group.alb.id
}

output "rabbitmq_security_group_id" {
  description = "RabbitMQ security group ID"
  value       = aws_security_group.rabbitmq.id
}

output "nat_gateway_ips" {
  description = "NAT Gateway public IPs"
  value       = aws_eip.nat[*].public_ip
}

output "vpc_endpoints" {
  description = "Map of VPC endpoint IDs"
  value = {
    s3            = try(aws_vpc_endpoint.s3[0].id, null)
    dynamodb      = try(aws_vpc_endpoint.dynamodb[0].id, null)
    ecr_api       = try(aws_vpc_endpoint.interface["ecr_api"].id, null)
    ecr_dkr       = try(aws_vpc_endpoint.interface["ecr_dkr"].id, null)
    ec2           = try(aws_vpc_endpoint.interface["ec2"].id, null)
    logs          = try(aws_vpc_endpoint.interface["logs"].id, null)
    monitoring    = try(aws_vpc_endpoint.interface["monitoring"].id, null)
    secretsmanager = try(aws_vpc_endpoint.interface["secretsmanager"].id, null)
  }
}

output "internet_gateway_id" {
  description = "Internet Gateway ID"
  value       = aws_internet_gateway.this.id
}

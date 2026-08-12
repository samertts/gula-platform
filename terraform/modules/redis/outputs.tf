output "id" {
  description = "Redis replication group ID"
  value       = aws_elasticache_replication_group.this.id
}

output "endpoint" {
  description = "Redis cluster endpoint (configuration endpoint for cluster mode)"
  value       = aws_elasticache_replication_group.this.configuration_endpoint
}

output "primary_endpoint" {
  description = "Redis primary endpoint"
  value       = aws_elasticache_replication_group.this.primary_endpoint_address
}

output "reader_endpoint" {
  description = "Redis reader endpoint"
  value       = aws_elasticache_replication_group.this.reader_endpoint_address
}

output "port" {
  description = "Redis port"
  value       = aws_elasticache_replication_group.this.port
}

output "auth_token_secret_arn" {
  description = "ARN of the Secrets Manager secret containing the auth token"
  value       = aws_secretsmanager_secret.redis_auth.arn
}

output "parameter_group_name" {
  description = "ElastiCache parameter group name"
  value       = aws_elasticache_parameter_group.this.name
}

output "cloudwatch_alarms" {
  description = "Map of CloudWatch alarm names"
  value = {
    cpu         = aws_cloudwatch_metric_alarm.redis_cpu.alarm_name
    memory      = aws_cloudwatch_metric_alarm.redis_memory.alarm_name
    connections = aws_cloudwatch_metric_alarm.redis_curr_connections.alarm_name
  }
}

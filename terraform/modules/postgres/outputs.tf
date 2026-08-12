output "endpoint" {
  description = "Primary PostgreSQL endpoint"
  value       = aws_db_instance.primary.address
}

output "port" {
  description = "PostgreSQL port"
  value       = aws_db_instance.primary.port
}

output "reader_endpoint" {
  description = "Reader endpoint (primary if no replicas)"
  value       = var.enable_read_replica ? aws_db_instance.read_replica[0].address : aws_db_instance.primary.address
}

output "master_username" {
  description = "Master username"
  value       = "gula_admin"
}

output "master_secret_arn" {
  description = "ARN of the Secrets Manager secret for master credentials"
  value       = aws_secretsmanager_secret.db_master.arn
}

output "db_name" {
  description = "Database name"
  value       = local.db_name
}

output "instance_id" {
  description = "RDS instance identifier"
  value       = aws_db_instance.primary.id
}

output "parameter_group_name" {
  description = "DB parameter group name"
  value       = aws_db_parameter_group.this.name
}

output "security_group_id" {
  description = "PgBouncer security group ID"
  value       = aws_security_group.pgbouncer.id
}

output "cloudwatch_alarms" {
  description = "Map of CloudWatch alarm names"
  value = {
    connections = aws_cloudwatch_metric_alarm.db_connections.alarm_name
    cpu         = aws_cloudwatch_metric_alarm.db_cpu.alarm_name
    storage     = aws_cloudwatch_metric_alarm.db_storage.alarm_name
    replica_lag = try(aws_cloudwatch_metric_alarm.db_replica_lag[0].alarm_name, null)
  }
}

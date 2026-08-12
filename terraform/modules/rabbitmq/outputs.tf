output "id" {
  description = "RabbitMQ broker ID"
  value       = aws_mq_broker.this.id
}

output "arn" {
  description = "RabbitMQ broker ARN"
  value       = aws_mq_broker.this.arn
}

output "endpoint" {
  description = "RabbitMQ broker AMQPS endpoint"
  value       = aws_mq_broker.this.endpoints[0]
}

output "amqp_endpoint" {
  description = "RabbitMQ broker AMQP endpoint"
  value       = try(aws_mq_broker.this.endpoints[1], aws_mq_broker.this.endpoints[0])
}

output "console_url" {
  description = "RabbitMQ management console URL"
  value       = aws_mq_broker.this.instances[0].console_url
}

output "admin_secret_arn" {
  description = "ARN of the Secrets Manager secret for admin credentials"
  value       = aws_secretsmanager_secret.rabbitmq_admin.arn
}

output "security_group_id" {
  description = "RabbitMQ security group ID"
  value       = aws_security_group.rabbitmq.id
}

output "cloudwatch_alarms" {
  description = "Map of CloudWatch alarm names"
  value = {
    cpu    = aws_cloudwatch_metric_alarm.rabbitmq_cpu.alarm_name
    memory = aws_cloudwatch_metric_alarm.rabbitmq_memory.alarm_name
    disk   = aws_cloudwatch_metric_alarm.rabbitmq_disk.alarm_name
  }
}

output "grafana_workspace_id" {
  description = "Grafana workspace ID"
  value       = try(aws_grafana_workspace.this[0].id, null)
}

output "grafana_endpoint" {
  description = "Grafana workspace endpoint URL"
  value       = try(aws_grafana_workspace.this[0].endpoint, null)
}

output "grafana_arn" {
  description = "Grafana workspace ARN"
  value       = try(aws_grafana_workspace.this[0].arn, null)
}

output "prometheus_workspace_id" {
  description = "AMP workspace ID"
  value       = try(aws_prometheus_workspace.this[0].id, null)
}

output "prometheus_endpoint" {
  description = "AMP remote write endpoint URL"
  value       = try(aws_prometheus_workspace.this[0].prometheus_endpoint, null)
}

output "prometheus_arn" {
  description = "AMP workspace ARN"
  value       = try(aws_prometheus_workspace.this[0].arn, null)
}

output "alertmanager_arn" {
  description = "Alertmanager rule group ARN"
  value       = try(aws_prometheus_alert_manager_definition.this[0].arn, null)
}

output "sns_topic_arn" {
  description = "SNS topic ARN for alerts"
  value       = try(aws_sns_topic.alerts[0].arn, null)
}

output "cloudwatch_log_group_names" {
  description = "Map of CloudWatch log group names"
  value = {
    application = aws_cloudwatch_log_group.application.name
    system      = aws_cloudwatch_log_group.system.name
    access      = aws_cloudwatch_log_group.access.name
  }
}

output "cloudwatch_dashboard_name" {
  description = "CloudWatch dashboard name"
  value       = try(aws_cloudwatch_dashboard.this[0].dashboard_name, null)
}

output "thanos_bucket_name" {
  description = "Thanos storage bucket name"
  value       = try(aws_s3_bucket.thanos[0].id, null)
}

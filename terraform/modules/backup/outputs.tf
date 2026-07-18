output "vault_id" {
  description = "Backup vault ID"
  value       = aws_backup_vault.this.id
}

output "vault_arn" {
  description = "Backup vault ARN"
  value       = aws_backup_vault.this.arn
}

output "vault_name" {
  description = "Backup vault name"
  value       = aws_backup_vault.this.name
}

output "daily_plan_id" {
  description = "Daily backup plan ID"
  value       = try(aws_backup_plan.daily[0].id, null)
}

output "daily_plan_arn" {
  description = "Daily backup plan ARN"
  value       = try(aws_backup_plan.daily[0].arn, null)
}

output "weekly_plan_id" {
  description = "Weekly backup plan ID"
  value       = try(aws_backup_plan.weekly[0].id, null)
}

output "weekly_plan_arn" {
  description = "Weekly backup plan ARN"
  value       = try(aws_backup_plan.weekly[0].arn, null)
}

output "monthly_plan_id" {
  description = "Monthly backup plan ID"
  value       = try(aws_backup_plan.monthly[0].id, null)
}

output "monthly_plan_arn" {
  description = "Monthly backup plan ARN"
  value       = try(aws_backup_plan.monthly[0].arn, null)
}

output "sns_topic_arn" {
  description = "SNS topic ARN for backup notifications"
  value       = try(aws_sns_topic.backup_notifications[0].arn, null)
}

output "iam_role_arn" {
  description = "Backup IAM role ARN"
  value       = aws_iam_role.backup.arn
}

output "cross_region_vault_arn" {
  description = "Cross-region backup vault ARN"
  value       = try(aws_backup_vault.cross_region[0].arn, null)
}

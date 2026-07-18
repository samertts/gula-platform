output "kms_key_arn" {
  description = "General KMS key ARN"
  value       = aws_kms_key.general.arn
}

output "kms_key_id" {
  description = "General KMS key ID"
  value       = aws_kms_key.general.key_id
}

output "kms_s3_key_arn" {
  description = "S3 KMS key ARN"
  value       = aws_kms_key.s3.arn
}

output "kms_rds_key_arn" {
  description = "RDS KMS key ARN"
  value       = aws_kms_key.rds.arn
}

output "waf_arn" {
  description = "WAF web ACL ARN"
  value       = try(aws_wafv2_web_acl.this[0].arn, null)
}

output "waf_id" {
  description = "WAF web ACL ID"
  value       = try(aws_wafv2_web_acl.this[0].id, null)
}

output "guardduty_detector_id" {
  description = "GuardDuty detector ID"
  value       = try(aws_guardduty_detector.this[0].id, null)
}

output "security_hub_enabled" {
  description = "Whether Security Hub is enabled"
  value       = var.enable_security_hub
}

output "terraform_state_role_arn" {
  description = "Terraform state IAM role ARN"
  value       = aws_iam_role.terraform_state.arn
}

output "general_secret_arn" {
  description = "General Secrets Manager secret ARN"
  value       = aws_secretsmanager_secret.general.arn
}

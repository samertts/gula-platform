output "private_bucket_id" {
  description = "Private bucket ID"
  value       = aws_s3_bucket.private.id
}

output "private_bucket_arn" {
  description = "Private bucket ARN"
  value       = aws_s3_bucket.private.arn
}

output "private_bucket_name" {
  description = "Private bucket name"
  value       = aws_s3_bucket.private.bucket
}

output "public_bucket_id" {
  description = "Public bucket ID"
  value       = aws_s3_bucket.public.id
}

output "public_bucket_arn" {
  description = "Public bucket ARN"
  value       = aws_s3_bucket.public.arn
}

output "public_bucket_name" {
  description = "Public bucket name"
  value       = aws_s3_bucket.public.bucket
}

output "logs_bucket_id" {
  description = "Logs bucket ID"
  value       = aws_s3_bucket.logs.id
}

output "logs_bucket_arn" {
  description = "Logs bucket ARN"
  value       = aws_s3_bucket.logs.arn
}

output "logs_bucket_name" {
  description = "Logs bucket name"
  value       = aws_s3_bucket.logs.bucket
}

output "backups_bucket_id" {
  description = "Backups bucket ID"
  value       = aws_s3_bucket.backups.id
}

output "backups_bucket_arn" {
  description = "Backups bucket ARN"
  value       = aws_s3_bucket.backups.arn
}

output "backups_bucket_name" {
  description = "Backups bucket name"
  value       = aws_s3_bucket.backups.bucket
}

output "replica_bucket_name" {
  description = "Replica bucket name"
  value       = try(aws_s3_bucket.replica[0].bucket, null)
}

output "replication_role_arn" {
  description = "S3 replication IAM role ARN"
  value       = try(aws_iam_role.replication[0].arn, null)
}

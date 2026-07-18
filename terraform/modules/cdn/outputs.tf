output "distribution_id" {
  description = "CloudFront distribution ID"
  value       = aws_cloudfront_distribution.this.id
}

output "domain_name" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.this.domain_name
}

output "hosted_zone_id" {
  description = "CloudFront Route53 zone ID"
  value       = aws_cloudfront_distribution.this.hosted_zone_id
}

output "arn" {
  description = "CloudFront distribution ARN"
  value       = aws_cloudfront_distribution.this.arn
}

output "status" {
  description = "CloudFront distribution status"
  value       = aws_cloudfront_distribution.this.status
}

output "origin_access_control_id" {
  description = "Origin Access Control ID for S3"
  value       = try(aws_cloudfront_origin_access_control.s3[0].id, null)
}

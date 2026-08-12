output "public_zone_id" {
  description = "Public Route53 zone ID"
  value       = try(aws_route53_zone.public[0].zone_id, null)
}

output "public_zone_arn" {
  description = "Public Route53 zone ARN"
  value       = try(aws_route53_zone.public[0].arn, null)
}

output "public_nameservers" {
  description = "Public Route53 zone nameservers"
  value       = try(aws_route53_zone.public[0].name_servers, [])
}

output "private_zone_id" {
  description = "Private Route53 zone ID"
  value       = try(aws_route53_zone.private[0].zone_id, null)
}

output "private_zone_arn" {
  description = "Private Route53 zone ARN"
  value       = try(aws_route53_zone.private[0].arn, null)
}

output "alb_record_fqdn" {
  description = "ALB A record FQDN"
  value       = var.alb_dns_name != "" ? try(aws_route53_record.alb[0].fqdn, null) : null
}

output "cdn_record_fqdn" {
  description = "CDN A record FQDN"
  value       = var.cdn_domain_name != "" ? try(aws_route53_record.cdn[0].fqdn, null) : null
}

output "health_check_ids" {
  description = "Map of health check IDs"
  value = {
    for k, v in aws_route53_health_check.this : k => v.id
  }
}

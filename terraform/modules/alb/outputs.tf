output "alb_id" {
  description = "ALB ID"
  value       = aws_lb.this.id
}

output "alb_arn" {
  description = "ALB ARN"
  value       = aws_lb.this.arn
}

output "dns_name" {
  description = "ALB DNS name"
  value       = aws_lb.this.dns_name
}

output "zone_id" {
  description = "ALB Route53 zone ID"
  value       = aws_lb.this.zone_id
}

output "target_group_arn" {
  description = "Default target group ARN"
  value       = aws_lb_target_group.main.arn
}

output "target_group_name" {
  description = "Default target group name"
  value       = aws_lb_target_group.main.name
}

output "http_listener_arn" {
  description = "HTTP listener ARN"
  value       = try(aws_lb_listener.http[0].arn, null)
}

output "https_listener_arn" {
  description = "HTTPS listener ARN"
  value       = try(aws_lb_listener.https[0].arn, null)
}

output "security_group_id" {
  description = "ALB security group ID"
  value       = aws_security_group.this.id
}

output "additional_target_group_arns" {
  description = "Map of additional target group ARNs"
  value = {
    for k, v in aws_lb_target_group.additional : k => v.arn
  }
}

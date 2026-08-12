output "cluster_id" {
  description = "EKS cluster ID"
  value       = aws_eks_cluster.this.id
}

output "cluster_name" {
  description = "EKS cluster name"
  value       = aws_eks_cluster.this.name
}

output "cluster_endpoint" {
  description = "EKS cluster API endpoint"
  value       = aws_eks_cluster.this.endpoint
}

output "cluster_ca_cert" {
  description = "EKS cluster CA certificate (base64)"
  value       = aws_eks_cluster.this.certificate_authority[0].data
}

output "cluster_arn" {
  description = "EKS cluster ARN"
  value       = aws_eks_cluster.this.arn
}

output "cluster_security_group_id" {
  description = "EKS cluster security group ID"
  value       = aws_eks_cluster.this.vpc_config[0].cluster_security_group_id
}

output "oidc_provider_arn" {
  description = "OIDC provider ARN"
  value       = aws_iam_openid_connect_provider.this.arn
}

output "oidc_provider_url" {
  description = "OIDC provider URL"
  value       = aws_iam_openid_connect_provider.this.url
}

output "node_role_arn" {
  description = "EKS node instance role ARN"
  value       = aws_iam_role.node.arn
}

output "cluster_autoscaler_role_arn" {
  description = "Cluster autoscaler IAM role ARN"
  value       = aws_iam_role.cluster_autoscaler.arn
}

output "node_security_group_id" {
  description = "EKS node security group ID"
  value       = aws_security_group.node.id
}

output "log_group_name" {
  description = "EKS control plane log group name"
  value       = aws_cloudwatch_log_group.eks.name
}

output "system_node_group_id" {
  description = "System node group ID"
  value       = aws_eks_node_group.system.id
}

output "app_node_group_id" {
  description = "Application node group ID"
  value       = aws_eks_node_group.application.id
}

output "spot_node_group_id" {
  description = "Spot node group ID"
  value       = aws_eks_node_group.spot.id
}

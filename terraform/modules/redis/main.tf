resource "random_password" "auth_token" {
  length           = 32
  special          = false
  min_upper        = 2
  min_lower        = 2
  min_numeric      = 2
}

locals {
  cluster_mode_enabled = var.cluster_mode_enabled
}

resource "aws_secretsmanager_secret" "redis_auth" {
  name                    = "${var.name_prefix}-redis-auth"
  description             = "Redis auth token for ${var.name_prefix}"
  kms_key_id              = var.kms_key_arn
  recovery_window_in_days = 7

  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "redis_auth" {
  secret_id     = aws_secretsmanager_secret.redis_auth.id
  secret_string = random_password.auth_token.result
}

resource "aws_elasticache_parameter_group" "this" {
  name        = "${var.name_prefix}-redis7"
  family      = "redis7"
  description = "Custom parameter group for ${var.name_prefix} Redis 7"

  parameter {
    name  = "activedefrag"
    value = "yes"
  }
  parameter {
    name  = "cluster-enabled"
    value = local.cluster_mode_enabled ? "yes" : "no"
  }
  parameter {
    name  = "notify-keyspace-events"
    value = "Ex"
  }
  parameter {
    name  = "lfu-decay-time"
    value = "1"
  }
  parameter {
    name  = "lfu-log-factor"
    value = "10"
  }
  parameter {
    name  = "timeout"
    value = "300"
  }
  parameter {
    name  = "tcp-keepalive"
    value = "300"
  }
  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }

  tags = var.tags
}

resource "aws_elasticache_replication_group" "this" {
  replication_group_id          = "${var.name_prefix}-redis"
  description                   = "Redis 7 cluster for ${var.name_prefix}"
  node_type                     = var.node_type
  port                          = 6379
  parameter_group_name          = aws_elasticache_parameter_group.this.name
  subnet_group_name             = var.subnet_group_name
  security_group_ids            = var.security_group_ids
  automatic_failover_enabled    = var.multi_az || var.cluster_mode_enabled
  multi_az_enabled              = var.multi_az
  num_cache_clusters            = local.cluster_mode_enabled ? null : var.num_cache_nodes
  num_node_groups               = local.cluster_mode_enabled ? var.shard_count : null
  replicas_per_node_group       = local.cluster_mode_enabled ? var.replicas_per_node_group : null
  engine_version                = var.engine_version
  at_rest_encryption_enabled    = true
  transit_encryption_enabled    = true
  auth_token                    = random_password.auth_token.result
  kms_key_id                    = var.kms_key_arn != "" ? var.kms_key_arn : null
  snapshot_retention_limit      = var.backup_retention_days
  snapshot_window               = var.backup_window
  maintenance_window            = var.maintenance_window
  auto_minor_version_upgrade    = true
  data_tiering_enabled          = false
  notification_topic_arn        = null

  lifecycle {
    prevent_destroy = false
    ignore_changes  = [num_cache_clusters]
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-redis"
  })
}

resource "aws_cloudwatch_metric_alarm" "redis_cpu" {
  alarm_name          = "${var.name_prefix}-redis-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ElastiCache"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Redis CPU utilization exceeds 80%"
  alarm_actions       = []

  dimensions = {
    CacheClusterId = aws_elasticache_replication_group.this.id
  }

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "redis_memory" {
  alarm_name          = "${var.name_prefix}-redis-high-memory"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "DatabaseMemoryUsagePercentage"
  namespace           = "AWS/ElastiCache"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Redis memory usage exceeds 80%"
  alarm_actions       = []

  dimensions = {
    CacheClusterId = aws_elasticache_replication_group.this.id
  }

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "redis_curr_connections" {
  alarm_name          = "${var.name_prefix}-redis-high-connections"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CurrConnections"
  namespace           = "AWS/ElastiCache"
  period              = 300
  statistic           = "Average"
  threshold           = 500
  alarm_description   = "Redis connections exceed 500"
  alarm_actions       = []

  dimensions = {
    CacheClusterId = aws_elasticache_replication_group.this.id
  }

  tags = var.tags
}

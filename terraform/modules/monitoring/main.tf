locals {
  has_notifications = var.notification_email != "" || var.pagerduty_integration_key != "" || var.slack_webhook_url != ""
}

# ── CloudWatch Log Groups ────────────────────────────────────────────────

resource "aws_cloudwatch_log_group" "application" {
  name              = "/${var.name_prefix}/application"
  retention_in_days = var.log_retention_days
  kms_key_id        = var.kms_key_arn != "" ? var.kms_key_arn : null

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-application-logs"
  })
}

resource "aws_cloudwatch_log_group" "system" {
  name              = "/${var.name_prefix}/system"
  retention_in_days = var.log_retention_days
  kms_key_id        = var.kms_key_arn != "" ? var.kms_key_arn : null

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-system-logs"
  })
}

resource "aws_cloudwatch_log_group" "access" {
  name              = "/${var.name_prefix}/access"
  retention_in_days = var.log_retention_days
  kms_key_id        = var.kms_key_arn != "" ? var.kms_key_arn : null

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-access-logs"
  })
}

# ── CloudWatch Metric Alarms (Global) ───────────────────────────────────

resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  alarm_name          = "${var.name_prefix}-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 300
  statistic           = "Average"
  threshold           = var.cpu_alarm_threshold
  alarm_description   = "EC2 CPU utilization exceeds ${var.cpu_alarm_threshold}%"
  alarm_actions       = try([aws_sns_topic.alerts[0].arn], [])
  ok_actions          = try([aws_sns_topic.alerts[0].arn], [])

  insufficient_data_actions = []
  treat_missing_data        = "notBreaching"

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "high_memory" {
  alarm_name          = "${var.name_prefix}-high-memory"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "MemoryUtilization"
  namespace           = "CWAgent"
  period              = 300
  statistic           = "Average"
  threshold           = var.memory_alarm_threshold
  alarm_description   = "Memory utilization exceeds ${var.memory_alarm_threshold}%"
  alarm_actions       = try([aws_sns_topic.alerts[0].arn], [])
  ok_actions          = try([aws_sns_topic.alerts[0].arn], [])

  insufficient_data_actions = []
  treat_missing_data        = "notBreaching"

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "high_disk" {
  alarm_name          = "${var.name_prefix}-high-disk"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "disk_used_percent"
  namespace           = "CWAgent"
  period              = 300
  statistic           = "Average"
  threshold           = var.disk_alarm_threshold
  alarm_description   = "Disk usage exceeds ${var.disk_alarm_threshold}%"
  alarm_actions       = try([aws_sns_topic.alerts[0].arn], [])
  ok_actions          = try([aws_sns_topic.alerts[0].arn], [])

  insufficient_data_actions = []
  treat_missing_data        = "notBreaching"

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "alb_5xx" {
  alarm_name          = "${var.name_prefix}-alb-5xx"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "HTTPCode_ELB_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "ALB 5XX errors exceed threshold"
  alarm_actions       = try([aws_sns_topic.alerts[0].arn], [])
  ok_actions          = try([aws_sns_topic.alerts[0].arn], [])

  insufficient_data_actions = []

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "alb_latency" {
  alarm_name          = "${var.name_prefix}-alb-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "TargetResponseTime"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Average"
  threshold           = 2.0
  alarm_description   = "ALB target response time exceeds 2 seconds"
  alarm_actions       = try([aws_sns_topic.alerts[0].arn], [])
  ok_actions          = try([aws_sns_topic.alerts[0].arn], [])

  insufficient_data_actions = []

  tags = var.tags
}

# ── CloudWatch Dashboard ─────────────────────────────────────────────────

resource "aws_cloudwatch_dashboard" "this" {
  count          = var.enable_dashboard ? 1 : 0
  dashboard_name = "${var.name_prefix}-operations"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ApplicationELB", "TargetResponseTime", { stat = "Average" }],
            [".", "RequestCount", { stat = "Sum" }],
            [".", "HTTPCode_ELB_5XX_Count", { stat = "Sum" }],
            [".", "HTTPCode_ELB_4XX_Count", { stat = "Sum" }],
          ]
          period = 300
          stat   = "Average"
          region = "eu-west-1"
          title  = "ALB Metrics"
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/RDS", "CPUUtilization", { stat = "Average" }],
            [".", "DatabaseConnections", { stat = "Average" }],
            [".", "FreeStorageSpace", { stat = "Average" }],
            [".", "ReadLatency", { stat = "Average" }],
          ]
          period = 300
          stat   = "Average"
          region = "eu-west-1"
          title  = "RDS Metrics"
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ElastiCache", "CPUUtilization", { stat = "Average" }],
            [".", "DatabaseMemoryUsagePercentage", { stat = "Average" }],
            [".", "CurrConnections", { stat = "Average" }],
          ]
          period = 300
          stat   = "Average"
          region = "eu-west-1"
          title  = "ElastiCache Metrics"
        }
      }
    ]
  })
}

# ── SNS Topic for Alerts ─────────────────────────────────────────────────

resource "aws_sns_topic" "alerts" {
  count             = local.has_notifications ? 1 : 0
  name              = "${var.name_prefix}-alerts"
  kms_master_key_id = var.kms_key_arn != "" ? "alias/aws/sns" : null

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-alerts"
  })
}

resource "aws_sns_topic_subscription" "email" {
  count     = var.notification_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alerts[0].arn
  protocol  = "email"
  endpoint  = var.notification_email
}

resource "aws_sns_topic_subscription" "pagerduty" {
  count     = var.pagerduty_integration_key != "" ? 1 : 0
  topic_arn = aws_sns_topic.alerts[0].arn
  protocol  = "https"
  endpoint  = "https://events.pagerduty.com/integration/${var.pagerduty_integration_key}/enqueue"
}

resource "aws_sns_topic_subscription" "slack" {
  count     = var.slack_webhook_url != "" ? 1 : 0
  topic_arn = aws_sns_topic.alerts[0].arn
  protocol  = "https"
  endpoint  = var.slack_webhook_url
}

# ── Amazon Managed Prometheus (AMP) ──────────────────────────────────────

resource "aws_prometheus_workspace" "this" {
  count       = var.enable_prometheus ? 1 : 0
  alias       = var.amp_workspace_alias != "" ? var.amp_workspace_alias : var.name_prefix

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-amp"
  })
}

resource "aws_prometheus_rule_group_namespace" "this" {
  count          = var.enable_prometheus ? 1 : 0
  name           = "${var.name_prefix}-rules"
  workspace_id   = aws_prometheus_workspace.this[0].id
  data           = <<EOF
groups:
  - name: gula-alerts
    rules:
    - alert: HighCPUUsage
      expr: avg by (instance) (cpu_usage_active) > 0.8
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "High CPU usage on {{ $labels.instance }}"
        description: "CPU usage is above 80% for 5 minutes"

    - alert: HighMemoryUsage
      expr: (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) > 0.8
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "High memory usage on {{ $labels.instance }}"
        description: "Memory usage is above 80% for 5 minutes"

    - alert: HighDiskUsage
      expr: (1 - node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) > 0.8
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High disk usage on {{ $labels.instance }}"
        description: "Disk usage is above 80%"
EOF
}

resource "aws_prometheus_alert_manager_definition" "this" {
  count        = var.enable_alertmanager ? 1 : 0
  workspace_id = aws_prometheus_workspace.this[0].id
  definition   = <<EOF
alertmanager_config: |
  route:
    receiver: default
    group_by: ['alertname', 'severity']
    group_wait: 30s
    group_interval: 5m
    repeat_interval: 4h
    routes:
    - receiver: critical
      match:
        severity: critical
      repeat_interval: 10m
  receivers:
  - name: default
    sns_configs:
    - topic_arn: ${try(aws_sns_topic.alerts[0].arn, "arn:aws:sns:us-east-1:000000000000:default")}
  - name: critical
    sns_configs:
    - topic_arn: ${try(aws_sns_topic.alerts[0].arn, "arn:aws:sns:us-east-1:000000000000:default")}
EOF
}

# ── Grafana Workspace ────────────────────────────────────────────────────

resource "aws_grafana_workspace" "this" {
  count             = var.enable_grafana ? 1 : 0
  name              = var.name_prefix
  description       = "Grafana workspace for ${var.name_prefix}"
  account_access    = "CURRENT_ACCOUNT"
  authentication_providers = ["AWS_SSO"]
  permission_type   = "SERVICE_MANAGED"
  data_sources      = ["PROMETHEUS", "CLOUDWATCH"]
  notification_destinations = var.slack_webhook_url != "" ? ["SNS"] : []

  role_arn = aws_iam_role.grafana[0].arn

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-grafana"
  })
}

resource "aws_iam_role" "grafana" {
  count = var.enable_grafana ? 1 : 0
  name  = "${var.name_prefix}-grafana"

  assume_role_policy = data.aws_iam_policy_document.grafana_assume[0].json

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-grafana-role"
  })
}

data "aws_iam_policy_document" "grafana_assume" {
  count = var.enable_grafana ? 1 : 0

  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["grafana.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

data "aws_caller_identity" "current" {}

resource "aws_grafana_role_association" "admin" {
  count        = var.enable_grafana && length(var.grafana_admin_users) > 0 ? 1 : 0
  workspace_id = aws_grafana_workspace.this[0].id
  role         = "ADMIN"
  user_ids     = var.grafana_admin_users
}

resource "aws_grafana_role_association" "editor" {
  count        = var.enable_grafana && length(var.grafana_editor_users) > 0 ? 1 : 0
  workspace_id = aws_grafana_workspace.this[0].id
  role         = "EDITOR"
  user_ids     = var.grafana_editor_users
}

resource "aws_grafana_role_association" "viewer" {
  count        = var.enable_grafana && length(var.grafana_viewer_users) > 0 ? 1 : 0
  workspace_id = aws_grafana_workspace.this[0].id
  role         = "VIEWER"
  user_ids     = var.grafana_viewer_users
}

# ── Grafana AMP Data Source Integration ──────────────────────────────────

resource "aws_grafana_workspace_api_key" "this" {
  count         = var.enable_grafana && var.enable_prometheus ? 1 : 0
  key_name      = "${var.name_prefix}-amp-key"
  key_role      = "ADMIN"
  workspace_id  = aws_grafana_workspace.this[0].id
}

# ── Thanos Long-term Storage ─────────────────────────────────────────────

resource "aws_s3_bucket" "thanos" {
  count         = var.enable_thanos ? 1 : 0
  bucket        = "${var.name_prefix}-thanos"
  force_destroy = !var.environment == "prod"

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-thanos"
  })
}

resource "aws_s3_bucket_versioning" "thanos" {
  count  = var.enable_thanos ? 1 : 0
  bucket = aws_s3_bucket.thanos[0].id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "thanos" {
  count  = var.enable_thanos ? 1 : 0
  bucket = aws_s3_bucket.thanos[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "thanos" {
  count  = var.enable_thanos ? 1 : 0
  bucket = aws_s3_bucket.thanos[0].id

  rule {
    id     = "abort-incomplete-mpu"
    status = "Enabled"
    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

resource "aws_s3_bucket_public_access_block" "thanos" {
  count                   = var.enable_thanos ? 1 : 0
  bucket                  = aws_s3_bucket.thanos[0].id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ── Log Subscription Filters ────────────────────────────────────────────

resource "aws_cloudwatch_log_subscription_filter" "application" {
  count           = var.notification_email != "" ? 1 : 0
  name            = "${var.name_prefix}-application-subscription"
  log_group_name  = aws_cloudwatch_log_group.application.name
  filter_pattern  = "[w=ERROR, m, ...]"
  destination_arn = aws_sns_topic.alerts[0].arn
  distribution    = "ByLogStream"
}

resource "aws_cloudwatch_log_subscription_filter" "system" {
  count           = var.notification_email != "" ? 1 : 0
  name            = "${var.name_prefix}-system-subscription"
  log_group_name  = aws_cloudwatch_log_group.system.name
  filter_pattern  = "[w=CRITICAL, m, ...]"
  destination_arn = aws_sns_topic.alerts[0].arn
  distribution    = "ByLogStream"
}

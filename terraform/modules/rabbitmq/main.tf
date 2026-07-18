resource "random_password" "rabbitmq_admin" {
  length           = 24
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
  min_upper        = 2
  min_lower        = 2
  min_numeric      = 2
  min_special      = 2
}

resource "aws_secretsmanager_secret" "rabbitmq_admin" {
  name                    = "${var.name_prefix}-rabbitmq-admin"
  description             = "Admin credentials for ${var.name_prefix} RabbitMQ"
  kms_key_id              = var.kms_key_arn
  recovery_window_in_days = 7

  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "rabbitmq_admin" {
  secret_id = aws_secretsmanager_secret.rabbitmq_admin.id
  secret_string = jsonencode({
    username = "gula_admin"
    password = random_password.rabbitmq_admin.result
  })
}

resource "aws_mq_broker" "this" {
  broker_name        = "${var.name_prefix}-rabbitmq"
  engine_type        = "RabbitMQ"
  engine_version     = var.engine_version
  host_instance_type = var.instance_type
  storage_type       = "ebs"
  authentication_strategy = "simple"
  auto_minor_version_upgrade = true
  deployment_mode    = var.deployment_mode
  subnet_ids         = var.deployment_mode == "CLUSTER_MULTI_AZ" ? var.subnet_ids : slice(var.subnet_ids, 0, 1)
  security_groups    = var.security_group_ids
  publicly_accessible = false
  apply_immediately  = false

  configuration {
    id       = aws_mq_configuration.this.id
    revision = aws_mq_configuration.this.latest_revision
  }

  encryption_options {
    use_aws_owned_key = var.kms_key_arn == ""
    kms_key_id        = var.kms_key_arn != "" ? var.kms_key_arn : null
  }

  logs {
    general = true
    audit   = true
  }

  maintenance_window_start_time {
    day_of_week = var.maintenance_window_day
    time_of_day = var.maintenance_window_time
    time_zone   = "UTC"
  }

  user {
    username = "gula_admin"
    password = random_password.rabbitmq_admin.result
    console_access = true
    groups   = ["administrators"]
  }

  user {
    username = var.app_user_name
    password = var.app_user_password
    console_access = false
    tags = {
      purpose = "application"
    }
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-rabbitmq"
  })

  lifecycle {
    prevent_destroy = var.prevent_destroy
  }
}

resource "aws_mq_configuration" "this" {
  name           = "${var.name_prefix}-rabbitmq-config"
  engine_type    = "RabbitMQ"
  engine_version = var.engine_version

  data = <<EOF
# GULA RabbitMQ Configuration
log.console = true
log.file = true
log.level = info
vm_memory_high_watermark.absolute = 2GB
heartbeat = 60
frame_max = 131072
channel_max = 2048
collect_statistics_interval = 10000
EOF

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-rabbitmq-config"
  })
}

resource "aws_security_group" "rabbitmq" {
  name_prefix = "${var.name_prefix}-rabbitmq-"
  description = "Security group for RabbitMQ managed by module"
  vpc_id      = var.vpc_id

  ingress {
    description = "AMQPS from VPC"
    from_port   = 5671
    to_port     = 5671
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  ingress {
    description = "AMQP from VPC"
    from_port   = 5672
    to_port     = 5672
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  ingress {
    description = "HTTPS management from VPC"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-rabbitmq-sg"
  })
}

resource "aws_cloudwatch_metric_alarm" "rabbitmq_cpu" {
  alarm_name          = "${var.name_prefix}-rabbitmq-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CpuUtilization"
  namespace           = "AWS/AmazonMQ"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "RabbitMQ broker CPU exceeds 80%"
  alarm_actions       = []

  dimensions = {
    Broker = aws_mq_broker.this.id
  }

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "rabbitmq_memory" {
  alarm_name          = "${var.name_prefix}-rabbitmq-high-memory"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/AmazonMQ"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "RabbitMQ broker memory exceeds 80%"
  alarm_actions       = []

  dimensions = {
    Broker = aws_mq_broker.this.id
  }

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "rabbitmq_disk" {
  alarm_name          = "${var.name_prefix}-rabbitmq-low-disk"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1
  metric_name         = "DiskUsage"
  namespace           = "AWS/AmazonMQ"
  period              = 600
  statistic           = "Average"
  threshold           = 20
  alarm_description   = "RabbitMQ available disk space below 20%"
  alarm_actions       = []

  dimensions = {
    Broker = aws_mq_broker.this.id
  }

  tags = var.tags
}

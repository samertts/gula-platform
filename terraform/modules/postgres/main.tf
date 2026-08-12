locals {
  db_name = "gula${var.environment == "prod" ? "" : "_${var.environment}"}"
}

resource "random_password" "db_master" {
  length           = 24
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
  min_upper        = 2
  min_lower        = 2
  min_numeric      = 2
  min_special      = 2
}

resource "aws_secretsmanager_secret" "db_master" {
  name                    = "${var.name_prefix}-db-master"
  description             = "Master credentials for ${var.name_prefix} PostgreSQL"
  kms_key_id              = var.kms_key_arn
  recovery_window_in_days = 7

  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "db_master" {
  secret_id = aws_secretsmanager_secret.db_master.id
  secret_string = jsonencode({
    username            = "gula_admin"
    password            = random_password.db_master.result
    engine              = "postgres"
    host                = aws_db_instance.primary.address
    port                = aws_db_instance.primary.port
    dbname              = local.db_name
    dbInstanceIdentifier = aws_db_instance.primary.identifier
  })
}

resource "aws_db_parameter_group" "this" {
  name        = "${var.name_prefix}-postgres16"
  family      = var.parameter_group_family
  description = "Custom parameter group for ${var.name_prefix} PostgreSQL 16"

  parameter {
    name  = "shared_preload_libraries"
    value = "pg_stat_statements,pg_buffercache,auto_explain,pgaudit"
  }

  parameter {
    name  = "pg_stat_statements.track"
    value = "ALL"
  }

  parameter {
    name  = "auto_explain.log_min_duration"
    value = "1000"
  }

  parameter {
    name  = "auto_explain.log_analyze"
    value = "1"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000"
  }

  parameter {
    name  = "log_connections"
    value = "1"
  }

  parameter {
    name  = "log_disconnections"
    value = "1"
  }

  parameter {
    name  = "log_checkpoints"
    value = "1"
  }

  parameter {
    name  = "log_lock_waits"
    value = "1"
  }

  parameter {
    name  = "log_autovacuum_min_duration"
    value = "0"
  }

  parameter {
    name  = "pgaudit.log"
    value = "ALL"
  }

  parameter {
    name  = "pgaudit.log_level"
    value = "notice"
  }

  parameter {
    name  = "random_page_cost"
    value = "1.1"
  }

  parameter {
    name  = "effective_cache_size"
    value = "{DBInstanceClassMemory*3/4}"
  }

  parameter {
    name  = "maintenance_work_mem"
    value = "{DBInstanceClassMemory*1/16}"
  }

  parameter {
    name  = "max_connections"
    value = "200"
  }

  tags = var.tags
}

resource "aws_db_option_group" "this" {
  name_prefix              = "${var.name_prefix}-postgres16-"
  engine_name              = "postgres"
  major_engine_version     = "16"

  tags = var.tags

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_db_instance" "primary" {
  identifier = "${var.name_prefix}-postgres"

  engine                      = "postgres"
  engine_version              = var.engine_version
  instance_class              = var.instance_class
  allocated_storage           = var.allocated_storage
  max_allocated_storage       = var.max_allocated_storage
  storage_type                = "gp3"
  storage_encrypted           = true
  kms_key_id                  = var.kms_key_arn

  db_name                     = local.db_name
  username                    = "gula_admin"
  password                    = random_password.db_master.result
  port                        = 5432

  db_subnet_group_name        = var.database_subnet_group_name
  vpc_security_group_ids      = var.security_group_ids
  parameter_group_name        = aws_db_parameter_group.this.name
  option_group_name           = aws_db_option_group.this.name

  multi_az                    = var.multi_az
  backup_retention_period     = var.backup_retention_period
  backup_window               = var.backup_window
  maintenance_window          = var.maintenance_window
  copy_tags_to_snapshot       = true

  delete_automated_backups    = false
  deletion_protection         = var.deletion_protection
  skip_final_snapshot         = var.skip_final_snapshot
  final_snapshot_identifier   = var.skip_final_snapshot ? null : "${var.name_prefix}-postgres-final-${formatdate("YYYYMMDD-HHmmss", timestamp())}"

  enabled_cloudwatch_logs_exports = [
    "postgresql",
    "upgrade",
  ]

  performance_insights_enabled          = true
  performance_insights_retention_period  = var.environment == "prod" ? 731 : 7
  monitoring_interval                   = 15
  monitoring_role_arn                   = aws_iam_role.rds_enhanced_monitoring[0].arn
  auto_minor_version_upgrade            = true

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-postgres"
  })
}

resource "aws_iam_role" "rds_enhanced_monitoring" {
  name_prefix          = "${var.name_prefix}-rds-monitor-"
  assume_role_policy   = data.aws_iam_policy_document.rds_monitoring_assume.json
  managed_policy_arns  = ["arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"]

  tags = var.tags
}

data "aws_iam_policy_document" "rds_monitoring_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["monitoring.rds.amazonaws.com"]
    }
  }
}

# ── Read Replica ────────────────────────────────────────────────────────

resource "aws_db_instance" "read_replica" {
  count = var.enable_read_replica ? 1 : 0

  identifier = "${var.name_prefix}-postgres-${var.read_replica_region != "" ? var.read_replica_region : "replica"}"

  engine                      = "postgres"
  engine_version              = var.engine_version
  instance_class              = var.instance_class
  allocated_storage           = var.allocated_storage
  max_allocated_storage       = var.max_allocated_storage
  storage_type                = "gp3"
  storage_encrypted           = true
  kms_key_id                  = var.kms_key_arn

  replicate_source_db         = aws_db_instance.primary.arn
  source_region               = var.read_replica_region

  vpc_security_group_ids      = var.security_group_ids
  parameter_group_name        = aws_db_parameter_group.this.name
  option_group_name           = aws_db_option_group.this.name

  backup_retention_period     = 7
  backup_window               = "05:00-06:00"
  maintenance_window          = "mon:06:00-mon:07:00"
  copy_tags_to_snapshot       = true
  deletion_protection         = var.deletion_protection
  skip_final_snapshot         = var.skip_final_snapshot

  performance_insights_enabled          = true
  performance_insights_retention_period  = 7
  monitoring_interval                   = 15
  monitoring_role_arn                   = aws_iam_role.rds_enhanced_monitoring[0].arn
  auto_minor_version_upgrade            = true

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-postgres-${var.read_replica_region}"
  })
}

# ── PgBouncer (EC2-side connection pooling) ─────────────────────────────
# Note: In production, deploy PgBouncer as sidecar in EKS or on dedicated
# instances. This resource creates the security group rules.
# For full PgBouncer deployment, use the Helm chart in the kubernetes module.

resource "aws_security_group" "pgbouncer" {
  name_prefix = "${var.name_prefix}-pgbouncer-"
  description = "Security group for PgBouncer connection pooler"
  vpc_id      = var.vpc_id

  ingress {
    description = "PgBouncer from app layer"
    from_port   = 6432
    to_port     = 6432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "All outbound to database"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-pgbouncer-sg"
  })
}

# ── CloudWatch Alarms ───────────────────────────────────────────────────

resource "aws_cloudwatch_metric_alarm" "db_connections" {
  alarm_name          = "${var.name_prefix}-db-high-connections"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "3"
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "150"
  alarm_description   = "Average database connections exceeds 150"
  alarm_actions       = []

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.primary.id
  }

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "db_cpu" {
  alarm_name          = "${var.name_prefix}-db-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "3"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "Average database CPU exceeds 80%"
  alarm_actions       = []

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.primary.id
  }

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "db_storage" {
  alarm_name          = "${var.name_prefix}-db-low-storage"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = var.allocated_storage * 1073741824 * 0.2
  alarm_description   = "Free storage space below 20%"
  alarm_actions       = []

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.primary.id
  }

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "db_replica_lag" {
  count = var.enable_read_replica ? 1 : 0

  alarm_name          = "${var.name_prefix}-db-replica-lag"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "3"
  metric_name         = "ReplicaLag"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "60"
  alarm_description   = "Replica lag exceeds 60 seconds"
  alarm_actions       = []

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.read_replica[0].id
  }

  tags = var.tags
}

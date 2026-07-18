locals {
  vault_name           = var.vault_name != "" ? var.vault_name : "${var.name_prefix}-backup-vault"
  has_notifications    = var.notification_email != ""
  has_cross_region     = var.enable_cross_region_backup && var.cross_region_destination != ""
}

data "aws_caller_identity" "current" {}

# ── IAM Role for Backup ──────────────────────────────────────────────────

resource "aws_iam_role" "backup" {
  count              = var.enable_backup ? 1 : 0
  name               = "${var.name_prefix}-backup-role"
  assume_role_policy = data.aws_iam_policy_document.backup_assume[0].json

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-backup-role"
  })
}

data "aws_iam_policy_document" "backup_assume" {
  count = var.enable_backup ? 1 : 0

  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["backup.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "backup" {
  count      = var.enable_backup ? 1 : 0
  role       = aws_iam_role.backup[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup"
}

resource "aws_iam_role_policy_attachment" "restore" {
  count      = var.enable_backup ? 1 : 0
  role       = aws_iam_role.backup[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForRestores"
}

# ── Backup Vault ─────────────────────────────────────────────────────────

resource "aws_backup_vault" "this" {
  count       = var.enable_backup ? 1 : 0
  name        = local.vault_name
  kms_key_arn = var.kms_key_arn != "" ? var.kms_key_arn : null

  tags = merge(var.tags, {
    Name = local.vault_name
  })
}

# ── Cross-Region Backup Vault ────────────────────────────────────────────

resource "aws_backup_vault" "cross_region" {
  provider = aws.dr
  count    = local.has_cross_region ? 1 : 0
  name     = "${var.name_prefix}-backup-vault-dr"

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-backup-vault-dr"
  })
}

# ── Daily Backup Plan ────────────────────────────────────────────────────

resource "aws_backup_plan" "daily" {
  count = var.enable_backup && var.daily_backup_enabled ? 1 : 0
  name  = "${var.name_prefix}-daily-backup"

  rule {
    rule_name         = "${var.name_prefix}-daily"
    target_vault_name = aws_backup_vault.this[0].name
    schedule          = var.daily_backup_time
    start_window      = 60
    completion_window = 180

    lifecycle {
      cold_storage_after = var.daily_cold_storage_after
      delete_after       = var.daily_delete_after
    }

    dynamic "copy_action" {
      for_each = local.has_cross_region ? [1] : []
      content {
        destination_vault_arn = aws_backup_vault.cross_region[0].arn
        lifecycle {
          cold_storage_after = var.daily_cold_storage_after
          delete_after       = var.daily_delete_after
        }
      }
    }

    recovery_point_tags = merge(var.tags, {
      BackupType = "daily"
    })
  }

  advanced_backup_setting {
    resource_type = "RDS"
    backup_options = {
      WindowsVSS = "disabled"
    }
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-daily-backup"
  })
}

resource "aws_backup_selection" "daily" {
  count        = var.enable_backup && var.daily_backup_enabled ? 1 : 0
  name         = "${var.name_prefix}-daily-selection"
  plan_id      = aws_backup_plan.daily[0].id
  iam_role_arn = aws_iam_role.backup[0].arn

  dynamic "resources" {
    for_each = var.resource_selections[0].resources
    content {
      type = resources.value
    }
  }

  dynamic "selection_tag" {
    for_each = var.resource_selections[0].tags
    content {
      type  = "STRING_EQUALS"
      key   = selection_tag.key
      value = selection_tag.value
    }
  }
}

# ── Weekly Backup Plan ───────────────────────────────────────────────────

resource "aws_backup_plan" "weekly" {
  count = var.enable_backup && var.weekly_backup_enabled ? 1 : 0
  name  = "${var.name_prefix}-weekly-backup"

  rule {
    rule_name         = "${var.name_prefix}-weekly"
    target_vault_name = aws_backup_vault.this[0].name
    schedule          = var.weekly_backup_time
    start_window      = 60
    completion_window = 180

    lifecycle {
      cold_storage_after = var.weekly_cold_storage_after
      delete_after       = var.weekly_delete_after
    }

    dynamic "copy_action" {
      for_each = local.has_cross_region ? [1] : []
      content {
        destination_vault_arn = aws_backup_vault.cross_region[0].arn
        lifecycle {
          cold_storage_after = var.weekly_cold_storage_after
          delete_after       = var.weekly_delete_after
        }
      }
    }

    recovery_point_tags = merge(var.tags, {
      BackupType = "weekly"
    })
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-weekly-backup"
  })
}

resource "aws_backup_selection" "weekly" {
  count        = var.enable_backup && var.weekly_backup_enabled ? 1 : 0
  name         = "${var.name_prefix}-weekly-selection"
  plan_id      = aws_backup_plan.weekly[0].id
  iam_role_arn = aws_iam_role.backup[0].arn

  resources = var.resource_selections[0].resources
}

# ── Monthly Backup Plan ──────────────────────────────────────────────────

resource "aws_backup_plan" "monthly" {
  count = var.enable_backup && var.monthly_backup_enabled ? 1 : 0
  name  = "${var.name_prefix}-monthly-backup"

  rule {
    rule_name         = "${var.name_prefix}-monthly"
    target_vault_name = aws_backup_vault.this[0].name
    schedule          = var.monthly_backup_time
    start_window      = 120
    completion_window = 240

    lifecycle {
      cold_storage_after = var.monthly_cold_storage_after
      delete_after       = var.monthly_delete_after
    }

    dynamic "copy_action" {
      for_each = local.has_cross_region ? [1] : []
      content {
        destination_vault_arn = aws_backup_vault.cross_region[0].arn
        lifecycle {
          cold_storage_after = var.monthly_cold_storage_after
          delete_after       = var.monthly_delete_after
        }
      }
    }

    recovery_point_tags = merge(var.tags, {
      BackupType = "monthly"
    })
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-monthly-backup"
  })
}

resource "aws_backup_selection" "monthly" {
  count        = var.enable_backup && var.monthly_backup_enabled ? 1 : 0
  name         = "${var.name_prefix}-monthly-selection"
  plan_id      = aws_backup_plan.monthly[0].id
  iam_role_arn = aws_iam_role.backup[0].arn

  resources = var.resource_selections[0].resources
}

# ── SNS Notifications ────────────────────────────────────────────────────

resource "aws_sns_topic" "backup_notifications" {
  count  = local.has_notifications ? 1 : 0
  name   = "${var.name_prefix}-backup-notifications"

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-backup-notifications"
  })
}

resource "aws_sns_topic_subscription" "backup_email" {
  count     = local.has_notifications ? 1 : 0
  topic_arn = aws_sns_topic.backup_notifications[0].arn
  protocol  = "email"
  endpoint  = var.notification_email
}

resource "aws_backup_vault_notifications" "this" {
  count  = local.has_notifications ? 1 : 0
  backup_vault_name = aws_backup_vault.this[0].name
  sns_topic_arn     = aws_sns_topic.backup_notifications[0].arn
  backup_vault_events = var.notification_events
}

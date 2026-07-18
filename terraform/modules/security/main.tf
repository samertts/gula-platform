# ── KMS Keys ─────────────────────────────────────────────────────────────

resource "aws_kms_key" "general" {
  description             = "GULA ${var.environment} general purpose encryption key"
  deletion_window_in_days = var.kms_deletion_window_in_days
  enable_key_rotation     = true
  policy                  = data.aws_iam_policy_document.kms_general.json

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-general-kms"
  })
}

resource "aws_kms_alias" "general" {
  name          = "alias/${var.name_prefix}-general"
  target_key_id = aws_kms_key.general.key_id
}

resource "aws_kms_key" "s3" {
  description             = "GULA ${var.environment} S3 encryption key"
  deletion_window_in_days = var.kms_deletion_window_in_days
  enable_key_rotation     = true

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-s3-kms"
  })
}

resource "aws_kms_alias" "s3" {
  name          = "alias/${var.name_prefix}-s3"
  target_key_id = aws_kms_key.s3.key_id
}

resource "aws_kms_key" "rds" {
  description             = "GULA ${var.environment} RDS encryption key"
  deletion_window_in_days = var.kms_deletion_window_in_days
  enable_key_rotation     = true

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-rds-kms"
  })
}

resource "aws_kms_alias" "rds" {
  name          = "alias/${var.name_prefix}-rds"
  target_key_id = aws_kms_key.rds.key_id
}

resource "aws_kms_key" "cloudtrail" {
  description             = "GULA ${var.environment} CloudTrail encryption key"
  deletion_window_in_days = var.kms_deletion_window_in_days
  enable_key_rotation     = true

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-cloudtrail-kms"
  })
}

resource "aws_kms_alias" "cloudtrail" {
  name          = "alias/${var.name_prefix}-cloudtrail"
  target_key_id = aws_kms_key.cloudtrail.key_id
}

data "aws_iam_policy_document" "kms_general" {
  statement {
    sid    = "EnableIAMUserPermissions"
    effect = "Allow"
    principals {
      type = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }
    actions   = ["kms:*"]
    resources = ["*"]
  }
}

data "aws_caller_identity" "current" {}

# ── WAF Web ACL ─────────────────────────────────────────────────────────

resource "aws_wafv2_web_acl" "this" {
  count       = var.enable_waf ? 1 : 0
  name        = "${var.name_prefix}-web-acl"
  description = "WAF Web ACL for ${var.name_prefix}"
  scope       = var.waf_scope

  default_action {
    allow {}
  }

  # AWS Managed Rule Groups
  dynamic "rule" {
    for_each = var.enable_waf_managed_rules ? [1] : []
    content {
      name     = "AWS-AWSManagedRulesCommonRuleSet"
      priority = 10

      override_action {
        none {}
      }

      statement {
        managed_rule_group_statement {
          name        = "AWSManagedRulesCommonRuleSet"
          vendor_name = "AWS"
          excluded_rule {
            name = "NoUserAgent_HEADER"
          }
        }
      }

      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = "${var.name_prefix}-aws-common-rules"
        sampled_requests_enabled   = true
      }
    }
  }

  rule {
    name     = "AWS-AWSManagedRulesSQLiRuleSet"
    priority = 20

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesSQLiRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${var.name_prefix}-aws-sqli-rules"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "AWS-AWSManagedRulesKnownBadInputsRuleSet"
    priority = 30

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${var.name_prefix}-aws-known-bad-inputs"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "rate-limiting"
    priority = 100

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = var.rate_limit
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${var.name_prefix}-rate-limit"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "AWS-AWSManagedRulesAmazonIpReputationList"
    priority = 40

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesAmazonIpReputationList"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${var.name_prefix}-aws-ip-rep"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "AWS-AWSManagedRulesAnonymousIpList"
    priority = 50

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesAnonymousIpList"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${var.name_prefix}-aws-anon-ip"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.name_prefix}-waf"
    sampled_requests_enabled   = true
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-web-acl"
  })
}

resource "aws_wafv2_ip_set" "allowed" {
  count              = length(var.allowed_ip_set) > 0 ? 1 : 0
  name               = "${var.name_prefix}-allowed-ips"
  description        = "Allowed IP set for ${var.name_prefix}"
  scope              = var.waf_scope
  ip_address_version = "IPV4"
  addresses          = var.allowed_ip_set

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-allowed-ips"
  })
}

resource "aws_wafv2_ip_set" "blocked" {
  count              = length(var.blocked_ip_set) > 0 ? 1 : 0
  name               = "${var.name_prefix}-blocked-ips"
  description        = "Blocked IP set for ${var.name_prefix}"
  scope              = var.waf_scope
  ip_address_version = "IPV4"
  addresses          = var.blocked_ip_set

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-blocked-ips"
  })
}

# ── IAM Roles ───────────────────────────────────────────────────────────

resource "aws_iam_role" "terraform_state" {
  name               = "${var.name_prefix}-terraform-state"
  assume_role_policy = data.aws_iam_policy_document.terraform_state_assume.json

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-terraform-state-role"
  })
}

data "aws_iam_policy_document" "terraform_state_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "AWS"
      identifiers = var.terraform_role_principals
    }
  }
}

resource "aws_iam_policy" "terraform_state" {
  name   = "${var.name_prefix}-terraform-state-policy"
  policy = data.aws_iam_policy_document.terraform_state_policy.json

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "terraform_state" {
  role       = aws_iam_role.terraform_state.name
  policy_arn = aws_iam_policy.terraform_state.arn
}

data "aws_iam_policy_document" "terraform_state_policy" {
  statement {
    effect = "Allow"
    actions = [
      "s3:ListBucket",
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
    ]
    resources = [
      "arn:aws:s3:::gula-terraform-state-${var.environment}",
      "arn:aws:s3:::gula-terraform-state-${var.environment}/*",
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:DeleteItem",
      "dynamodb:Query",
      "dynamodb:Scan",
    ]
    resources = ["arn:aws:dynamodb:*:*:table/gula-terraform-locks-${var.environment}"]
  }

  statement {
    effect = "Allow"
    actions = [
      "kms:Decrypt",
      "kms:GenerateDataKey",
      "kms:DescribeKey",
    ]
    resources = [aws_kms_key.general.arn]
  }
}

resource "aws_iam_role" "backup" {
  name               = "${var.name_prefix}-backup-role"
  assume_role_policy = data.aws_iam_policy_document.backup_assume.json

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-backup-role"
  })
}

data "aws_iam_policy_document" "backup_assume" {
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
  role       = aws_iam_role.backup.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup"
}

resource "aws_iam_role_policy_attachment" "backup_restore" {
  role       = aws_iam_role.backup.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForRestores"
}

# ── GuardDuty ───────────────────────────────────────────────────────────

resource "aws_guardduty_detector" "this" {
  count                      = var.enable_guardduty ? 1 : 0
  enable                     = true
  datasources {
    s3_logs {
      enable = true
    }
    kubernetes {
      audit_logs {
        enable = true
      }
    }
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-guardduty"
  })
}

# ── Security Hub ────────────────────────────────────────────────────────

resource "aws_securityhub_account" "this" {
  count                 = var.enable_security_hub ? 1 : 0
  enable_default_standards = var.security_hub_enable_default_standards

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-security-hub"
  })
}

# ── AWS Config ──────────────────────────────────────────────────────────

resource "aws_config_configuration_recorder" "this" {
  count    = var.enable_config ? 1 : 0
  name     = "${var.name_prefix}-config-recorder"
  role_arn = aws_iam_role.config[0].arn

  recording_group {
    all_supported                 = true
    include_global_resource_types = true
  }
}

resource "aws_config_delivery_channel" "this" {
  count          = var.enable_config && var.config_delivery_bucket != "" ? 1 : 0
  name           = "${var.name_prefix}-config-delivery"
  s3_bucket_name = var.config_delivery_bucket
  depends_on     = [aws_config_configuration_recorder.this]
}

resource "aws_iam_role" "config" {
  count = var.enable_config ? 1 : 0
  name  = "${var.name_prefix}-config-role"

  assume_role_policy = data.aws_iam_policy_document.config_assume[0].json

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-config-role"
  })
}

data "aws_iam_policy_document" "config_assume" {
  count = var.enable_config ? 1 : 0

  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["config.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "config" {
  count      = var.enable_config ? 1 : 0
  role       = aws_iam_role.config[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSConfigRole"
}

# ── CloudTrail ──────────────────────────────────────────────────────────

resource "aws_cloudtrail" "this" {
  count                         = var.enable_cloudtrail ? 1 : 0
  name                          = "${var.name_prefix}-trail"
  s3_bucket_name                = var.cloudtrail_bucket
  s3_key_prefix                 = "cloudtrail"
  include_global_service_events = true
  is_multi_region_trail         = true
  enable_log_file_validation    = true
  kms_key_id                    = aws_kms_key.cloudtrail.arn
  is_organization_trail         = false

  event_selector {
    read_write_type           = "All"
    include_management_events = true

    data_resource {
      type   = "AWS::S3::Object"
      values = ["arn:aws:s3"]
    }
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-trail"
  })
}

# ── Secrets Manager ─────────────────────────────────────────────────────

resource "aws_secretsmanager_secret" "general" {
  name                    = "${var.name_prefix}-secrets"
  description             = "General secrets for ${var.name_prefix} applications"
  kms_key_id              = aws_kms_key.general.arn
  recovery_window_in_days = 7

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-secrets"
  })
}

# ── WAF logging ─────────────────────────────────────────────────────────

resource "aws_wafv2_web_acl_logging_configuration" "this" {
  count         = var.enable_waf && var.waf_logging_bucket != "" ? 1 : 0
  log_destination_configs = ["arn:aws:s3:::${var.waf_logging_bucket}/AWSLogs/${data.aws_caller_identity.current.account_id}/WAFLogs/"]
  resource_arn  = aws_wafv2_web_acl.this[0].arn
}

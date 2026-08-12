locals {
  has_replication = var.replication_enabled && var.replication_region != ""
}

# ── Private Application Data Bucket ─────────────────────────────────────

resource "aws_s3_bucket" "private" {
  bucket        = "${var.name_prefix}-private"
  force_destroy = var.force_destroy

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-private"
  })
}

resource "aws_s3_bucket_versioning" "private" {
  bucket = aws_s3_bucket.private.id
  versioning_configuration {
    status = var.versioning_enabled ? "Enabled" : "Suspended"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "private" {
  bucket = aws_s3_bucket.private.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = var.kms_key_arn
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "private" {
  bucket                  = aws_s3_bucket.private.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "private" {
  bucket = aws_s3_bucket.private.id

  rule {
    id     = "expire-noncurrent"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = var.noncurrent_version_expiration_days
    }
  }

  rule {
    id     = "abort-incomplete-mpu"
    status = "Enabled"

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  dynamic "rule" {
    for_each = var.enable_lifecycle_transitions ? [1] : []
    content {
      id     = "transition-to-ia"
      status = "Enabled"

      transition {
        days          = var.ia_transition_days
        storage_class = "STANDARD_IA"
      }

      transition {
        days          = var.glacier_transition_days
        storage_class = "GLACIER"
      }
    }
  }
}

resource "aws_s3_bucket_policy" "private" {
  count  = var.enforce_ssl ? 1 : 0
  bucket = aws_s3_bucket.private.id
  policy = data.aws_iam_policy_document.private_bucket_policy[0].json
}

data "aws_iam_policy_document" "private_bucket_policy" {
  count = var.enforce_ssl ? 1 : 0

  statement {
    sid    = "EnforceTLSRequestsOnly"
    effect = "Deny"
    principals {
      type        = "AWS"
      identifiers = ["*"]
    }
    actions = ["s3:*"]
    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
    resources = [
      aws_s3_bucket.private.arn,
      "${aws_s3_bucket.private.arn}/*",
    ]
  }
}

# ── Public / Static Assets Bucket ───────────────────────────────────────

resource "aws_s3_bucket" "public" {
  bucket        = "${var.name_prefix}-public"
  force_destroy = var.force_destroy

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-public"
  })
}

resource "aws_s3_bucket_versioning" "public" {
  bucket = aws_s3_bucket.public.id
  versioning_configuration {
    status = var.versioning_enabled ? "Enabled" : "Suspended"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "public" {
  bucket = aws_s3_bucket.public.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = var.kms_key_arn
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "public" {
  bucket                  = aws_s3_bucket.public.id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "public" {
  count  = var.public_read_access ? 1 : 0
  bucket = aws_s3_bucket.public.id
  policy = data.aws_iam_policy_document.public_read_policy[0].json
}

data "aws_iam_policy_document" "public_read_policy" {
  count = var.public_read_access ? 1 : 0

  statement {
    sid    = "PublicReadGetObject"
    effect = "Allow"
    principals {
      type        = "*"
      identifiers = ["*"]
    }
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.public.arn}/*"]
  }

  statement {
    sid    = "EnforceTLSRequestsOnly"
    effect = "Deny"
    principals {
      type        = "AWS"
      identifiers = ["*"]
    }
    actions = ["s3:*"]
    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
    resources = [
      aws_s3_bucket.public.arn,
      "${aws_s3_bucket.public.arn}/*",
    ]
  }
}

# ── Logs Bucket ─────────────────────────────────────────────────────────

resource "aws_s3_bucket" "logs" {
  bucket        = "${var.name_prefix}-logs"
  force_destroy = var.force_destroy

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-logs"
  })
}

resource "aws_s3_bucket_versioning" "logs" {
  bucket = aws_s3_bucket.logs.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = var.kms_key_arn
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "logs" {
  bucket                  = aws_s3_bucket.logs.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id

  rule {
    id     = "expire-logs"
    status = "Enabled"

    expiration {
      days = var.log_expiration_days
    }
  }

  rule {
    id     = "abort-incomplete-mpu"
    status = "Enabled"

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

resource "aws_s3_bucket_policy" "logs" {
  count  = var.enable_log_delivery_policy ? 1 : 0
  bucket = aws_s3_bucket.logs.id
  policy = data.aws_iam_policy_document.log_delivery_policy[0].json
}

data "aws_iam_policy_document" "log_delivery_policy" {
  count = var.enable_log_delivery_policy ? 1 : 0

  statement {
    sid    = "ALBLogDelivery"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["delivery.logs.amazonaws.com"]
    }
    actions = [
      "s3:PutObject",
      "s3:GetBucketAcl",
    ]
    resources = [
      aws_s3_bucket.logs.arn,
      "${aws_s3_bucket.logs.arn}/*",
    ]
    condition {
      test     = "StringEquals"
      variable = "s3:x-amz-acl"
      values   = ["bucket-owner-full-control"]
    }
  }
}

# ── Backups Bucket ──────────────────────────────────────────────────────

resource "aws_s3_bucket" "backups" {
  bucket        = "${var.name_prefix}-backups"
  force_destroy = false

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-backups"
  })
}

resource "aws_s3_bucket_versioning" "backups" {
  bucket = aws_s3_bucket.backups.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = var.kms_key_arn
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "backups" {
  bucket                  = aws_s3_bucket.backups.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id

  rule {
    id     = "expire-old-backups"
    status = "Enabled"

    expiration {
      days = var.backup_expiration_days
    }
  }
}

resource "aws_s3_bucket_policy" "backups" {
  count  = var.enforce_ssl ? 1 : 0
  bucket = aws_s3_bucket.backups.id
  policy = data.aws_iam_policy_document.private_bucket_policy[0].json
}

# ── Cross-Region Replication ────────────────────────────────────────────

resource "aws_s3_bucket" "replica" {
  count    = local.has_replication ? 1 : 0
  provider = aws.dr
  bucket   = "${var.name_prefix}-replica-${var.replication_region}"
  force_destroy = false

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-replica-${var.replication_region}"
  })
}

resource "aws_s3_bucket_versioning" "replica" {
  count    = local.has_replication ? 1 : 0
  provider = aws.dr
  bucket   = aws_s3_bucket.replica[0].id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "replica" {
  count    = local.has_replication ? 1 : 0
  provider = aws.dr
  bucket   = aws_s3_bucket.replica[0].id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = var.kms_key_arn
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "replica" {
  count    = local.has_replication ? 1 : 0
  provider = aws.dr
  bucket   = aws_s3_bucket.replica[0].id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_iam_role" "replication" {
  count = local.has_replication ? 1 : 0
  name  = "${var.name_prefix}-s3-replication"

  assume_role_policy = data.aws_iam_policy_document.replication_assume[0].json

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-s3-replication-role"
  })
}

data "aws_iam_policy_document" "replication_assume" {
  count = local.has_replication ? 1 : 0

  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["s3.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "replication_policy" {
  count = local.has_replication ? 1 : 0

  statement {
    effect = "Allow"
    actions = [
      "s3:GetReplicationConfiguration",
      "s3:ListBucket",
    ]
    resources = [aws_s3_bucket.private.arn]
  }

  statement {
    effect = "Allow"
    actions = [
      "s3:GetObjectVersionForReplication",
      "s3:GetObjectVersionAcl",
      "s3:GetObjectVersionTagging",
    ]
    resources = ["${aws_s3_bucket.private.arn}/*"]
  }

  statement {
    effect = "Allow"
    actions = [
      "s3:ReplicateObject",
      "s3:ReplicateDelete",
      "s3:ReplicateTags",
    ]
    resources = ["${aws_s3_bucket.replica[0].arn}/*"]
  }
}

resource "aws_iam_policy" "replication" {
  count  = local.has_replication ? 1 : 0
  name   = "${var.name_prefix}-s3-replication-policy"
  policy = data.aws_iam_policy_document.replication_policy[0].json

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "replication" {
  count      = local.has_replication ? 1 : 0
  role       = aws_iam_role.replication[0].name
  policy_arn = aws_iam_policy.replication[0].arn
}

resource "aws_s3_bucket_replication_configuration" "private" {
  count   = local.has_replication ? 1 : 0
  bucket  = aws_s3_bucket.private.id
  role    = aws_iam_role.replication[0].arn

  rule {
    id     = "replicate-to-dr"
    status = "Enabled"

    filter {}

    destination {
      bucket        = aws_s3_bucket.replica[0].arn
      storage_class = "STANDARD_IA"
      replication_time {
        status  = "Enabled"
        time {
          minutes = 15
        }
      }
      metrics {
        status  = "Enabled"
        event_threshold {
          minutes = 15
        }
      }
    }

    delete_marker_replication {
      status = "Enabled"
    }

    source_selection_criteria {
      sse_kms_encrypted_objects {
        status = "Enabled"
      }
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.replication,
  ]
}

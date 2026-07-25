# GSF-005: Terraform Security Module

Audits Terraform configurations for security best practices.

## Components

- `TerraformSecurityManager` - Central security manager
  - State file security (encryption, locking, backend)
  - Provider version pinning validation
  - Sensitive output detection
  - Variable security (sensitive flag, validation)
  - Module source validation (pinned versions)
  - IAM permission audit (least privilege)
  - Security group rule audit (0.0.0.0/0 detection)
  - Resource tagging enforcement
  - Encryption-at-rest validation (S3, RDS, EBS, KMS)
  - Checkov integration abstraction

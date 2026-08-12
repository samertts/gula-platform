# =============================================================================
# GULA Platform - Vault PRODUCTION Configuration
# Auto-unseal via Transit (or replace with AWS KMS / GCP KMS)
# =============================================================================

ui = true

listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = 0
  tls_cert_file = "/vault/certs/vault.crt"
  tls_key_file  = "/vault/certs/vault.key"
}

# File storage (replace with Consul or Raft for HA)
storage "file" {
  path = "/vault/data"
}

# ===========================================================================
# Auto-Unseal via Transit (another Vault instance)
# Uncomment and configure for production to prevent sealed state after restart
# ===========================================================================
# seal "transit" {
#   address            = "https://vault-primary:8200"
#   token              = "TRANSIT_TOKEN"
#   disable_renewal    = "false"
#   key_name           = "gula-unseal-key"
#   mount_path         = "transit/"
# }

# ===========================================================================
# Auto-Unseal via AWS KMS (recommended for cloud deployments)
# ===========================================================================
# seal "awskms" {
#   region     = "me-south-1"
#   kms_key_id = "alias/gula-vault-unseal"
# }

api_addr     = "https://vault:8200"
cluster_addr = "https://vault:8201"

# Telemetry for Prometheus
telemetry {
  prometheus_retention_time = "30s"
  disable_hostname          = true
}

# Audit logging (compliance requirement)
# Enable after init: vault audit enable file file_path=/vault/logs/audit.log

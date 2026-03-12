# =============================================================================
# GULA Platform - HashiCorp Vault Configuration
# Executive Order 17: Secure secret management
# =============================================================================

ui = true

listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = 1
}

storage "file" {
  path = "/vault/data"
}

api_addr = "http://0.0.0.0:8200"
cluster_addr = "http://0.0.0.0:8201"

# Secret backends
# After initialization, store:
# - Database passwords at: secret/gula/database
# - RabbitMQ credentials at: secret/gula/rabbitmq
# - MinIO credentials at: secret/gula/minio
# - API tokens at: secret/gula/tokens
# - Keycloak credentials at: secret/gula/keycloak

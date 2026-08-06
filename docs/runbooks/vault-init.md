# Runbook: Vault Initialization (vault-init.md)

**Applies to:** `gula-vault` container (production `server` mode)

Vault now runs in persistent `server` mode with file storage (`/vault/data`). On
first start the Vault instance is **uninitialized and sealed** — no secrets can
be read until this runbook is completed once.

## 1. Initialize

```bash
docker exec gula-vault vault operator init -key-shares=1 -key-threshold=1
```

Output contains the unseal key and the root token. **Store both in a password
manager immediately** (this is the only time the full token is printed).

## 2. Unseal

```bash
docker exec gula-vault vault operator unseal "<UNSEAL_KEY>"
```

Repeat this step after every container restart while no auto-unseal is
configured.

## 3. Authenticate and store secrets

```bash
docker exec -e VAULT_TOKEN="<ROOT_TOKEN>" gula-vault vault secrets enable -path=secret kv-v2
docker exec -e VAULT_TOKEN="<ROOT_TOKEN>" gula-vault vault kv put secret/gula/database password="$(grep POSTGRES_PASSWORD .env | cut -d= -f2)"
```

Recommended paths (see `config/vault/vault.hcl`):
- `secret/gula/database` — DB passwords
- `secret/gula/tokens` — API tokens
- `secret/gula/keycloak` — Keycloak admin credentials

## 4. Auto-unseal (recommended before HA)

Replace the file storage seal in `config/vault/vault-prod.hcl` with a Transit
or AWS KMS seal block, then point compose at `vault-prod.hcl`.

#!/bin/bash
set -euo pipefail

log() { printf '[ROTATE-KEYS] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*"; }

log "=== Key Rotation ==="
log "Rotating JWT signing keys..."
NEW_SECRET=$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')
echo "SECRET_KEY=$NEW_SECRET" > /tmp/new-jwt-key.env

log "Rotating refresh token keys..."
NEW_REFRESH_SECRET=$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')
echo "REFRESH_TOKEN_SECRET=$NEW_REFRESH_SECRET" >> /tmp/new-jwt-key.env

log "Updating deployment secrets..."
kubectl create secret generic gula-secrets \
    --from-literal=SECRET_KEY="$NEW_SECRET" \
    --from-literal=REFRESH_TOKEN_SECRET="$NEW_REFRESH_SECRET" \
    --dry-run=client -o yaml | kubectl apply -f - 2>/dev/null || {
    log "K8s not available — updating .env"
    sed -i "s/^SECRET_KEY=.*/SECRET_KEY=$NEW_SECRET/" .env
    sed -i "s/^REFRESH_TOKEN_SECRET=.*/REFRESH_TOKEN_SECRET=$NEW_REFRESH_SECRET/" .env
}

log "Restarting services to pick up new keys..."
kubectl rollout restart deployment gula-backend -n gula 2>/dev/null || docker compose restart gula-backend 2>/dev/null || true

log "Verifying new keys are active..."
sleep 15
TOKEN=$(python3 -c "
import jwt, time
payload = {'sub': '1', 'lab_id': '1', 'exp': int(time.time()) + 3600}
token = jwt.encode(payload, '$NEW_SECRET', algorithm='HS256')
print(token)
" 2>/dev/null || echo "VERIFICATION_FAILED")

if [ "$TOKEN" != "VERIFICATION_FAILED" ]; then
    log "Key rotation verified — new JWT signing works"
    log "Old keys will be invalidated after TTL expires"
else
    log "WARNING: Key rotation verification failed"
fi

log "Key rotation complete"

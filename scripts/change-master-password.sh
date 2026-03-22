#!/bin/bash
# =============================================================================
# GULA — Change Master Admin Password
# Run inside the server:
#   bash scripts/change-master-password.sh
# =============================================================================
set -euo pipefail

NEW_PASSWORD="${1:-}"
if [[ -z "$NEW_PASSWORD" ]]; then
    echo "Usage: bash scripts/change-master-password.sh 'NewStrongPassword!'"
    echo ""
    echo "Password requirements:"
    echo "  - At least 12 characters"
    echo "  - Mix of letters, numbers, symbols"
    exit 1
fi

if [[ ${#NEW_PASSWORD} -lt 12 ]]; then
    echo "ERROR: Password must be at least 12 characters"
    exit 1
fi

echo "[1/3] Hashing new password..."
NEW_HASH=$(docker exec gula-backend python3 -c "
from passlib.context import CryptContext
ctx = CryptContext(schemes=['bcrypt'], deprecated='auto')
print(ctx.hash('${NEW_PASSWORD}'))
")

echo "[2/3] Updating password in database..."
docker exec gula-postgres psql -U postgres -d labdb -c "
UPDATE lab_users
SET password_hash = '${NEW_HASH}',
    perm_version = COALESCE(perm_version, 1) + 1
WHERE role = 'master_admin'
RETURNING id, email, role;
"

echo "[3/3] Removing plaintext password from .env..."
cd "$(dirname "$0")/.."
if grep -q "GULA_ADMIN_PASSWORD=" .env; then
    sed -i '/^GULA_ADMIN_PASSWORD=/d' .env
    echo "  Removed GULA_ADMIN_PASSWORD from .env"
fi

echo ""
echo "============================================"
echo " Password changed successfully."
echo " All existing sessions have been invalidated."
echo " New password: [hidden — you set it above]"
echo "============================================"

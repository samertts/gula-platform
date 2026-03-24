#!/bin/bash
# =============================================================================
# GULA — Change Master Admin Password
# Run inside the server:
#   bash scripts/change-master-password.sh
# Password is read from stdin (not CLI arg) to avoid exposure in process list.
# =============================================================================
set -euo pipefail

# Read password securely from stdin (not visible in `ps aux` or shell history)
if [ -t 0 ]; then
    read -r -s -p "New master admin password: " NEW_PASSWORD
    echo
    read -r -s -p "Confirm password: " NEW_PASSWORD_CONFIRM
    echo
    if [[ "$NEW_PASSWORD" != "$NEW_PASSWORD_CONFIRM" ]]; then
        echo "ERROR: Passwords do not match"
        exit 1
    fi
else
    # Non-interactive (piped): read single line from stdin
    read -r NEW_PASSWORD
fi

if [[ -z "$NEW_PASSWORD" ]]; then
    echo "Usage: bash scripts/change-master-password.sh"
    echo "       (password will be prompted securely)"
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
# Pass password via environment variable to avoid CLI arg visibility
NEW_HASH=$(docker exec -e GULA_NEW_PASSWORD="$NEW_PASSWORD" gula-backend python3 -c "
import os
from passlib.context import CryptContext
ctx = CryptContext(schemes=['bcrypt'], deprecated='auto')
print(ctx.hash(os.environ['GULA_NEW_PASSWORD']))
")

echo "[2/3] Updating password in database..."
# Use parameterized query via psql --variable to prevent SQL injection
docker exec gula-postgres psql -U postgres -d labdb \
    -v "new_hash=$NEW_HASH" \
    -c "UPDATE lab_users
        SET password_hash = :'new_hash',
            perm_version = COALESCE(perm_version, 1) + 1
        WHERE role = 'master_admin'
        RETURNING id, email, role;"

echo "[3/3] Removing plaintext password from .env..."
cd "$(dirname "$0")/.."
if grep -q "GULA_ADMIN_PASSWORD=" .env 2>/dev/null; then
    sed -i '/^GULA_ADMIN_PASSWORD=/d' .env
    echo "  Removed GULA_ADMIN_PASSWORD from .env"
fi

echo ""
echo "============================================"
echo " Password changed successfully."
echo " All existing sessions have been invalidated."
echo "============================================"

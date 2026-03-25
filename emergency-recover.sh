#!/usr/bin/env bash
# =============================================================================
# GULA PLATFORM — Emergency Recovery Script
# =============================================================================
# USE THIS when the server is stuck in a broken state:
#   - Merge conflict markers in docker-compose.yml / nginx configs
#   - YAML validation failures ("could not find expected ':'")
#   - Site unreachable (ERR_CONNECTION_REFUSED)
#   - Failed git rebase/merge that won't resolve
#
# USAGE:
#   chmod +x emergency-recover.sh
#   ./emergency-recover.sh
#
# WHAT IT DOES:
#   1. Aborts any pending merge/rebase
#   2. Switches to the canonical production branch
#   3. Hard-resets to the remote (discards ALL local changes)
#   4. Verifies no conflict markers remain
#   5. Re-installs system nginx config
#   6. Starts Docker stack
# =============================================================================
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

RED='\033[0;31m'; YEL='\033[1;33m'; GRN='\033[0;32m'; CYN='\033[0;36m'; NC='\033[0m'
log()  { printf "${CYN}[recover]${NC} %s\n" "$*"; }
ok()   { printf "${GRN}[recover] ✓ %s${NC}\n" "$*"; }
warn() { printf "${YEL}[recover] ⚠ %s${NC}\n" "$*"; }
err()  { printf "${RED}[recover] ✗ %s${NC}\n" "$*" >&2; }
die()  { err "$*"; exit 1; }

# ─── Target branch ────────────────────────────────────────────────────────────
TARGET_BRANCH="claude/fix-bugs-vulnerabilities-Y6mGU"
TARGET_REMOTE="origin/${TARGET_BRANCH}"

echo ""
echo "========================================================"
echo "  GULA PLATFORM — Emergency Recovery"
echo "========================================================"
echo "  Target branch : ${TARGET_BRANCH}"
echo "  Directory     : $(pwd)"
echo "========================================================"
echo ""

# ─── Step 1: Abort any pending git operations ─────────────────────────────────
log "Aborting any pending merge / rebase / cherry-pick..."
git merge --abort 2>/dev/null      && warn "Aborted pending merge"   || true
git rebase --abort 2>/dev/null     && warn "Aborted pending rebase"  || true
git cherry-pick --abort 2>/dev/null && warn "Aborted cherry-pick"    || true
ok "Git state cleared"

# ─── Step 2: Fetch latest from remote ─────────────────────────────────────────
log "Fetching latest from remote..."
FETCH_ATTEMPTS=0
while ! git fetch origin 2>&1; do
  FETCH_ATTEMPTS=$((FETCH_ATTEMPTS+1))
  [ "$FETCH_ATTEMPTS" -ge 4 ] && die "git fetch failed after 4 attempts — check network"
  warn "Fetch failed, retrying in ${FETCH_ATTEMPTS}s..."
  sleep "$FETCH_ATTEMPTS"
done
ok "Fetch complete"

# Verify target branch exists on remote
if ! git ls-remote --exit-code origin "${TARGET_BRANCH}" >/dev/null 2>&1; then
  die "Remote branch '${TARGET_REMOTE}' does not exist — check branch name"
fi

# ─── Step 3: Switch to target branch ──────────────────────────────────────────
log "Switching to ${TARGET_BRANCH}..."
git checkout -B "${TARGET_BRANCH}" "${TARGET_REMOTE}"
ok "Now on ${TARGET_BRANCH}"

# ─── Step 4: Hard reset to remote (discard ALL local changes) ─────────────────
log "Hard-resetting to ${TARGET_REMOTE}..."
git reset --hard "${TARGET_REMOTE}"
ok "Reset complete — HEAD is now at $(git rev-parse --short HEAD) $(git log -1 --format='%s')"

# ─── Step 5: Remove untracked files (leftover conflict artifacts) ─────────────
log "Cleaning untracked files..."
git clean -fd
ok "Working tree clean"

# ─── Step 6: Verify no merge conflict markers remain ──────────────────────────
log "Checking for merge conflict markers..."
CONFLICT_FILES=()
while IFS= read -r file; do
  if grep -qE "^(<{7}|={7}|>{7}) " "$file" 2>/dev/null; then
    CONFLICT_FILES+=("$file")
  fi
done < <(git ls-files)

if [ "${#CONFLICT_FILES[@]}" -gt 0 ]; then
  err "Conflict markers found in the following files (should not happen after reset):"
  for f in "${CONFLICT_FILES[@]}"; do
    err "  $f"
    grep -nE "^(<{7}|={7}|>{7}) " "$f" | head -3 | while read -r line; do
      err "    $line"
    done
  done
  die "Cannot proceed — repository state is corrupt. Contact the repo owner."
fi
ok "No conflict markers found"

# ─── Step 7: Validate docker-compose.yml YAML ─────────────────────────────────
log "Validating docker-compose.yml..."
if command -v python3 >/dev/null 2>&1; then
  python3 -c "
import yaml, sys
try:
    yaml.safe_load(open('docker-compose.yml'))
    print('  YAML: OK')
except yaml.YAMLError as e:
    print(f'  YAML ERROR: {e}', file=sys.stderr)
    sys.exit(1)
" || die "docker-compose.yml YAML is invalid — repository may be corrupt"
else
  warn "python3 not found — skipping YAML pre-validation"
fi
ok "docker-compose.yml is valid YAML"

# ─── Step 8: Re-install system nginx config ────────────────────────────────────
if command -v nginx >/dev/null 2>&1; then
  log "Re-installing system nginx config..."
  # Use HTTPS config if certificates exist, otherwise HTTP config
  if [ -f "/etc/letsencrypt/live/gula-platform.org/fullchain.pem" ]; then
    NGINX_CONF="config/nginx/system/gula-platform.conf"
    log "  SSL certificates found — using HTTPS config"
  else
    NGINX_CONF="config/nginx/system/gula-platform-http.conf"
    log "  No SSL certificates — using HTTP-only config"
  fi

  if [ -f "$NGINX_CONF" ]; then
    sudo cp "$NGINX_CONF" /etc/nginx/sites-available/gula-platform
    sudo ln -sf /etc/nginx/sites-available/gula-platform \
                /etc/nginx/sites-enabled/gula-platform 2>/dev/null || true
    sudo rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true

    if sudo nginx -t 2>&1; then
      sudo systemctl reload nginx 2>/dev/null || sudo systemctl restart nginx 2>/dev/null || true
      ok "System nginx reloaded"
    else
      warn "nginx -t still failing — check /etc/nginx/sites-enabled/ for other conflicting configs"
      warn "Running: sudo nginx -T 2>&1 | grep -A3 'nginx: \\[error\\]'"
      sudo nginx -T 2>&1 | grep -A3 'nginx: \[error\]' || true
    fi
  else
    warn "Nginx config file not found: $NGINX_CONF"
  fi
else
  warn "nginx not installed on system — skipping nginx config"
fi

# ─── Step 9: Run the main deploy ──────────────────────────────────────────────
echo ""
log "Starting Docker stack via deploy.sh..."
if [ -x ./deploy.sh ]; then
  ./deploy.sh
else
  warn "deploy.sh not executable — trying: bash deploy.sh"
  bash deploy.sh
fi

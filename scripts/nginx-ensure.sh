#!/usr/bin/env bash
# =============================================================================
# GULA Platform — Nginx Smart Config Switcher + Restart Guard
#
# ROOT CAUSE FIX: nginx fails to start when SSL certs don't exist yet,
# and systemd marks it as "failed" — stopping all retry attempts.
# This script picks the right config before nginx starts and ensures
# nginx is ALWAYS running (HTTP-only until certs arrive, HTTPS after).
#
# Called by:
#   - systemd override (Before=nginx.service) on every boot
#   - auto_heal.sh every 5 minutes
#   - deploy.sh after every deployment
#
# Usage: sudo bash scripts/nginx-ensure.sh
# =============================================================================
set -euo pipefail

REPO_DIR="${GULA_DIR:-/home/samertts/gula-platform}"
SITES_AVAIL="/etc/nginx/sites-available/gula-platform"
SITES_ENABLED="/etc/nginx/sites-enabled/gula-platform"
CERT_PATH="/etc/letsencrypt/live/gula-platform.org/fullchain.pem"
HTTPS_CONF="${REPO_DIR}/config/nginx/system/gula-platform.conf"
HTTP_CONF="${REPO_DIR}/config/nginx/system/gula-platform-http.conf"
LOG="/var/log/gula-nginx-ensure.log"

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') [nginx-ensure] $*" | tee -a "$LOG"; }

# ─── Pick the right config ───────────────────────────────────────────────────
if [ -f "$CERT_PATH" ]; then
    ACTIVE_CONF="$HTTPS_CONF"
    MODE="HTTPS"
else
    ACTIVE_CONF="$HTTP_CONF"
    MODE="HTTP-only (no SSL cert yet)"
fi

# ─── Install config if changed ───────────────────────────────────────────────
if ! cmp -s "$ACTIVE_CONF" "$SITES_AVAIL" 2>/dev/null; then
    log "Installing $MODE config..."
    cp "$ACTIVE_CONF" "$SITES_AVAIL"
fi

ln -sf "$SITES_AVAIL" "$SITES_ENABLED"
rm -f /etc/nginx/sites-enabled/default

# ─── Test nginx config ───────────────────────────────────────────────────────
if ! nginx -t 2>>"$LOG"; then
    log "ERROR: nginx config test failed — falling back to HTTP-only"
    cp "$HTTP_CONF" "$SITES_AVAIL"
    if ! nginx -t 2>>"$LOG"; then
        log "CRITICAL: Even HTTP config fails — check nginx installation"
        exit 1
    fi
    MODE="HTTP-only (fallback after config error)"
fi

# ─── Ensure nginx is running ─────────────────────────────────────────────────
if systemctl is-active --quiet nginx; then
    # Running — reload config only if it changed
    systemctl reload nginx
    log "OK: nginx reloaded ($MODE)"
else
    # Not running — reset failed state and start
    systemctl reset-failed nginx 2>/dev/null || true
    systemctl start nginx
    log "OK: nginx started ($MODE)"
fi

# ─── Verify port 80 is actually listening ────────────────────────────────────
sleep 1
if ! ss -tlnp | grep -q ':80 '; then
    log "ERROR: Port 80 not listening after nginx start — forcing restart"
    systemctl restart nginx
    sleep 2
    if ! ss -tlnp | grep -q ':80 '; then
        log "CRITICAL: nginx refuses to bind port 80"
        exit 1
    fi
fi

log "PASS: nginx listening on port 80 ($MODE)"

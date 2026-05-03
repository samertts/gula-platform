#!/usr/bin/env bash
# =============================================================================
# GULA Platform — DigitalOcean Droplet Diagnostic
# =============================================================================
#
# Read-only diagnostic snapshot of a GULA Droplet. Safe to run on any state —
# it never modifies, restarts, or repairs anything; it only reports.
#
# Usage (on the Droplet, as the deploy user — typically `samertts`):
#
#   chmod +x scripts/diagnose-droplet.sh
#   ./scripts/diagnose-droplet.sh                 # print to stdout + log file
#   ./scripts/diagnose-droplet.sh --domain X      # also probe https://X
#   ./scripts/diagnose-droplet.sh --quiet         # log file only, no stdout
#
# Output is also written to /tmp/gula-diagnose-<timestamp>.log so it can be
# pasted back to Claude for analysis.
#
# Secrets are NEVER printed. Only their presence + length is reported.
# =============================================================================

# Intentionally not using `set -e` — we want every check to run even if
# earlier ones fail. Failures are individually reported.
set -u
set -o pipefail

# ── Args ────────────────────────────────────────────────────────────────────
DOMAIN=""
QUIET=0
while [ $# -gt 0 ]; do
    case "$1" in
        --domain) DOMAIN="${2:-}"; shift 2 ;;
        --quiet)  QUIET=1; shift ;;
        -h|--help)
            sed -n '2,20p' "$0"; exit 0 ;;
        *) echo "Unknown arg: $1" >&2; exit 2 ;;
    esac
done

# ── Output capture ──────────────────────────────────────────────────────────
TS="$(date -u +%Y%m%dT%H%M%SZ)"
LOG="/tmp/gula-diagnose-${TS}.log"
: >"$LOG"

# tee to stdout + log, or log only
if [ "$QUIET" -eq 1 ]; then
    exec 3>"$LOG"
    say() { printf "%s\n" "$*" >&3; }
else
    exec 3> >(tee -a "$LOG")
    say() { printf "%s\n" "$*" >&3; }
fi

run() {
    # Run a command and capture its output + exit code into the log.
    # Never aborts on failure.
    local desc="$1"; shift
    say ""
    say "$ $*"
    if out=$("$@" 2>&1); then
        printf "%s\n" "$out" >&3
    else
        rc=$?
        printf "%s\n" "$out" >&3
        say "[exit=$rc] $desc"
    fi
}

run_sh() {
    # Run a shell snippet (so we can use pipes/redirects).
    local desc="$1"; shift
    local snippet="$1"; shift || true
    say ""
    say "$ $snippet"
    if out=$(bash -c "$snippet" 2>&1); then
        printf "%s\n" "$out" >&3
    else
        rc=$?
        printf "%s\n" "$out" >&3
        say "[exit=$rc] $desc"
    fi
}

section() {
    say ""
    say "═════════════════════════════════════════════════════════════════════"
    say "  $*"
    say "═════════════════════════════════════════════════════════════════════"
}

sub() {
    say ""
    say "─── $* ───"
}

# ── Resolve project directory ───────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR" 2>/dev/null || true

# Detect docker compose flavour
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    DC="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    DC="docker-compose"
else
    DC=""
fi

# =============================================================================
section "GULA Droplet Diagnostic — ${TS}"
# =============================================================================
say "Project dir : $PROJECT_DIR"
say "Log file    : $LOG"
say "Domain arg  : ${DOMAIN:-<none>}"
say "Compose CLI : ${DC:-<not found>}"
say "Whoami      : $(id)"

# =============================================================================
section "1. System"
# =============================================================================
sub "OS / kernel"
run_sh "lsb_release" "lsb_release -a 2>/dev/null || cat /etc/os-release"
run "uname"   uname -a
run "uptime"  uptime
run "date"    date -u

sub "Resources"
run_sh "free"     "free -h"
run_sh "df"       "df -h | head -20"
run_sh "load"     "cat /proc/loadavg"
run_sh "cpus"     "nproc; lscpu | grep -E 'Model name|CPU\\(s\\)' | head -5"
run_sh "memlimit" "cat /proc/meminfo | head -5"

sub "Top processes (by memory)"
run_sh "top-mem" "ps auxf --sort=-%mem | head -15"

# =============================================================================
section "2. Network & DNS"
# =============================================================================
sub "Listening sockets"
run_sh "ss" "ss -tulpn 2>/dev/null | grep -E ':(22|80|443|8000|8080|5432|6379|9090|3000)\\s' || ss -tulpn 2>/dev/null | head -30"

sub "Public IP"
run_sh "publicip" "curl -fsS --max-time 5 https://ifconfig.me 2>/dev/null || echo '(could not fetch)'"

sub "DNS resolution"
if [ -n "$DOMAIN" ]; then
    run_sh "dig-A"   "dig +short A    $DOMAIN @1.1.1.1 2>/dev/null || nslookup $DOMAIN 2>/dev/null | tail -5"
    run_sh "dig-AAAA" "dig +short AAAA $DOMAIN @1.1.1.1 2>/dev/null || true"
else
    say "(skipped — pass --domain <name> to probe DNS)"
fi

# =============================================================================
section "3. Docker"
# =============================================================================
if ! command -v docker >/dev/null 2>&1; then
    say "[!] Docker NOT installed"
else
    run "docker-version"  docker --version
    run_sh "compose-version" "$DC version 2>&1 || true"
    run_sh "docker-info"  "docker info 2>&1 | grep -E 'Server Version|Storage Driver|Cgroup|Operating System|Kernel|Total Memory|CPUs' | head -15"

    sub "All containers (running + stopped)"
    run_sh "docker-ps" "docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' 2>&1"

    sub "Resource usage (snapshot)"
    run_sh "docker-stats" "docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}' 2>&1 | head -20"

    sub "Disk usage by Docker"
    run_sh "docker-df" "docker system df 2>&1"
fi

# =============================================================================
section "4. Compose stack (project: $PROJECT_DIR)"
# =============================================================================
if [ -z "$DC" ]; then
    say "[!] No compose CLI available — skipping"
elif [ ! -f "$PROJECT_DIR/docker-compose.yml" ]; then
    say "[!] $PROJECT_DIR/docker-compose.yml not found"
else
    run_sh "compose-ps" "$DC ps 2>&1"

    sub "Service health summary"
    run_sh "compose-health" "$DC ps --format json 2>/dev/null | python3 -c '
import json, sys
for line in sys.stdin:
    line = line.strip()
    if not line: continue
    try:
        d = json.loads(line)
        print(f\"{d.get(\"Service\",\"?\"):20s} state={d.get(\"State\",\"?\"):12s} health={d.get(\"Health\",\"-\")}\")
    except Exception:
        pass
' 2>/dev/null || $DC ps 2>&1 | head -30"

    sub "Recent logs per service (tail 50)"
    for svc in postgres redis gula-backend gula-worker frontend api-gateway; do
        say ""
        say "── logs: $svc ──"
        run_sh "logs-$svc" "$DC logs --tail=50 --no-color $svc 2>&1 || true"
    done
fi

# =============================================================================
section "5. Backend health endpoints"
# =============================================================================
# These bypass middlewares (whitelisted in app/main.py) and reveal WHY
# startup failed if it did.
for path in /health /health/live /health/ready /health/status /health/deep; do
    sub "GET http://127.0.0.1:8080${path}"
    run_sh "curl-$path" "curl -fsS --max-time 5 -i http://127.0.0.1:8080${path} 2>&1 | head -40 || true"
done

# Direct backend (bypass api-gateway) — useful when gateway is down
sub "GET http://127.0.0.1:8000/health (direct, bypassing gateway)"
run_sh "curl-direct" "curl -fsS --max-time 5 -i http://127.0.0.1:8000/health 2>&1 | head -20 || true"

# =============================================================================
section "6. Database & Redis"
# =============================================================================
if [ -n "$DC" ]; then
    sub "Postgres"
    run_sh "pg-ready"   "$DC exec -T postgres pg_isready 2>&1 || true"
    run_sh "pg-version" "$DC exec -T postgres psql -U postgres -c 'SELECT version();' 2>&1 | head -5 || true"
    run_sh "pg-conns"   "$DC exec -T postgres psql -U postgres -c 'SELECT count(*) AS active FROM pg_stat_activity;' 2>&1 || true"
    run_sh "pg-dbsize"  "$DC exec -T postgres psql -U postgres -c \"SELECT pg_size_pretty(pg_database_size(current_database()));\" 2>&1 || true"

    sub "Alembic migration head"
    run_sh "alembic-current" "$DC exec -T gula-backend alembic current 2>&1 || true"
    run_sh "alembic-heads"   "$DC exec -T gula-backend alembic heads 2>&1 || true"

    sub "Redis"
    run_sh "redis-ping" "$DC exec -T redis redis-cli ping 2>&1 || true"
    run_sh "redis-info" "$DC exec -T redis redis-cli INFO server 2>&1 | head -10 || true"
fi

# =============================================================================
section "7. .env file (presence + key audit, NO values printed)"
# =============================================================================
ENV_FILE="$PROJECT_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    say "[!] $ENV_FILE NOT FOUND"
else
    say "$ENV_FILE found ($(wc -l <"$ENV_FILE") lines, $(stat -c%a "$ENV_FILE" 2>/dev/null || stat -f%Lp "$ENV_FILE") perms)"

    sub "Required keys (set/unset only — values masked)"
    REQUIRED=(
        SECRET_KEY ENCRYPTION_KEY NID_HMAC_KEY DEVICE_HMAC_KEY REFRESH_TOKEN_SECRET
        DATABASE_URL POSTGRES_PASSWORD REDIS_PASSWORD
        GULA_ADMIN_EMAIL GULA_ADMIN_PASSWORD
        BASE_URL CORS_ORIGINS ENV
    )
    for key in "${REQUIRED[@]}"; do
        line=$(grep -E "^${key}=" "$ENV_FILE" 2>/dev/null | head -1)
        if [ -z "$line" ]; then
            say "  $key : MISSING"
        else
            val="${line#*=}"
            len=${#val}
            # detect obvious weak/default placeholders WITHOUT printing the value
            weak=""
            case "$val" in
                ""|"changeme"|"change_me"|"password"|"secret"|"placeholder"|"your_"*|"<"*">")
                    weak=" WEAK_OR_PLACEHOLDER" ;;
            esac
            say "  $key : set (len=$len)$weak"
        fi
    done

    sub "Total non-empty, non-comment lines"
    run_sh "env-count" "grep -cE '^[A-Z_]+=' '$ENV_FILE' 2>&1 || true"
fi

# =============================================================================
section "8. nginx (system-level reverse proxy)"
# =============================================================================
if ! command -v nginx >/dev/null 2>&1; then
    say "[!] system nginx NOT installed (might be OK if api-gateway handles TLS)"
else
    run "nginx-version" nginx -v
    run_sh "nginx-test"   "nginx -t 2>&1"
    run_sh "nginx-status" "systemctl is-active nginx 2>&1; systemctl is-enabled nginx 2>&1"
    run_sh "nginx-sites"  "ls -la /etc/nginx/sites-enabled/ 2>&1"
fi

# =============================================================================
section "9. SSL / TLS"
# =============================================================================
if [ -d /etc/letsencrypt/live ]; then
    sub "Let's Encrypt certificates"
    run_sh "le-list" "ls /etc/letsencrypt/live/ 2>&1"
    for d in /etc/letsencrypt/live/*/; do
        [ -d "$d" ] || continue
        name=$(basename "$d")
        say ""
        say "── cert: $name ──"
        run_sh "le-dates-$name" "sudo openssl x509 -in '$d/fullchain.pem' -noout -dates -subject -issuer 2>&1 || openssl x509 -in '$d/fullchain.pem' -noout -dates -subject -issuer 2>&1 || true"
    done
    run_sh "certbot-timer" "systemctl list-timers 2>/dev/null | grep -i certbot || echo '(no certbot timer)'"
else
    say "[!] /etc/letsencrypt/live not present — no Let's Encrypt certs installed"
fi

if [ -n "$DOMAIN" ]; then
    sub "External HTTPS probe to $DOMAIN"
    run_sh "https-headers" "curl -fsS --max-time 8 -I https://$DOMAIN/health 2>&1 | head -20 || true"
    run_sh "https-cert"    "echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | openssl x509 -noout -dates -subject 2>&1 || true"
fi

# =============================================================================
section "10. Firewall & SSH hardening"
# =============================================================================
run_sh "ufw" "sudo ufw status verbose 2>&1 || ufw status verbose 2>&1 || echo '(ufw not installed or no sudo)'"
run_sh "iptables" "sudo iptables -L -n --line-numbers 2>&1 | head -40 || echo '(no sudo)'"

sub "SSH config (key lines only)"
run_sh "sshd" "grep -E '^(Port|PermitRootLogin|PasswordAuthentication|PubkeyAuthentication|PermitEmptyPasswords|MaxAuthTries|X11Forwarding)\\s' /etc/ssh/sshd_config 2>&1 || sudo grep -E '^(Port|PermitRootLogin|PasswordAuthentication|PubkeyAuthentication|PermitEmptyPasswords|MaxAuthTries)\\s' /etc/ssh/sshd_config 2>&1 || true"

sub "Fail2ban"
run_sh "fail2ban" "systemctl is-active fail2ban 2>&1 || echo '(not installed)'"
run_sh "fail2ban-jails" "sudo fail2ban-client status 2>&1 || true"

sub "Unattended upgrades"
run_sh "unattended" "systemctl is-active unattended-upgrades 2>&1 || echo '(not installed)'"

# =============================================================================
section "11. systemd services"
# =============================================================================
for svc in docker gula nginx fail2ban unattended-upgrades; do
    sub "service: $svc"
    run_sh "sysctl-$svc" "systemctl status $svc --no-pager 2>&1 | head -15 || echo '(no such service)'"
done

# =============================================================================
section "12. Recent journal errors (last 30 minutes)"
# =============================================================================
run_sh "journal-docker" "journalctl -u docker --since '30 minutes ago' --no-pager 2>&1 | tail -30 || true"
run_sh "journal-gula"   "journalctl -u gula  --since '30 minutes ago' --no-pager 2>&1 | tail -30 || true"
run_sh "journal-priority" "journalctl --since '30 minutes ago' -p err --no-pager 2>&1 | tail -30 || true"

# =============================================================================
section "13. Disk hot-spots"
# =============================================================================
run_sh "du-var" "sudo du -sh /var/lib/docker /var/log /home /opt 2>&1 || du -sh /var/lib/docker /var/log /home /opt 2>&1 || true"
run_sh "largelogs" "sudo find /var/log -type f -size +100M 2>/dev/null | head -10 || true"

# =============================================================================
section "Diagnostic complete"
# =============================================================================
say ""
say "Log written to: $LOG"
say ""
say "Next steps:"
say "  1. Inspect the log:    less $LOG"
say "  2. Share with Claude:  cat $LOG | head -500   (paste output)"
say "  3. Or upload:          scp <user>@<host>:$LOG ./"
say ""

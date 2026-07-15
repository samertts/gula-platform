#!/bin/bash
# =============================================================================
# GULA Platform — Comprehensive Health Probe
# =============================================================================
# Probes every service in the stack, measures latency, reports status.
# Outputs JSON for monitoring integration (Prometheus, Grafana, webhooks).
#
# Usage:
#   ./scripts/health-probes/check-all.sh
#   ./scripts/health-probes/check-all.sh --json     # JSON output only
#   ./scripts/health-probes/check-all.sh --summary   # Summary line only
#   HEALTH_TIMEOUT=5 ./scripts/health-probes/check-all.sh
#
# Exit codes:
#   0 — All services UP
#   1 — One or more services DEGRADED (writable, but impaired)
#   2 — One or more services DOWN (critical)
# =============================================================================

set -euo pipefail

# ── Configuration ────────────────────────────────────────────────────────────
HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-5}"
BACKEND_URL="${BACKEND_URL:-http://gula-backend:8000}"
POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
REDIS_HOST="${REDIS_HOST:-redis}"
REDIS_PORT="${REDIS_PORT:-6379}"
RABBITMQ_HOST="${RABBITMQ_HOST:-rabbitmq-lb}"
RABBITMQ_PORT="${RABBITMQ_PORT:-15672}"
MINIO_HOST="${MINIO_HOST:-minio-lb}"
MINIO_PORT="${MINIO_PORT:-9000}"
PATRONI_HOST="${PATRONI_HOST:-patroni:8008}"

REDIS_PASSWORD="${REDIS_PASSWORD:-}"
RABBITMQ_USER="${RABBITMQ_USER:-gula}"
RABBITMQ_PASS="${RABBITMQ_PASS:-}"
MINIO_ACCESS_KEY="${MINIO_ACCESS_KEY:-}"
MINIO_SECRET_KEY="${MINIO_SECRET_KEY:-}"

# ── Globals ──────────────────────────────────────────────────────────────────
OVERALL_STATUS="UP"
UP_COUNT=0
DOWN_COUNT=0
DEGRADED_COUNT=0
declare -A RESULTS
declare -A LATENCIES

# ── Timestamp helper ─────────────────────────────────────────────────────────
now_ms() {
    python3 -c "import time; print(int(time.time() * 1000))"
}

# ── Probing Functions ────────────────────────────────────────────────────────

probe_http() {
    local name="$1"
    local url="$2"
    local expected_code="${3:-200}"
    local start end status latency

    start=$(now_ms)
    local code
    code=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$HEALTH_TIMEOUT" "$url" 2>/dev/null || echo "000")
    end=$(now_ms)
    latency=$(( end - start ))

    if [[ "$code" == "$expected_code" ]]; then
        RESULTS["$name"]="UP"
        LATENCIES["$name"]="$latency"
        UP_COUNT=$(( UP_COUNT + 1 ))
    elif [[ "$code" == "000" ]]; then
        RESULTS["$name"]="DOWN"
        LATENCIES["$name"]="0"
        DOWN_COUNT=$(( DOWN_COUNT + 1 ))
    else
        RESULTS["$name"]="DEGRADED"
        LATENCIES["$name"]="$latency"
        DEGRADED_COUNT=$(( DEGRADED_COUNT + 1 ))
    fi
}

probe_tcp() {
    local name="$1"
    local host="$2"
    local port="$3"
    local start end latency

    start=$(now_ms)
    if timeout "$HEALTH_TIMEOUT" bash -c "echo > /dev/tcp/${host}/${port}" 2>/dev/null; then
        end=$(now_ms)
        latency=$(( end - start ))
        RESULTS["$name"]="UP"
        LATENCIES["$name"]="$latency"
        UP_COUNT=$(( UP_COUNT + 1 ))
    else
        RESULTS["$name"]="DOWN"
        LATENCIES["$name"]="0"
        DOWN_COUNT=$(( DOWN_COUNT + 1 ))
    fi
}

probe_pg() {
    local name="postgres"
    local start end latency

    start=$(now_ms)
    if command -v pg_isready &>/dev/null; then
        local result
        result=$(PGPASSWORD="${PGPASSWORD:-}" pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U postgres -q 2>&1) || true
        end=$(now_ms)
        latency=$(( end - start ))

        if [[ "$result" == *"accepting connections"* ]] || [[ "$result" == *"ready"* ]]; then
            RESULTS["$name"]="UP"
            LATENCIES["$name"]="$latency"
            UP_COUNT=$(( UP_COUNT + 1 ))
        elif [[ -z "$result" ]]; then
            RESULTS["$name"]="DOWN"
            LATENCIES["$name"]="0"
            DOWN_COUNT=$(( DOWN_COUNT + 1 ))
        else
            RESULTS["$name"]="DEGRADED"
            LATENCIES["$name"]="$latency"
            DEGRADED_COUNT=$(( DEGRADED_COUNT + 1 ))
        fi
    else
        probe_tcp "$name" "$POSTGRES_HOST" "$POSTGRES_PORT"
    fi
}

probe_redis() {
    local name="redis"
    local start end latency

    start=$(now_ms)
    if command -v redis-cli &>/dev/null; then
        local result
        result=$(timeout "$HEALTH_TIMEOUT" redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "${REDIS_PASSWORD}" ping 2>/dev/null) || result=""
        end=$(now_ms)
        latency=$(( end - start ))

        if [[ "$result" == "PONG" ]]; then
            RESULTS["$name"]="UP"
            LATENCIES["$name"]="$latency"
            UP_COUNT=$(( UP_COUNT + 1 ))
        elif [[ -z "$result" ]]; then
            RESULTS["$name"]="DOWN"
            LATENCIES["$name"]="0"
            DOWN_COUNT=$(( DOWN_COUNT + 1 ))
        else
            RESULTS["$name"]="DEGRADED"
            LATENCIES["$name"]="$latency"
            DEGRADED_COUNT=$(( DEGRADED_COUNT + 1 ))
        fi
    else
        probe_tcp "$name" "$REDIS_HOST" "$REDIS_PORT"
    fi
}

probe_rabbitmq() {
    local name="rabbitmq"
    local url="http://${RABBITMQ_HOST}:${RABBITMQ_PORT}/api/health/checks/alarms"

    if [[ -n "$RABBITMQ_PASS" ]]; then
        probe_http "$name" "$url" "200"
    else
        probe_tcp "$name" "$RABBITMQ_HOST" "${RABBITMQ_PORT}"
    fi
}

probe_minio() {
    probe_http "minio" "http://${MINIO_HOST}:${MINIO_PORT}/minio/health/live" "200"
}

probe_patroni() {
    local name="patroni-cluster"
    local url="http://${PATRONI_HOST}/cluster"

    probe_http "$name" "$url" "200"
}

probe_backend_health() {
    probe_http "backend" "${BACKEND_URL}/health/live" "200"
}

probe_backend_ready() {
    probe_http "backend-ready" "${BACKEND_URL}/health/ready" "200"
}

probe_backend_deep() {
    probe_http "backend-deep" "${BACKEND_URL}/health/deep" "200"
}

# ── Overall Status ──────────────────────────────────────────────────────────

compute_overall_status() {
    if [[ "$DOWN_COUNT" -gt 0 ]]; then
        OVERALL_STATUS="DOWN"
    elif [[ "$DEGRADED_COUNT" -gt 0 ]]; then
        OVERALL_STATUS="DEGRADED"
    else
        OVERALL_STATUS="UP"
    fi
}

# ── Output Formats ──────────────────────────────────────────────────────────

output_json() {
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    local components="{}"
    local first=true
    for key in "${!RESULTS[@]}"; do
        local entry
        entry=$(cat <<ENTRY
"${key}": {
    "status": "${RESULTS[$key]}",
    "latency_ms": ${LATENCIES[$key]}
}
ENTRY
)
        if $first; then
            components="{$entry"
            first=false
        else
            components="${components}, ${entry}"
        fi
    done
    components="${components}}"

    cat <<JSON
{
    "timestamp": "${timestamp}",
    "overall_status": "${OVERALL_STATUS}",
    "services_up": ${UP_COUNT},
    "services_degraded": ${DEGRADED_COUNT},
    "services_down": ${DOWN_COUNT},
    "services": ${components}
}
JSON
}

output_summary() {
    local emoji
    case "$OVERALL_STATUS" in
        UP)       emoji="✓" ;;
        DEGRADED) emoji="⚠" ;;
        DOWN)     emoji="✗" ;;
    esac
    echo "${emoji} ${OVERALL_STATUS}  up=${UP_COUNT} degraded=${DEGRADED_COUNT} down=${DOWN_COUNT}"
}

output_table() {
    printf "%-20s %-12s %-10s\n" "SERVICE" "STATUS" "LATENCY"
    printf "%-20s %-12s %-10s\n" "-------" "------" "-------"
    for key in "${!RESULTS[@]}"; do
        local status="${RESULTS[$key]}"
        local latency="${LATENCIES[$key]}"
        local color=""
        case "$status" in
            UP)       color="" ;;
            DEGRADED) color="" ;;
            DOWN)     color="" ;;
        esac
        if [[ "$latency" -gt 0 ]]; then
            printf "%-20s %-12s %dms\n" "$key" "$status" "$latency"
        else
            printf "%-20s %-12s N/A\n" "$key" "$status"
        fi
    done
}

# ── Main ────────────────────────────────────────────────────────────────────

main() {
    local output_mode="${1:-all}"

    # Run all probes in parallel
    probe_backend_health &
    probe_backend_ready &
    probe_backend_deep &
    probe_pg &
    probe_redis &
    probe_rabbitmq &
    probe_minio &
    probe_patroni &

    wait

    compute_overall_status

    case "$output_mode" in
        --json|-j)
            output_json
            ;;
        --summary|-s)
            output_summary
            ;;
        --table|-t|all)
            output_table
            echo ""
            output_summary
            echo ""
            output_json
            ;;
        *)
            echo "Usage: $0 [--json|--summary|--table]"
            echo ""
            output_table
            echo ""
            output_summary
            ;;
    esac

    case "$OVERALL_STATUS" in
        UP)       exit 0 ;;
        DEGRADED) exit 1 ;;
        DOWN)     exit 2 ;;
    esac
}

main "$@"

#!/bin/bash
# =============================================================================
# GULA Platform — Generate Prometheus metrics bearer token file
#
# Prometheus reads the raw token from a file (credentials_file in prometheus.yml)
# rather than an env var. This script writes METRICS_BEARER_TOKEN → file.
#
# Run once after setting METRICS_BEARER_TOKEN in .env:
#   source .env && bash scripts/generate-metrics-token.sh
#
# Or let deploy.sh call it automatically before `docker compose up`.
# =============================================================================

set -euo pipefail

TOKEN_FILE="config/prometheus/metrics_token"
TOKEN="${METRICS_BEARER_TOKEN:-}"

if [[ -z "$TOKEN" ]]; then
    echo "ERROR: METRICS_BEARER_TOKEN is not set."
    echo "       Set it in .env, then run: source .env && bash $0"
    exit 1
fi

# Write token with no trailing newline (Prometheus reads the raw file content)
printf '%s' "$TOKEN" > "$TOKEN_FILE"
chmod 600 "$TOKEN_FILE"

echo "✓ Token written to ${TOKEN_FILE} ($(wc -c < "$TOKEN_FILE") bytes)"
echo "  Prometheus will use this to scrape /metrics/prom with Bearer auth."

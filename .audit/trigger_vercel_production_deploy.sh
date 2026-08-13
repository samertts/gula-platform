#!/usr/bin/env bash
set -euo pipefail
readonly DEPLOY_HOOK_URL='https://api.vercel.com/v1/integrations/deploy/prj_xvgrHcfO6BWlwViUJ6HRQdawPsKX/Dgs02cMfZc'
response_file="$(mktemp)"
status="$(curl --silent --show-error --location --request POST --output "$response_file" --write-out '%{http_code}' "$DEPLOY_HOOK_URL")"
printf 'HTTP_STATUS=%s\n' "$status"
cat "$response_file"
rm -f "$response_file"

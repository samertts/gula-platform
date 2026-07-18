#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

usage() {
  cat <<EOF
Usage: $(basename "$0") -e ENVIRONMENT [options]

Plan Terraform deployment for an environment.

Options:
  -e ENVIRONMENT  Target environment (dev, staging, pilot, prod, dr)
  -o              Save plan to file
  -d              Destroy plan (plan for destruction)
  -h              Show this help message

Examples:
  $(basename "$0") -e dev
  $(basename "$0") -e prod -o
  $(basename "$0") -e staging -d
EOF
  exit 1
}

ENVIRONMENT=""
SAVE_PLAN=false
DESTROY=false

while getopts "e:odh" opt; do
  case "$opt" in
    e) ENVIRONMENT="$OPTARG" ;;
    o) SAVE_PLAN=true ;;
    d) DESTROY=true ;;
    h) usage ;;
    *) usage ;;
  esac
done

if [[ -z "$ENVIRONMENT" ]]; then
  echo -e "${RED}ERROR: Environment (-e) is required${NC}"
  usage
fi

ENV_DIR="$PROJECT_ROOT/environments/$ENVIRONMENT"

if [[ ! -d "$ENV_DIR" ]]; then
  echo -e "${RED}ERROR: Environment directory not found: $ENV_DIR${NC}"
  exit 1
fi

cd "$ENV_DIR"

echo -e "${GREEN}=== Planning deployment for: $ENVIRONMENT ===${NC}"

# Verify init has been run
if [[ ! -d ".terraform" ]]; then
  echo -e "${RED}ERROR: Terraform not initialized. Run init.sh first.${NC}"
  exit 1
fi

PLAN_OPTS=""
if $DESTROY; then
  PLAN_OPTS="-destroy"
  echo -e "${YELLOW}Planning DESTROY operation!${NC}"
fi

if $SAVE_PLAN; then
  PLAN_FILE="${ENVIRONMENT}-$(date +%Y%m%d-%H%M%S).tfplan"
  echo -e "${YELLOW}Plan will be saved to: $PLAN_FILE${NC}"
  terraform plan $PLAN_OPTS \
    -var-file=terraform.tfvars \
    -out="$PLAN_FILE" \
    -detailed-exitcode
  EXIT_CODE=$?
  if [[ $EXIT_CODE -eq 0 ]]; then
    echo -e "${GREEN}No changes detected.${NC}"
  elif [[ $EXIT_CODE -eq 2 ]]; then
    echo -e "${YELLOW}Changes detected. Plan saved to: $PLAN_FILE${NC}"
  else
    echo -e "${RED}Plan failed with exit code: $EXIT_CODE${NC}"
    exit $EXIT_CODE
  fi
else
  terraform plan $PLAN_OPTS \
    -var-file=terraform.tfvars
fi

echo -e "${GREEN}=== Plan complete for $ENVIRONMENT ===${NC}"

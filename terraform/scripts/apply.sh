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

Apply Terraform deployment for an environment.

Options:
  -e ENVIRONMENT  Target environment (dev, staging, pilot, prod, dr)
  -f PLAN_FILE    Apply a specific plan file instead of planning now
  -a              Auto-approve (skip confirmation prompt)
  -h              Show this help message

Examples:
  $(basename "$0") -e dev
  $(basename "$0") -e prod -f prod-20250101-120000.tfplan
  $(basename "$0") -e staging -a
EOF
  exit 1
}

ENVIRONMENT=""
PLAN_FILE=""
AUTO_APPROVE=false

while getopts "e:f:ah" opt; do
  case "$opt" in
    e) ENVIRONMENT="$OPTARG" ;;
    f) PLAN_FILE="$OPTARG" ;;
    a) AUTO_APPROVE=true ;;
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

# Verify init has been run
if [[ ! -d ".terraform" ]]; then
  echo -e "${RED}ERROR: Terraform not initialized. Run init.sh first.${NC}"
  exit 1
fi

echo -e "${GREEN}=== Applying deployment for: $ENVIRONMENT ===${NC}"

if [[ "$ENVIRONMENT" == "prod" || "$ENVIRONMENT" == "dr" ]]; then
  echo -e "${YELLOW}============================================${NC}"
  echo -e "${YELLOW}  PRODUCTION DEPLOYMENT                    ${NC}"
  echo -e "${YELLOW}  Environment: $ENVIRONMENT${NC}"
  echo -e "${YELLOW}============================================${NC}"
  echo ""

  if [[ "$AUTO_APPROVE" == false ]]; then
    echo -e "${RED}WARNING: You are about to apply changes to $ENVIRONMENT!${NC}"
    echo -e "${RED}This is a production environment.${NC}"
    echo ""
    read -rp "Are you sure you want to continue? (type 'yes' to confirm): " CONFIRM
    if [[ "$CONFIRM" != "yes" ]]; then
      echo -e "${RED}Cancelled.${NC}"
      exit 1
    fi
    echo ""
  fi
fi

APPROVE_OPTS=""
if $AUTO_APPROVE; then
  APPROVE_OPTS="-auto-approve"
fi

if [[ -n "$PLAN_FILE" ]]; then
  if [[ ! -f "$PLAN_FILE" ]]; then
    echo -e "${RED}ERROR: Plan file not found: $PLAN_FILE${NC}"
    exit 1
  fi
  echo -e "${YELLOW}Applying plan file: $PLAN_FILE${NC}"
  terraform apply $APPROVE_OPTS "$PLAN_FILE"
else
  echo -e "${YELLOW}Planning and applying...${NC}"
  terraform apply $APPROVE_OPTS \
    -var-file=terraform.tfvars
fi

echo -e "${GREEN}=== Apply complete for $ENVIRONMENT ===${NC}"

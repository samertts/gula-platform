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

DESTROY Terraform-managed infrastructure for an environment.

WARNING: This will destroy ALL resources managed by Terraform in the
specified environment. This is irreversible for most resources.

Options:
  -e ENVIRONMENT  Target environment (dev, staging, pilot, prod, dr)
  -a              Auto-approve (skip all confirmation prompts)
  -f PLAN_FILE    Destroy using a destroy plan file
  -h              Show this help message

Examples:
  $(basename "$0") -e dev
  $(basename "$0") -e staging -a
EOF
  exit 1
}

ENVIRONMENT=""
AUTO_APPROVE=false
PLAN_FILE=""

while getopts "e:af:h" opt; do
  case "$opt" in
    e) ENVIRONMENT="$OPTARG" ;;
    a) AUTO_APPROVE=true ;;
    f) PLAN_FILE="$OPTARG" ;;
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

if [[ ! -d ".terraform" ]]; then
  echo -e "${RED}ERROR: Terraform not initialized. Run init.sh first.${NC}"
  exit 1
fi

echo -e "${RED}============================================${NC}"
echo -e "${RED}  DESTROY OPERATION                         ${NC}"
echo -e "${RED}  Environment: $ENVIRONMENT${NC}"
echo -e "${RED}  ALL RESOURCES WILL BE DESTROYED           ${NC}"
echo -e "${RED}============================================${NC}"
echo ""

if [[ "$AUTO_APPROVE" == false ]]; then
  echo -e "${YELLOW}Are you ABSOLUTELY SURE you want to destroy all resources in '$ENVIRONMENT'?${NC}"
  read -rp "Type the environment name to confirm: " CONFIRM_ENV
  if [[ "$CONFIRM_ENV" != "$ENVIRONMENT" ]]; then
    echo -e "${RED}Cancelled. Environment name does not match.${NC}"
    exit 1
  fi

  read -rp "Type 'yes' to confirm destruction: " CONFIRM
  if [[ "$CONFIRM" != "yes" ]]; then
    echo -e "${RED}Cancelled.${NC}"
    exit 1
  fi
  echo ""
fi

if [[ -n "$PLAN_FILE" ]]; then
  if [[ ! -f "$PLAN_FILE" ]]; then
    echo -e "${RED}ERROR: Plan file not found: $PLAN_FILE${NC}"
    exit 1
  fi
  echo -e "${YELLOW}Applying destroy plan file: $PLAN_FILE${NC}"
  terraform apply "$PLAN_FILE"
else
  APPROVE_OPTS=""
  if $AUTO_APPROVE; then
    APPROVE_OPTS="-auto-approve"
  fi
  terraform destroy $APPROVE_OPTS \
    -var-file=terraform.tfvars
fi

echo -e "${GREEN}=== Destroy complete for $ENVIRONMENT ===${NC}"

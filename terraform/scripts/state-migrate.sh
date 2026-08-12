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

Migrate Terraform state to a new backend for an environment.
Useful when changing state storage locations or migrating from local to remote state.

Options:
  -e ENVIRONMENT  Target environment (dev, staging, pilot, prod, dr)
  -b BUCKET       Target S3 bucket name
  -k KEY          State file key (path)
  -t TABLE        DynamoDB lock table name
  -r REGION       AWS region for state bucket
  -l              Local to remote migration (use local state as source)
  -h              Show this help message

Examples:
  $(basename "$0") -e dev -b gula-terraform-state-dev -k dev/terraform.tfstate -t gula-terraform-locks-dev
  $(basename "$0") -e prod -l
EOF
  exit 1
}

ENVIRONMENT=""
TARGET_BUCKET=""
TARGET_KEY=""
TARGET_TABLE=""
TARGET_REGION=""
LOCAL_TO_REMOTE=false

while getopts "e:b:k:t:r:lh" opt; do
  case "$opt" in
    e) ENVIRONMENT="$OPTARG" ;;
    b) TARGET_BUCKET="$OPTARG" ;;
    k) TARGET_KEY="$OPTARG" ;;
    t) TARGET_TABLE="$OPTARG" ;;
    r) TARGET_REGION="$OPTARG" ;;
    l) LOCAL_TO_REMOTE=true ;;
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

echo -e "${GREEN}=== State Migration for: $ENVIRONMENT ===${NC}"

if $LOCAL_TO_REMOTE; then
  if [[ ! -f "terraform.tfstate" ]]; then
    echo -e "${RED}ERROR: Local state file not found: terraform.tfstate${NC}"
    echo -e "${YELLOW}Run a plan/apply first to generate local state, or specify target backend manually.${NC}"
    exit 1
  fi

  echo -e "${YELLOW}Migrating from LOCAL state to S3 backend...${NC}"
  echo ""

  # Generate a temporary backend config for the migration
  BACKEND_CONFIG="backend-migrate-${ENVIRONMENT}.hcl"
  cat > "$BACKEND_CONFIG" <<BACKENDEOF
bucket         = "gula-terraform-state-${ENVIRONMENT}"
key            = "${ENVIRONMENT}/terraform.tfstate"
region         = "${TARGET_REGION:-eu-west-1}"
encrypt        = true
dynamodb_table = "gula-terraform-locks-${ENVIRONMENT}"
BACKENDEOF

  echo -e "${YELLOW}Backend config:${NC}"
  cat "$BACKEND_CONFIG"
  echo ""

  read -rp "Proceed with migration? (yes/no): " CONFIRM
  if [[ "$CONFIRM" != "yes" ]]; then
    echo -e "${RED}Cancelled.${NC}"
    rm -f "$BACKEND_CONFIG"
    exit 1
  fi

  terraform init \
    -migrate-state \
    -backend-config="$BACKEND_CONFIG" \
    -reconfigure

  rm -f "$BACKEND_CONFIG"
  echo -e "${GREEN}State migrated from local to S3 successfully.${NC}"

else
  if [[ -z "$TARGET_BUCKET" || -z "$TARGET_KEY" || -z "$TARGET_TABLE" ]]; then
    echo -e "${RED}ERROR: When not using -l, you must provide -b, -k, and -t${NC}"
    usage
  fi

  BACKEND_CONFIG="backend-migrate-${ENVIRONMENT}.hcl"
  cat > "$BACKEND_CONFIG" <<BACKENDEOF
bucket         = "${TARGET_BUCKET}"
key            = "${TARGET_KEY}"
region         = "${TARGET_REGION:-eu-west-1}"
encrypt        = true
dynamodb_table = "${TARGET_TABLE}"
BACKENDEOF

  echo -e "${YELLOW}Migrating to new backend...${NC}"
  echo -e "${YELLOW}Target bucket: ${TARGET_BUCKET}${NC}"
  echo -e "${YELLOW}Target key: ${TARGET_KEY}${NC}"
  echo -e "${YELLOW}Target table: ${TARGET_TABLE}${NC}"
  echo ""

  read -rp "Proceed with migration? (yes/no): " CONFIRM
  if [[ "$CONFIRM" != "yes" ]]; then
    echo -e "${RED}Cancelled.${NC}"
    rm -f "$BACKEND_CONFIG"
    exit 1
  fi

  terraform init \
    -migrate-state \
    -backend-config="$BACKEND_CONFIG" \
    -reconfigure

  rm -f "$BACKEND_CONFIG"
  echo -e "${GREEN}State migrated successfully.${NC}"
fi

echo -e "${GREEN}=== Migration complete for $ENVIRONMENT ===${NC}"

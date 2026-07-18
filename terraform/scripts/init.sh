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
Usage: $(basename "$0") -e ENVIRONMENT [-r REGION]

Initialize a Terraform workspace for the specified environment.

Options:
  -e ENVIRONMENT  Target environment (dev, staging, pilot, prod, dr)
  -r REGION       AWS region (default: from environment config)
  -h              Show this help message

Examples:
  $(basename "$0") -e dev
  $(basename "$0") -e prod -r eu-west-1
EOF
  exit 1
}

ENVIRONMENT=""
REGION=""

while getopts "e:r:h" opt; do
  case "$opt" in
    e) ENVIRONMENT="$OPTARG" ;;
    r) REGION="$OPTARG" ;;
    h) usage ;;
    *) usage ;;
  esac
done

if [[ -z "$ENVIRONMENT" ]]; then
  echo -e "${RED}ERROR: Environment (-e) is required${NC}"
  usage
fi

VALID_ENVS=("dev" "staging" "pilot" "prod" "dr")
VALID=0
for ve in "${VALID_ENVS[@]}"; do
  if [[ "$ve" == "$ENVIRONMENT" ]]; then
    VALID=1
    break
  fi
done

if [[ "$VALID" -ne 1 ]]; then
  echo -e "${RED}ERROR: Invalid environment '$ENVIRONMENT'. Must be one of: ${VALID_ENVS[*]}${NC}"
  exit 1
fi

ENV_DIR="$PROJECT_ROOT/environments/$ENVIRONMENT"

if [[ ! -d "$ENV_DIR" ]]; then
  echo -e "${RED}ERROR: Environment directory not found: $ENV_DIR${NC}"
  exit 1
fi

echo -e "${GREEN}=== Initializing Terraform for environment: $ENVIRONMENT ===${NC}"

cd "$ENV_DIR"

# Detect region from terraform.tfvars if not provided
if [[ -z "$REGION" ]]; then
  REGION=$(grep -E '^\s*aws_region\s*=' terraform.tfvars 2>/dev/null | head -1 | cut -d'=' -f2 | tr -d ' "' || echo "")
  if [[ -z "$REGION" ]]; then
    REGION="eu-west-1"
  fi
fi

echo -e "${YELLOW}Region: $REGION${NC}"
echo -e "${YELLOW}Workspace: $ENVIRONMENT${NC}"

# Create backend config
BACKEND_CONFIG="backend-${ENVIRONMENT}.hcl"
cat > "$BACKEND_CONFIG" <<BACKENDEOF
bucket         = "gula-terraform-state-${ENVIRONMENT}"
key            = "${ENVIRONMENT}/terraform.tfstate"
region         = "${REGION}"
encrypt        = true
dynamodb_table = "gula-terraform-locks-${ENVIRONMENT}"
BACKENDEOF

echo -e "${YELLOW}Backend config written to: $BACKEND_CONFIG${NC}"

# Initialize Terraform
echo -e "${GREEN}Running terraform init...${NC}"
terraform init \
  -backend-config="$BACKEND_CONFIG" \
  -upgrade \
  -reconfigure

# Select or create workspace
echo -e "${GREEN}Selecting workspace: $ENVIRONMENT${NC}"
terraform workspace select "$ENVIRONMENT" 2>/dev/null || terraform workspace new "$ENVIRONMENT"

echo -e "${GREEN}=== Initialization complete for $ENVIRONMENT ===${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  cd $ENV_DIR"
echo "  terraform plan -var-file=terraform.tfvars"
echo "  terraform apply -var-file=terraform.tfvars"

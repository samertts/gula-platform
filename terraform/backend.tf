terraform {
  backend "s3" {
    # Backend configuration is provided via -backend-config or backend.hcl
    # during terraform init. These are defaults for local dev.
    #
    # Usage:
    #   terraform init -backend-config="bucket=gula-terraform-state-<env>" \
    #                  -backend-config="dynamodb_table=gula-terraform-locks-<env>"
    #
    # Or via env file:
    #   terraform init -backend-config=config/backend-<env>.hcl
    #
    # See scripts/init.sh for automated workspace initialization.
    bucket         = "gula-terraform-state"
    key            = "terraform.tfstate"
    region         = "eu-west-1"
    encrypt        = true
    dynamodb_table = "gula-terraform-locks"
  }
}

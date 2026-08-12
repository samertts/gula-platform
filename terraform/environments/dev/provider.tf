provider "aws" {
  region = var.aws_region

  assume_role {
    role_arn     = var.aws_assume_role_arn
    session_name = "gula-terraform-dev"
  }

  default_tags {
    tags = merge(var.tags, {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    })
  }
}

provider "random" {}
provider "tls" {}
provider "null" {}
provider "time" {}

terraform {
  required_version = ">= 1.6.0, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.40, < 6.0.0"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.5, < 4.0.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = ">= 4.0, < 5.0.0"
    }
    null = {
      source  = "hashicorp/null"
      version = ">= 3.2, < 4.0.0"
    }
    time = {
      source  = "hashicorp/time"
      version = ">= 0.10, < 1.0.0"
    }
  }
}

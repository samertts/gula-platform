provider "aws" {
  region = var.aws_region

  assume_role {
    role_arn     = var.aws_assume_role_arn
    session_name = "gula-terraform-pilot"
  }

  default_tags {
    tags = merge(var.tags, {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    })
  }
}

provider "aws" {
  alias  = "dr"
  region = var.aws_dr_region

  assume_role {
    role_arn     = var.aws_assume_role_arn
    session_name = "gula-terraform-dr-pilot"
  }

  default_tags {
    tags = merge(var.tags, {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    })
  }
}

provider "kubernetes" {
  host                   = module.kubernetes.cluster_endpoint
  cluster_ca_certificate = base64decode(module.kubernetes.cluster_ca_cert)
  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args        = ["eks", "get-token", "--cluster-name", module.kubernetes.cluster_name]
  }
}

provider "helm" {
  kubernetes {
    host                   = module.kubernetes.cluster_endpoint
    cluster_ca_certificate = base64decode(module.kubernetes.cluster_ca_cert)
    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args        = ["eks", "get-token", "--cluster-name", module.kubernetes.cluster_name]
    }
  }
}

provider "kubectl" {
  host                   = module.kubernetes.cluster_endpoint
  cluster_ca_certificate = base64decode(module.kubernetes.cluster_ca_cert)
  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args        = ["eks", "get-token", "--cluster-name", module.kubernetes.cluster_name]
  }
}

provider "random" {}
provider "tls" {}
provider "null" {}
provider "time" {}

terraform {
  required_version = ">= 1.6.0, < 2.0.0"

  backend "s3" {
    bucket         = "gula-terraform-state-pilot"
    key            = "pilot/terraform.tfstate"
    region         = "eu-west-1"
    encrypt        = true
    dynamodb_table = "gula-terraform-locks-pilot"
  }

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
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 2.25, < 3.0.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = ">= 2.12, < 3.0.0"
    }
    kubectl = {
      source  = "gavinbunney/kubectl"
      version = ">= 1.14, < 2.0.0"
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

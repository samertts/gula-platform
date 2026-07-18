provider "aws" {
  region = var.aws_region

  assume_role {
    role_arn     = var.aws_assume_role_arn
    session_name = "gula-terraform-${var.environment}"
  }

  default_tags {
    tags = local.global_tags
  }
}

provider "aws" {
  alias  = "dr"
  region = var.aws_dr_region

  assume_role {
    role_arn     = var.aws_assume_role_arn
    session_name = "gula-terraform-dr-${var.environment}"
  }

  default_tags {
    tags = local.global_tags
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

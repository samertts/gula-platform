terraform {
  required_version = ">= 1.6.0, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.95, < 6.0.0"
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
      version = ">= 2.36, < 3.0.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = ">= 2.17, < 3.0.0"
    }
    kubectl = {
      source  = "gavinbunney/kubectl"
      version = ">= 1.19, < 2.0.0"
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

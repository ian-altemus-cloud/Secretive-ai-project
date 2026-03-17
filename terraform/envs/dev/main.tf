terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.81.0"
    }
  }
}
provider "aws" {
  region = var.aws_region
}

module "vpc" {
  source = "../../modules/vpc"

  vpc_cidr             = "10.0.0.0/16"
  environment          = var.environment
  project_name         = var.project_name
  public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnet_cidrs = ["10.0.3.0/24", "10.0.4.0/24"]
  availability_zones   = ["us-east-1a", "us-east-1b"]
}

module "security_groups" {
  source = "../../modules/security_groups"

  vpc_id       = module.vpc.vpc_id
  vpc_cidr     = "10.0.0.0/16"
  environment  = var.environment
  project_name = var.project_name
}
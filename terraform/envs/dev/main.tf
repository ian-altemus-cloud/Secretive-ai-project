terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.81.0"
    }
  }
  backend "s3" {
    bucket         = "secretive-ai-terraform-state"
    key            = "secretive-nail-bar/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "secretive-ai-terraform-locks"
    encrypt        = true
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

module "sqs" {
  source       = "../../modules/sqs"
  project_name = var.project_name
  environment  = var.environment
}

module "DynamoDB" {
  source       = "../../modules/dynamodb"
  project_name = var.project_name
  environment  = var.environment
}

module "ecr" {
  source       = "../../modules/ecr"
  project_name = var.project_name
  environment  = var.environment
}

module "secrets" {
  source       = "../../modules/secrets"
  project_name = var.project_name
  environment  = var.environment
}

module "fargate" {
  source             = "../../modules/fargate"
  project_name       = var.project_name
  environment        = var.environment
  container_image    = module.ecr.ecr_repository_url
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  fargate_sg_id      = module.security_groups.fargate_sg_id
}

module "api_gateway" {
  source         = "../../modules/api_gateway"
  project_name   = var.project_name
  environment    = var.environment
  sqs_queue_arn  = module.sqs.sqs_arn
  sqs_queue_url  = module.sqs.sqs_url
  aws_account_id = "894943009636"
}
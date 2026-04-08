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
  source                   = "../../modules/fargate"
  project_name             = var.project_name
  environment              = var.environment
  container_image          = module.ecr.ecr_repository_url
  vpc_id                   = module.vpc.vpc_id
  private_subnet_ids       = module.vpc.private_subnet_ids
  fargate_sg_id            = module.security_groups.fargate_sg_id
  sqs_queue_arn            = module.sqs.sqs_arn
  dynamodb_table_arn       = module.DynamoDB.dynamodb_table_arn
  followup_lambda_arn      = module.followup_lambda.lambda_arn
  scheduler_role_arn       = module.followup_lambda.scheduler_role_arn
  target_group_arn         = module.alb.target_group_arn
  nlb_target_group_arn     = module.nlb.nlb_target_group_arn
  bedrock_model_arn        = "arn:aws:bedrock:us-east-1:894943009636:inference-profile/us.anthropic.claude-haiku-4-5-20251001-v1:0"
  google_sheets_secret_arn = "arn:aws:secretsmanager:us-east-1:894943009636:secret:secretive-nail-bar/dev/google-sheets-credentials-IM5gxg"

  depends_on = [module.alb]
}

module "api_gateway" {
  source         = "../../modules/api_gateway"
  project_name   = var.project_name
  environment    = var.environment
  sqs_queue_arn  = module.sqs.sqs_arn
  sqs_queue_url  = module.sqs.sqs_url
  aws_account_id = "894943009636"
  nlb_arn        = module.nlb.nlb_arn
  nlb_dns_name   = module.nlb.nlb_dns_name
}
module "observability" {
  source                       = "../../modules/observability"
  project_name                 = var.project_name
  environment                  = var.environment
  vpc_id                       = module.vpc.vpc_id
  private_subnet_ids           = module.vpc.private_subnet_ids
  public_subnet_ids            = module.vpc.public_subnet_ids
  ecs_cluster_id               = module.fargate.cluster_id
  grafana_sg_id                = module.security_groups.grafana_sg_id
  prometheus_sg_id             = module.security_groups.prometheus_sg_id
  flask_service_discovery_name = "flask.secretive-nail-bar-dev.local"
}

module "followup_lambda" {
  source                   = "../../modules/lambda"
  environment              = var.environment
  project_name             = var.project_name
  vpc_id                   = module.vpc.vpc_id
  private_subnet_ids       = module.vpc.private_subnet_ids
  dynamodb_table_arn       = module.DynamoDB.dynamodb_table_arn
  google_sheets_secret_arn = "arn:aws:secretsmanager:us-east-1:894943009636:secret:secretive-nail-bar/dev/google-sheets-credentials-IM5gxg"
  lambda_sg_id             = module.security_groups.lambda_sg_id
  meta_api_token_arn       = "arn:aws:secretsmanager:us-east-1:894943009636:secret:secretive-nail-bar-dev/meta-api-token-xs95gz"
  dynamodb_table_name      = module.DynamoDB.dynamodb_table_name
  anthropic_api_secret_arn = "arn:aws:secretsmanager:us-east-1:894943009636:secret:secretive-api-key-JLF2jL"
  bedrock_model_arn        = "arn:aws:bedrock:us-east-1:894943009636:inference-profile/us.anthropic.claude-haiku-4-5-20251001-v1:0"
}
module "alb" {
  source            = "../../modules/alb"
  project_name      = var.project_name
  environment       = var.environment
  vpc_id            = module.vpc.vpc_id
  public_subnet_ids = ["subnet-0b6c70f2de03463f6", "subnet-0e82c56aaa6daa7cc"]
  alb_sg_id         = module.security_groups.alb_sg_id
}

module "nlb" {
  source             = "../../modules/nlb"
  project_name       = var.project_name
  environment        = var.environment
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
}

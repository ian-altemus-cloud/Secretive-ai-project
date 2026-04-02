variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}
variable "memory" {
  description = "Memory in MB for Lambda task"
  type        = number
  default     = 512
}
variable "vpc_id" {
  description = "VPC ID for the lambda service"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for lambda tasks"
  type        = list(string)
}
variable "dynamodb_table_arn" {
  description = "DynamoDB Table ARN"
  type        = string
}
variable "bedrock_model_arn" {
  description = "Bedrock model arn -- reserved for when acct ready"
  type        = string
}
variable "google_sheets_secret_arn" {
  description = "google sheets arn"
  type        = string
}
variable "lambda_sg_id" {
  description = "SG for the follow up lambda"
  type        = string
}
variable "meta_api_token_arn" {
  description = "meta token arn"
  type        = string
}
variable "dynamodb_table_name" {
  description = "DynamoDB Table for conversation"
  type        = string
}
variable "anthropic_api_secret_arn" {
  description = " Anthropic arn"
  type        = string
}
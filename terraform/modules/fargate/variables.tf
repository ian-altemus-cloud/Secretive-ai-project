variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "container_image" {
  description = "ECR image URI for the Flask container"
  type        = string
}

variable "container_port" {
  description = "Port the container listens on"
  type        = number
  default     = 80
}

variable "cpu" {
  description = "CPU units for Fargate task"
  type        = number
  default     = 256
}

variable "memory" {
  description = "Memory in MB for Fargate task"
  type        = number
  default     = 512
}

variable "vpc_id" {
  description = "VPC ID for the Fargate service"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for Fargate tasks"
  type        = list(string)
}

variable "fargate_sg_id" {
  description = "Security group ID for Fargate tasks"
  type        = string
}

variable "desired_count" {
  description = "Number of Fargate tasks to run"
  type        = number
  default     = 1
}

variable "sqs_queue_arn" {
  description = "SQS Queue ARN"
  type        = string
}

variable "dynamodb_table_arn" {
  description = "DynamoDB Table ARN"
  type        = string
}

variable "bedrock_model_arn" {
  description = "Bedrock model arn"
  type        = string
}
variable "google_sheets_secret_arn" {
  description = "google sheets arn"
  type        = string
}
variable "followup_lambda_arn" {
  description = "ARN of the follow-up Lambda function"
  type        = string
}
variable "scheduler_role_arn" {
  description = "ARN of the EventBridge Scheduler IAM role"
  type        = string
}
variable "target_group_arn" {
  description = "ALB target group ARN for the Flask service"
  type        = string
}
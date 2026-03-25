variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Development environment for resource"
  type        = string
}

variable "sqs_queue_arn" {
  description = "ARN of the SQS queue to fwd webhook messages to"
  type        = string
}
variable "sqs_queue_url" {
  description = "URL of the SQS queue"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

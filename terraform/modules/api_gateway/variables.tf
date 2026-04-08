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

variable "aws_account_id" {
  description = "AWS account ID"
  type        = string
}
variable "nlb_arn" {
  description = "ARN of the NLB for VPC Link"
  type        = string
}

variable "nlb_dns_name" {
  description = "DNS name of the NLB for GET proxy integration"
  type        = string
}
variable "aws_region" {
  description = "AWS region to deploy resources"
  type = string
}

variable "environment" {
  description = "Deployment environment"
  type  = string
}

variable "project_name" {
  description = "Project identifier used for resource naming"
  type        = string
}

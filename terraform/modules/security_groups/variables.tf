variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block of the VPC"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}
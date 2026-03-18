variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Deployment Env"
  type        = string
}

variable "hash_key" {
  description = "Partition Key for the conversation table"
  type        = string
  default     = "instagram_user_id"
}

variable "billing_mode" {
  description = "DynamoDB billing mode"
  type        = string
  default     = "PAY_PER_REQUEST"
}

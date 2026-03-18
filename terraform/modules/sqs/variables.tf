variable "project_name" {
  description = "Project name for the resource naming"
  type        = string
}

variable "environment" {
  description = "Environment for the resource naming"
  type        = string
}

variable "visibility_timeout_seconds" {
  description = "Visibility timeout for messages in seconds"
  type        = number
  default     = 30
}

variable "message_retention_seconds" {
  description = "How long SQS retains a message in seconds"
  type        = number
  default     = 86400
}

variable "max_receive_count" {
  description = "Max retries before message moves to DLQ"
  type        = number
  default     = 3
}
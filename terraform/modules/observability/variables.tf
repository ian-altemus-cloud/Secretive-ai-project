variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}
variable "vpc_id" {
  description = "VPC ID for the Fargate service"
  type        = string
}
variable "private_subnet_ids" {
  description = "Private subnet IDs for Fargate tasks"
  type        = list(string)
}
variable "public_subnet_ids" {
  description = "Public subnet IDs for Fargate tasks"
  type        = list(string)
}
variable "ecs_cluster_id" {
  description = "ID for ECS cluster"
  type        = string
}
variable "flask_service_discovery_name" {
  description = "Name of the flask DNS resolver"
  type        = string
}
variable "grafana_sg_id" {
  description = "Security group ID for Grafana"
  type        = string
}

variable "prometheus_sg_id" {
  description = "Security group ID for Prometheus"
  type        = string
}
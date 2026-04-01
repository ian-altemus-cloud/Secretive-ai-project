output "prometheus_ecr_url" {
  description = "ECR repository URL for Prometheus image"
  value       = aws_ecr_repository.prometheus.repository_url
}

output "observability_service_name" {
  description = "Name of the observability ECS service"
  value       = aws_ecs_service.observability.name
}

output "service_discovery_namespace" {
  description = "Private DNS namespace for service discovery"
  value       = aws_service_discovery_private_dns_namespace.main.name
}
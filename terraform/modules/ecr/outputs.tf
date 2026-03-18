output "ecr_repository_url" {
  description = "URL of the ECR repo"
  value       = aws_ecr_repository.ecr_repository.repository_url
}

output "ecr_repository_arn" {
  description = "ARN of the ECR repo"
  value       = aws_ecr_repository.ecr_repository.arn
}
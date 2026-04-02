output "alb_sg_id" {
  description = "ID of the ALB security group"
  value       = aws_security_group.alb.id
}

output "fargate_sg_id" {
  description = "ID of the Fargate security group"
  value       = aws_security_group.fargate.id
}
output "prometheus_sg_id" {
  description = "ID of the Prometheus security group"
  value       = aws_security_group.prometheus.id
}
output "grafana_sg_id" {
  description = "ID of the Grafana security group"
  value       = aws_security_group.grafana.id
}
output "lambda_sg_id" {
  description = "ID of the Lambda security group"
  value       = aws_security_group.lambda.id
}
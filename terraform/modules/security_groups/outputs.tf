output "alb_sg_id" {
  description = "ID of the ALB security group"
  value       = aws_security_group.alb.id
}

output "fargate_sg_id" {
  description = "ID of the Fargate security group"
  value       = aws_security_group.fargate.id
}
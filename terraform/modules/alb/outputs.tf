output "target_group_arn" {
  value = aws_lb_target_group.flask.arn
}

output "alb_dns_name" {
  value = aws_lb.main.dns_name
}

output "acm_certificate_arn" {
  value = aws_acm_certificate.main.arn
}

output "acm_certificate_validation_options" {
  value = aws_acm_certificate.main.domain_validation_options
}

output "lambda_arn" {
  description = "ARN of the follow-up Lambda function"
  value       = aws_lambda_function.followup.arn
}

output "scheduler_role_arn" {
  description = "ARN of the EventBridge Scheduler IAM role"
  value       = aws_iam_role.scheduler_role.arn
}